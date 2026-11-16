"""Caches sintéticos pequenos: identidade completa, integridade e retomada."""

import hashlib
import json
import sqlite3

import polars as pl
import pytest

from tcc_music_popularity import sample_cache_reuse as mod


def metadata(title="Faixa", duration="180000", track="sintetico_1", artist="Artista"):
    return {"track_id": track, "artist_name": artist, "track_name": title, "duration_ms": duration}


def cache(path, entries):
    db = sqlite3.connect(path)
    db.executescript(mod.base.STATE_SQL)
    for query, status, text in entries:
        result = {
            "status": status,
            "reason": "decisao_sintetica",
            "rules_version": mod.recovery.VERSION,
        }
        key = mod.fingerprint(query)
        lyric = None
        if status == "accepted":
            value = hashlib.sha256(text.encode()).hexdigest()
            strict = mod.strict_plain_text_metrics(text)["strict_text_sha256"]
            result.update(
                text_sha256=value,
                strict_text_sha256=strict,
                selected_lrclib_id=10,
                selected_lyrics_id=20,
            )
            lyric = {
                "plain_text_source": text,
                "source_plain_original": text,
                "synced_text_source": None,
                "lrclib_id": 10,
                "lrclib_lyrics_id": 20,
                "text_sha256": value,
                "strict_text_sha256": strict,
            }
        db.execute(
            "INSERT INTO queries(query_id,data,status,result) VALUES (?,?,?,?)",
            (key, json.dumps(query), status, json.dumps(result)),
        )
        if lyric:
            db.execute("INSERT INTO lyrics VALUES (?,?)", (key, json.dumps(lyric)))
    db.commit()
    return db


def test_reutilizacao_exata_nao_depende_de_id_spotify_mas_exige_duracao_e_versao(tmp_path):
    query = mod.recovery.recovery_query(metadata())
    path = tmp_path / "cache.sqlite"
    db = cache(path, [(query, "accepted", "Texto sintético de teste\nSegunda linha")])
    databases = [(db, path, mod.recovery.VERSION)]
    identical = mod.recovery.recovery_query(metadata(track="outro_id"))
    result, lyric = mod.reuse_query(databases, identical)
    assert result["status"] == "accepted"
    assert lyric["plain_text_source"].startswith("Texto sintético")
    for changed in [metadata(duration="190000"), metadata(title="Faixa - Live")]:
        result, lyric = mod.reuse_query(databases, mod.recovery.recovery_query(changed))
        assert result["status"] == "pending_search" and lyric is None
    with pytest.raises(ValueError, match="proibido"):
        mod.reuse_query(databases, {**query, "popularity": 50})
    db.close()


def test_texto_corrompido_nao_e_aceito(tmp_path):
    query = mod.recovery.recovery_query(metadata())
    path = tmp_path / "cache.sqlite"
    db = cache(path, [(query, "accepted", "Texto íntegro")])
    key = mod.fingerprint(query)
    lyric = json.loads(db.execute("SELECT data FROM lyrics WHERE query_id=?", (key,)).fetchone()[0])
    lyric["plain_text_source"] = "Texto adulterado"
    db.execute("UPDATE lyrics SET data=? WHERE query_id=?", (json.dumps(lyric), key))
    with pytest.raises(ValueError, match="SHA"):
        mod.reuse_query([(db, path, mod.recovery.VERSION)], query)
    db.close()


def test_exportacao_preserva_texto_efetivo_derivado_e_plain_original_ausente(tmp_path):
    row = metadata()
    query = mod.recovery.recovery_query(row)
    key = mod.fingerprint(query)
    path = tmp_path / "cache.sqlite"
    db = cache(path, [(query, "accepted", "Verso extraído do LRC")])
    lyric = json.loads(db.execute("SELECT data FROM lyrics WHERE query_id=?", (key,)).fetchone()[0])
    lyric.update(source_plain_original=None, synced_text_source="[00:01.00]Verso extraído do LRC")
    db.execute("UPDATE lyrics SET data=? WHERE query_id=?", (json.dumps(lyric), key))
    db.commit()
    result, lyric = mod.reuse_query([(db, path, mod.recovery.VERSION)], query)
    own = sqlite3.connect(tmp_path / "output.sqlite")
    mod.init_state(own, {"fixture": True}, {key: query})
    own.execute(
        "INSERT INTO decisions VALUES (?,?,?,?)",
        (key, json.dumps(query), json.dumps(result), json.dumps(lyric)),
    )
    own.commit()
    sample = pl.DataFrame([row])
    mod.export_private(own, sample, [(row["track_id"], key)], tmp_path)
    accepted = pl.read_parquet(tmp_path / "letras_aceitas.parquet")
    assert accepted["accepted_text"][0] == "Verso extraído do LRC"
    assert accepted["plain_text_source"][0] is None
    assert accepted["synced_text_source"][0] == "[00:01.00]Verso extraído do LRC"
    own.close()
    db.close()


def test_decisao_v2_nao_e_contornada_por_aceitacao_v1(tmp_path):
    query = mod.recovery.recovery_query(metadata())
    p2, p1 = tmp_path / "v2.sqlite", tmp_path / "v1.sqlite"
    d2 = cache(p2, [(query, "ambiguous", None)])
    d1 = cache(p1, [(query, "accepted", "Letra antiga")])
    result, lyric = mod.reuse_query(
        [(d2, p2, mod.recovery.VERSION), (d1, p1, mod.base.VERSION)], query
    )
    assert result["status"] == "pending_search" and result["previous_status"] == "ambiguous"
    assert lyric is None
    d2.close()
    d1.close()


def test_acesso_sem_indice_ou_wal_ativo_e_interrompido(tmp_path):
    path = tmp_path / "sem_indice.sqlite"
    db = sqlite3.connect(path)
    db.executescript(
        "CREATE TABLE queries(query_id TEXT,data TEXT); CREATE TABLE lyrics(query_id TEXT,data TEXT);"
    )
    db.close()
    with pytest.raises(ValueError, match="chave"):
        mod.readonly(path)
    wal = tmp_path / "sem_indice.sqlite-wal"
    wal.write_bytes(b"transacao_sintetica")
    with pytest.raises(ValueError, match="WAL"):
        mod.stamp(path)


def test_integracao_sintetica_preserva_amostra_status_textos_e_retomada(tmp_path):
    rows = [
        metadata(track="a"),
        metadata(track="b"),
        metadata("Instrumental", track="c"),
        metadata("Sem cache", track="d"),
        metadata("Ambigua", track="e"),
        metadata("Sem artista", track="f", artist=None),
    ]
    sample = pl.DataFrame(rows).with_columns(
        pl.lit("rock").alias("genre"),
        pl.lit("2015").alias("year"),
        pl.lit("30").alias("popularity"),
        pl.lit(10.0).alias("_nova_peso"),
    )
    source = tmp_path / "sample.parquet"
    sample.write_parquet(source)
    summary = tmp_path / "summary.json"
    mod.atomic_json(
        summary, {"concluido": True, "n": 6, "parquet_sha256": mod.design.sha256(source)}
    )
    queries = [mod.recovery.recovery_query(r) for r in rows]
    p2, p1 = tmp_path / "v2.sqlite", tmp_path / "v1.sqlite"
    db = cache(
        p2,
        [
            (queries[0], "accepted", "Letra sintética\nOutra linha"),
            (queries[2], "instrumental", None),
            (queries[4], "ambiguous", None),
        ],
    )
    db.close()
    cache(p1, []).close()
    stamps = [mod.stamp(p) for p in [p2, p1]]
    workspace, output = tmp_path / "private", tmp_path / "reports"
    kwargs = {
        "sample": source,
        "summary_path": summary,
        "caches": (p2, p1),
        "workspace": workspace,
        "output": output,
    }
    result = mod.run(**kwargs)
    assert result["n_faixas"] == 6 and result["n_consultas"] == 4
    assert result["status_por_faixa"] == {
        "accepted": 2,
        "instrumental": 1,
        "pending_search": 2,
        "insufficient_metadata": 1,
        "cache_error": 0,
    }
    final = pl.read_parquet(workspace / "resultados_faixas.parquet")
    assert final.select(sample.columns).equals(sample)
    lyrics = pl.read_parquet(workspace / "letras_aceitas.parquet")
    assert lyrics.height == 1 and result["n_textos_reutilizados"] == 1
    assert result["recuperacao_integral_concluida"] is False
    assert result["dump_acessado"] is False
    again = mod.run(**kwargs)
    assert again["arquivos_privados_sha256"] == result["arquivos_privados_sha256"]
    assert [mod.stamp(p) for p in [p2, p1]] == stamps
    public = (output / "resumo_reaproveitamento.json").read_text(encoding="utf-8")
    assert "Letra sintética" not in public and "Texto sintético" not in public
