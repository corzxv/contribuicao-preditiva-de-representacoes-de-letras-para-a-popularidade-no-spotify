"""Render new V0.7 reports from the diagnosis only; never load scientific targets."""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict

import polars as pl

from .diagnostics_v070 import FIGURES, PRIVATE, ROOT, SUMMARY
from .io import sha256_file
from .local_demo import MODELS
from .local_demo_delivery import privacy_audit, scientific_hashes


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def fmt(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "---|" * len(headers),
            *["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows],
        ]
    )


def label(name):
    return MODELS.get(name, "Dummy")


def write(path, content):
    (ROOT / path).write_text(content.rstrip() + "\n", encoding="utf-8")


def verify_delivery():
    """Check joins' recorded assertions, saved aggregate totals and preserved original bytes."""
    summary = load(SUMMARY)
    before = load(f"{PRIVATE}/preservation_before.json")
    assert scientific_hashes(ROOT) == before["scientific_hashes"]
    assert all(
        sha256_file(ROOT / p) == h for p, h in before["git"]["preexisting_file_hashes"].items()
    )
    assert all(
        sha256_file(ROOT / r["path"]) == r["sha256_before"]
        for r in summary["metadata_read_projections"]
    )
    csv = pl.read_csv(ROOT / "reports/diagnostico_erros_agregados_v0_7.csv")
    assert csv.filter(pl.col("dimension") == "overall").height == 10
    for dataset, n in (("development_oof", 7648), ("holdout_v0_6", 2592)):
        for model in [*MODELS, "dummy__baseline"]:
            for dimension in ("target_bin", "prediction_bin"):
                part = csv.filter(
                    (pl.col("set") == dataset)
                    & (pl.col("model") == model)
                    & (pl.col("dimension") == dimension)
                )
                assert part.height == 12 and part["n"].sum() == n
    fields = [
        c
        for c in csv.columns
        if c not in ("set", "model", "dimension", "group", "n", "small_group")
    ]
    small = csv.filter(pl.col("small_group"))
    assert all(small[c].null_count() == small.height for c in fields)
    for row in summary["errors"]["overall"]:
        observed = csv.filter(
            (pl.col("set") == row["set"])
            & (pl.col("model") == row["model"])
            & (pl.col("dimension") == "overall")
        ).row(0, named=True)
        assert all(
            abs(observed[k] - row[k]) <= 1e-12 for k in ("mae", "rmse", "r2", "mean_residual")
        )
    assert max(r["abs_difference"] for r in summary["errors"]["reconciliation"]) <= 1e-10
    public = [
        "reports/diagnostico_amostra_modelos_v0_7.md",
        "reports/diagnostico_erros_agregados_v0_7.csv",
        "reports/plano_revisao_estatistica_v0_7.md",
        SUMMARY,
        "src/tcc_music_popularity/diagnostics_v070.py",
        "src/tcc_music_popularity/diagnostics_report_v070.py",
        "tests/test_diagnostics_v070.py",
    ]
    # Individual IDs and exact keys must stay in the private dossier, not shareable outputs/code.
    for case in load(f"{PRIVATE}/reported_cases_inference.json"):
        for path in public:
            text = (ROOT / path).read_text(encoding="utf-8")
            assert case["metadata"]["track_id"] not in text
            assert case["metadata"]["composition_key"] not in text
    private_paths = [
        p.relative_to(ROOT).as_posix() for p in (ROOT / PRIVATE).iterdir() if p.is_file()
    ]
    ignored = subprocess.run(
        ["git", "check-ignore", *private_paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    assert set(ignored) == set(private_paths)
    assert (
        subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        == before["git"]["staged"]
    )
    result = {
        "status": "verified",
        "frozen_artifacts": len(before["scientific_hashes"]),
        "preexisting_files": len(before["git"]["preexisting_file_hashes"]),
        "metadata_inputs": len({r["path"] for r in summary["metadata_read_projections"]}),
        "case_inference_count": 12,
        "metrics_reconciled": 30,
        "aggregate_rows": csv.height,
        "small_groups_suppressed": small.height,
        "private_files_ignored": len(private_paths),
        "privacy": privacy_audit(ROOT),
        "output_hashes": {p: sha256_file(ROOT / p) for p in public if p != SUMMARY},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def render():
    summary = load(SUMMARY)
    cov, source, err = summary["coverage"], summary["source_trace"], summary["errors"]
    parts = [
        "# Diagnóstico da amostra e dos modelos — V0.7",
        "## Escopo e conclusão",
        "Diagnóstico exploratório, posterior à abertura da V0.6. A primeira avaliação permanece encerrada e inalterada. Não houve ajuste, seleção de modelos, calibração, nova coleta, alteração de split nem mudança da interface. Tradicional continua sendo o candidato predefinido. O objetivo é estimar a popularidade observada no snapshot da fonte para a faixa representante de uma composição operacional; não popularidade universal da composição, causalidade ou sucesso comercial futuro.",
        "A conferência dos três casos não encontrou defeito de interface nem troca de linhas/chaves/alvos. Encontrou erro preditivo real em um caso e limitações documentais de versão/ano nos outros. A correspondência entre gravações e entre textos líricos de fontes diferentes não está certificada. Detalhes individuais, IDs, previsões completas, alternativas e contribuições estão exclusivamente no artefato privado `data/derived/private_diagnostics_v0_7/casos_relatados.md` e nos JSONs associados.",
        "## Preservação e acesso ao alvo",
        f"Git: branch `{summary['preservation']['branch']}`, HEAD `{summary['preservation']['head']}`. Estado inicial, stage e hashes dos arquivos pessoais estão em `data/derived/private_diagnostics_v0_7/preservation_before.json`. Foram conferidos {summary['preservation']['scientific_artifacts']} artefatos científicos selados e {summary['preservation']['preexisting_files']} arquivos preexistentes rastreados/não ignorados; hashes preservados. Nenhum commit, push, reset ou staging.",
        "Somente os alvos das 7.648 composições de desenvolvimento já autorizadas e das 2.592 do holdout aberto foram desserializados. Cobertura, reserva, catálogo original e candidatos futuros usam projeções explícitas sem popularidade, contagens de sucesso ou quintis. Ler bytes para SHA-256 não desserializa os alvos. A lista de projeções e hashes está no run summary. Não foram lidos caches nem textos de letras. Vetores congelados foram usados apenas internamente na inferência; não exportados.",
        "## 1. Cobertura: denominadores e perdas",
        f"Fonte Spotify: {source['original_source_rows']:,} linhas e track_ids únicos; {source['source_unique_compositions']:,} chaves operacionais não nulas; {source['source_normalized_artists']:,} nomes normalizados. Matching aceito: 111.758 / 1.159.764 = {111758 / 1159764:.4%}. As contagens abaixo de artistas são grupos operacionais, não identidades universais.",
        table(
            ["Status Spotify após matching", "Faixas"],
            [[r["match_status"], r["len"]] for r in source["source_matching_statuses"]],
        ),
    ]
    all_counts = [r for r in cov["funnel"] if r["split"] == "all"]
    parts += [
        table(
            ["Etapa", "Faixas/linhas", "Composições", "Artistas", "≥1 flag de versão"],
            [
                [r["stage"], r["rows"], r["compositions"], r["artists"], r["special_versions"]]
                for r in all_counts
            ],
        ),
        table(
            ["Etapa", "Development", "Holdout"],
            [
                [
                    r["stage"],
                    next(
                        x["rows"]
                        for x in cov["funnel"]
                        if x["stage"] == r["stage"] and x["split"] == "development_train"
                    ),
                    next(
                        x["rows"]
                        for x in cov["funnel"]
                        if x["stage"] == r["stage"] and x["split"] == "holdout_test"
                    ),
                ]
                for r in all_counts
            ],
        ),
        "A passagem de 111.758 pares para 111.422 representantes deixa 22 registros sem chave e colapsa 314 linhas adicionais de chaves repetidas; não elimina 336 composições válidas. O total de chaves não nulas já era 111.422. A reserva de 2.000 não é uma etapa aditiva posterior aos 15.000: só os dois primeiros lotes, 1.000 registros, foram ativados; 1.000 permaneceram inativos.",
        "Maior redução desde a base integrada: a amostragem por hash, de 111.422 elegíveis para 15.000 efetivamente consultados (13,4623%; 96.422 não consultados). Desses 15.000, 10.240 foram aceitos (68,2667%) e 4.760 não foram. Da fonte original, a maior perda antecede isso: 1.048.006 faixas não têm matching aceito. São razões diferentes: cobertura/matching, orçamento amostral e aceite da letra. Não há perda adicional entre letra aceita e matriz final, nem entre as 2.592 linhas do holdout e catálogo da aplicação.",
        table(
            ["Status de coleta", "Development", "Holdout", "Total"],
            [
                [
                    status,
                    sum(
                        r["len"]
                        for r in cov["lyrics_statuses"]
                        if r["final_status"] == status and r["split"] == "development_train"
                    ),
                    sum(
                        r["len"]
                        for r in cov["lyrics_statuses"]
                        if r["final_status"] == status and r["split"] == "holdout_test"
                    ),
                    sum(r["len"] for r in cov["lyrics_statuses"] if r["final_status"] == status),
                ]
                for status in sorted({r["final_status"] for r in cov["lyrics_statuses"]})
            ],
        ),
        "`request_error` soma 657 casos (4,38% das 15.000 consultas), diferente de `not_found` (644), instrumental (109) ou ambiguidades (3.350). Não interpretar erro HTTP como ausência de letra. A reconciliação V0.4 já distinguia 0 exceções de transporte de 657 resultados HTTP/consulta sem êxito.",
    ]
    rates = defaultdict(lambda: defaultdict(int))
    for r in cov["strata"]:
        rates[r["dimension"], r["group"]][r["stage"]] += r["n"]
    rate_rows = []
    for (dimension, group), counts in sorted(rates.items()):
        n = counts["queried_main_and_reserve"]
        rate_rows.append(
            [
                dimension,
                group,
                counts["eligible_representatives"],
                n,
                counts["final_matrix"],
                counts["final_matrix"] / n if n else None,
            ]
        )
    parts += [
        "### Perdas estratificadas",
        "Taxa de aceite = final / efetivamente consultado no estrato. Não é efeito causal do gênero, método ou flag. Todas as contagens, incluindo split e as oito flags separadas, estão em `coverage.strata` no run summary.",
        table(
            ["Dimensão", "Grupo", "Elegíveis", "Consultados", "Finais", "Aceite (0–1)"],
            [
                r
                for r in rate_rows
                if r[0] in ("period_diag", "match_method", "any_version", "artist_size_bin")
            ],
        ),
        "`artist_size_bin` conta composições elegíveis por artista (não quantidade de faixas nem popularidade). As composições são as unidades amostradas; artistas de catálogo maior podem aparecer com mais composições.",
        table(
            ["Gênero", "Elegíveis", "Consultados", "Finais", "Aceite (0–1)"],
            [r[1:] for r in rate_rows if r[0] == "genre"],
        ),
        "### Múltiplas versões e matching 1:1",
        "As contagens seguintes são faixas Spotify, agrupadas pelo número de registros que compartilham a chave operacional na fonte. Chaves normalizadas não garantem mesma obra/gravação. A regra 1:1 penaliza ambiguidades: candidatos determinísticos são contados antes de aceitar o par; não se escolhe arbitrariamente uma versão entre muitos candidatos. Matching temporal não é requisito de aceitação. Fuzzy é somente revisão, limitado no código, não evidência de ausência em toda a fonte LFM2b.",
    ]
    version_rows = []
    for group in ("1", "2-5", "6+"):
        rows = [r for r in source["matching_by_version_count"] if r["versions_bin"] == group]
        n = sum(r["len"] for r in rows)
        accepted = sum(r["len"] for r in rows if r["match_status"].startswith("accepted"))
        ambiguous = sum(r["len"] for r in rows if r["match_status"] == "ambiguous")
        version_rows.append([group, n, accepted, accepted / n, ambiguous, ambiguous / n])
    parts += [
        table(
            ["Versões/chave na fonte", "Faixas", "Aceitas", "Taxa", "Ambíguas", "Taxa ambígua"],
            version_rows,
        ),
        "A queda da taxa de aceite com multiplicidade é associação observada, não estimativa causal. Representantes são escolhidos somente entre matches aceitos: preferência por ausência de live/remix/acoustic/karaoke; depois status, método, score, completude, menor spotify_row_id e track_id. Uma gravação de estúdio disponível no Spotify, mas sem match aceito, não concorre nessa escolha.",
        "## 2. Artistas, versões, anos e flags",
        table(
            ["Artista", "Etapa", "Faixas", "Composições", "Grupos artista"],
            [
                [r["artist"], r["stage"], r["tracks"], r["compositions"], r["artists"]]
                for r in source["artist_stage_counts"]
                if r["split"] == "all"
            ],
        ),
        "Foram rastreadas todas as 232 faixas locais desses três artistas: 103 + 51 + 78. A lista privada `artist_track_trace.json` contém cada título e a primeira etapa responsável pela exclusão, preservando também flags e indicadores de presença. `matching_candidates_artists.json`, `matched_artists_audio_lfm.json`, `artist_composition_version_groups.json` e `artists_lrclib_metadata.json` detalham candidatos, chaves, alternativas e coleta. Não houve seleção por acerto/erro nem inferência de quais músicas deveriam ser os maiores sucessos.",
        table(
            ["Nome observado Spotify", "Grupos artista", "Splits", "Split"],
            [
                [r["artist_name_raw"], r["artist_groups"], r["split_count"], ", ".join(r["splits"])]
                for r in source["artist_group_fragmentation"]
            ],
        ),
        "As variações de caixa/pontuação observadas (inclusive Alice In Chains versus Alice in Chains nas fontes e apóstrofo em Guns N’ Roses) convergem na normalização conservadora. Não apareceu fragmentação desses três nomes entre os grupos aceitos. Globalmente, cruzamentos de artist_group_id, composition_key e split_group_id entre splits: zero. Isso não certifica aliases desconhecidos; não existe catálogo externo de identidades para resolver todo pseudônimo/colaboração.",
        f"O CSV Spotify original e o normalizado têm a mesma contagem. O ano bruto está entre {source['raw_year_min']} e {source['raw_year_max']}; {source['raw_outside_2000_2023']} linhas fora do intervalo. O código apenas rotula coortes temporais, não remove aqui faixas fora do intervalo. Assim, a ausência de gravações antigas pode estar no recorte da fonte, não em uma exclusão adicional comprovada da pipeline. Relançamentos/versões podem trazer datas posteriores, mas `year` não tem semântica documentada suficiente para afirmar se é lançamento original, álbum ou versão. Um ano no título é evidência textual, não confirmação documental da primeira gravação. `genre` é o rótulo da fonte, cujo método de curadoria não está documentado.",
        "### Auditoria das flags",
        table(
            [
                "Etapa",
                "Sinal textual",
                "n",
                "Sinal presente",
                "Sinal sem flag",
                "Flag sem contexto específico",
            ],
            [
                [
                    r["stage"],
                    r["signal"],
                    r["n"],
                    r["signal_count"],
                    r["signal_without_flag"],
                    r["flag_without_specific_context"],
                ]
                for r in source["flag_signals"]
                if r["stage"]
                in (
                    "source",
                    "integrated",
                    "eligible_representatives",
                    "queried_main_and_reserve",
                    "final_matrix",
                    "demo_catalog",
                )
            ],
        ),
        "`live_context` procura live at/in/from/on, (live) ou sufixo - live; remaster e remix usam palavras explícitas. Ausência de divergência nessa checagem lexical não valida semanticamente as flags: o código original usa `\\blive\\b` em qualquer parte do título e `mix` pode acionar remix. Título com a palavra inglesa live não demonstra apresentação ao vivo. Contagens de 'flag sem contexto' são candidatos a revisão, não erros adjudicados.",
        f"Detector adicional independente: {source['version_context_without_any_flag']['n_source']} títulos da fonte contêm unplugged/recorded at/concert/session sem nenhuma das oito flags; {source['version_context_without_any_flag']['n_integrated']} entraram na base integrada e {source['version_context_without_any_flag']['n_final']} na matriz final. São indícios para auditoria privada, não correções automáticas. A taxa real de falsos positivos/negativos não pode ser estimada sem revisão humana cega ou metadados de gravação confiáveis.",
        "## 3. Conferência técnica do demonstrador",
        f"Os três registros foram localizados nos arquivos, não por IDs presumidos. Foram executadas as 12 inferências (3 × 4 pipelines) com colunas na ordem e tipos do manifesto. As 219 entradas Baseline/LFM dos casos coincidem com a base congelada nas mesmas chaves. Comparação com previsões V0.6: diferença absoluta máxima {summary['demonstrator']['max_difference_saved']:.17g}, dentro de atol=1e-8 e rtol=1e-10. Popularidade ausente dos inputs. Observado associado por track_id + spotify_row_id; erro absoluto calculado antes do arredondamento de exibição. Trocar seleção limpa previsão e observado; estimar não revela o observado. Catálogo completo do app = holdout, sem perdas extras.",
        "Categorias desconhecidas, imputações e valores fora do mínimo/máximo univariado do treino: nenhum encontrado nos três casos (incluindo as dimensões de embeddings, sem exportar vetores). Isso não comprova suporte multivariado ou similaridade semântica. Os coeficientes foram decompostos após transformações congeladas; intercepto + soma das contribuições reproduz cada previsão. São descrições do modelo em sua codificação, dependentes de escala, one-hot e PCA; não efeitos causais ou importância universal. A decomposição completa está privada.",
        "## 4. Erros: OOF e teste separados",
        "OOF: cinco folds salvos; chaves e alvos reconciliados com a matriz de desenvolvimento. Não foram usadas previsões ajustadas no próprio treino para esses diagnósticos. Resíduo = observado − previsto. Quantis: interpolação linear NumPy; desvio padrão populacional (ddof=0); previsões sem clipping. Grupos com n<30 têm n publicado e métricas apenas no arquivo privado `all_group_metrics.json`; faixas vazias são mantidas. Não são intervalos individuais nem porcentagens de acerto.",
    ]
    for set_name, title in (
        ("development_oof", "Desenvolvimento OOF — n=7.648"),
        ("holdout_v0_6", "Holdout V0.6 — n=2.592"),
    ):
        rows = [r for r in err["overall"] if r["set"] == set_name]
        parts += [
            f"### {title}",
            table(
                ["Modelo", "MAE", "RMSE", "R²", "Resíduo médio"],
                [
                    [label(r["model"]), *[r[k] for k in ("mae", "rmse", "r2", "mean_residual")]]
                    for r in rows
                ],
            ),
            table(
                [
                    "Modelo",
                    "Mediana |erro|",
                    "P75",
                    "P90",
                    "P95",
                    "≤5 (%)",
                    "≤10 (%)",
                    "≤20 (%)",
                    ">20 n",
                    ">20 (%)",
                ],
                [
                    [
                        label(r["model"]),
                        *[r[k] for k in ("ae_median", "ae_p75", "ae_p90", "ae_p95")],
                        *[100 * r[k] for k in ("prop_ae_le_5", "prop_ae_le_10", "prop_ae_le_20")],
                        r["count_ae_gt_20"],
                        100 * r["prop_ae_gt_20"],
                    ]
                    for r in rows
                ],
            ),
            table(
                ["Distribuição", "Média", "DP", "Mín", "P5", "P25", "P50", "P75", "P95", "Máx"],
                [
                    [
                        "Observado",
                        *[
                            rows[0][f"observed_{k}"]
                            for k in (
                                "mean",
                                "std_ddof0",
                                "min",
                                "p05",
                                "p25",
                                "p50",
                                "p75",
                                "p95",
                                "max",
                            )
                        ],
                    ],
                    *[
                        [
                            label(r["model"]),
                            *[
                                r[f"predicted_{k}"]
                                for k in (
                                    "mean",
                                    "std_ddof0",
                                    "min",
                                    "p05",
                                    "p25",
                                    "p50",
                                    "p75",
                                    "p95",
                                    "max",
                                )
                            ],
                        ]
                        for r in rows
                    ],
                ],
            ),
        ]
    parts += [
        "### Distribuição em faixas fixas",
        table(
            ["Faixa/corte", "OOF n", "Teste n"],
            [
                [
                    r["bin"],
                    r["n"],
                    next(
                        t["n"]
                        for t in err["target_distribution"]
                        if t["set"] == "holdout_v0_6" and t["bin"] == r["bin"]
                    ),
                ]
                for r in err["target_distribution"]
                if r["set"] == "development_oof"
            ],
        ),
        "Faixas [0,10), …, [90,100]; cortes >40, >60 e >80 são estritos e se sobrepõem (não somar essas linhas). Há somente 27 observações ≥70 no desenvolvimento e 9 no teste; >80: 0 e 2. Não foi aberto o alvo dos registros que não entraram na matriz final para investigar essa seleção. O perfil histórico de matching já publicado (média 27,1641 em aceitos versus 17,4467 em não aceitos, `reports/tables/selection_bias.json`) é reutilizado apenas como contexto agregado, sem reabrir esses alvos.",
        "### Condicionamento pelo alvo versus pela previsão",
        "Subestimar grupos definidos pelo alvo alto não demonstra, por si só, falta de calibração. O alvo tem ruído residual e maior dispersão que a estimativa condicional; mesmo um modelo calibrado pode apresentar esse padrão. A tabela por previsão pergunta algo diferente: qual observado médio entre músicas que receberam previsões semelhantes? Não houve ajuste de calibrador nem novo teste de significância.",
    ]
    for dimension in ("target_bin", "prediction_bin", "period_diag", "any_version"):
        rows = [
            r
            for r in err["public_group_metrics"]
            if r["model"] == "elastic_net__traditional"
            and r["dimension"] == dimension
            and r["group"] not in ("<0", ">100")
        ]
        parts += [
            f"#### Tradicional: {dimension}",
            table(
                [
                    "Conjunto",
                    "Grupo",
                    "n",
                    "MAE",
                    "Resíduo médio",
                    "Prev. média",
                    "Obs. média",
                    ">20 (%)",
                ],
                [
                    [
                        r["set"],
                        r["group"],
                        r["n"],
                        r["mae"],
                        r["mean_residual"],
                        r["predicted_mean"],
                        r["observed_mean"],
                        None if r["prop_ae_gt_20"] is None else 100 * r["prop_ae_gt_20"],
                    ]
                    for r in rows
                ],
            ),
        ]
    parts += [
        "No Tradicional do teste, por alvo: MAE 18,1659 na faixa [60,70), n=40, contra 5,2664 em [20,30), n=720. Por previsão: as médias observadas de 15,7325, 24,1659 e 34,5298 acompanham previsões médias de 15,9240, 25,0860 e 34,1930 nas faixas centrais. Há desvios descritivos nos extremos, mas não evidência suficiente para aplicar uma correção global arbitrária. No período 2020–2023, MAE 8,6411 (n=77), versus 7,0209 em 2000–2009 (n=713); composição de gênero/artistas e tamanho amostral diferem. As flags de versão não concentram sozinhas todo o erro: MAE 7,1901 (n=98) com flag e 7,1828 (n=2.494) sem flag.",
        "Gêneros, períodos, cada flag, quatro blocos e Dummy: resultados completos no CSV agregado; células pequenas explicitamente identificadas, sem ranking conclusivo de grupos raros.",
        "### Quanto os blocos mudam as previsões?",
        table(
            [
                "Conjunto",
                "A",
                "B",
                "n",
                "Pearson",
                "Média |Δŷ|",
                "Mediana",
                "P95",
                "Máximo",
                "|Δŷ|>5 (%)",
            ],
            [
                [
                    r["set"],
                    label(r["a"]),
                    label(r["b"]),
                    r["n"],
                    r["pearson"],
                    r["mean_abs_difference"],
                    r["median_abs_difference"],
                    r["p95_abs_difference"],
                    r["max_abs_difference"],
                    100 * r["prop_abs_difference_gt_5"],
                ]
                for r in err["prediction_comparisons"]
            ],
        ),
        "No teste, os acréscimos textuais mudam a previsão Baseline em média 1,4654 / 1,5240 / 1,9860 pontos; correlações 0,9842 / 0,9810 / 0,9689. Isso é compatível com contribuição incremental pequena, não prova inutilidade de letras. O ganho de MAE oficial do Tradicional é apenas 0,019798 ponto; não redefinir o candidato usando o holdout. PCAs retêm variância de X, não necessariamente o sinal mais relevante a y; não há teste aqui que demonstre que trocar o embedding solucionaria a cauda.",
        "## 5. Entradas efetivas e função de ajuste",
        table(
            ["Modelo", "Inputs", "Depois de transformar", "PCA LFM", "PCA MiniLM"],
            [
                [
                    label(r["model"]),
                    r["input_features"],
                    r["transformed_features"],
                    r["pca"].get("traditional", {}).get("n_components"),
                    r["pca"].get("embedding", {}).get("n_components"),
                ]
                for r in summary["demonstrator"]["pipelines"]
            ],
        ),
        "Baseline: 23 entradas. Categóricas nominais: genre, key, time_signature → imputação pela moda e one-hot; desconhecidas ignoradas. As outras 20 entradas usam mediana + indicador de ausência e padronização: year (linear), características acústicas, mode binária e oito flags semânticas booleanas. As flags não foram confundidas com qf_* técnicas: estão explicitamente permitidas. Remoção de constantes ocorre após concatenar, não uma proibição semântica de flags. Listas, ordem, dtypes e dimensões conferem com o manifesto.",
        "LFM2b: 196 descritores, imputação e indicadores, remoção de constantes, escala, PCA90 com 77 componentes, escala dos scores. MiniLM: 384 dimensões, PCA90 separada com 185 componentes; não mistura Baseline com textos. Cada PCA final registra n_samples_=7.648; a auditoria anterior V0.5 verificou os ajustes dentro dos folds. Nesta etapa somente transform/predict e inspeção de objetos já ajustados.",
        "Elastic Net minimiza perda quadrática penalizada L1/L2; a seleção interna minimizou MAE médio de três folds. Não são a mesma função objetivo. Isso é escolha metodológica documentada, não bug: justifica testar uma alternativa alinhada ao MAE, sem garantir redução de erros extremos. O coeficiente linear de year e os efeitos one-hot de genre são relevantes nas decomposições privadas, mas suas semânticas limitadas pedem cautela antes de atribuir causas.",
        "## 6. Gráficos agregados novos (V0.7)",
        *[
            f"- `{FIGURES}/{name}.png`: {caption}"
            for name, caption in (
                (
                    "distribuicoes",
                    "alvo versus previsões brutas; frequências por intervalos de dez pontos",
                ),
                (
                    "erro_acumulado",
                    "fração com erro absoluto até cada limiar inteiro, sem exportar pontos individuais",
                ),
                (
                    "erro_por_alvo",
                    "MAE e resíduo médio condicionados à faixa observada; não é sozinho diagnóstico de calibração",
                ),
                (
                    "observado_por_previsao",
                    "observado médio em faixas da previsão; n anotado refere-se ao Tradicional",
                ),
            )
        ],
        "Os quatro gráficos V0.6 permanecem byte a byte iguais. Nos gráficos de médias por faixa, células n<30 são omitidas, mas seus n permanecem no CSV. Estatísticas são descritivas, sem novos intervalos de confiança que ignorariam agrupamento por artista.",
        "## 7. Avaliação futura e limites",
        f"A exclusão de grupos conhecidos de pilotos (coorte inteira de 2.000, suplemento de 47 e modelagem de 1.441), dos 10.240 registros finais e do preview histórico de 100 linhas deixa {summary['future_evaluation']['metadata_only_candidates'][0]['compositions']:,} representantes em {summary['future_evaluation']['metadata_only_candidates'][0]['artists']:,} grupos. Excluir também todos os grupos que apareceram na coorte/reserva V0.4 deixa {summary['future_evaluation']['not_previously_sampled_groups'][0]['compositions']:,} representantes em {summary['future_evaluation']['not_previously_sampled_groups'][0]['artists']:,} grupos. As listas são apenas candidatos de metadados; não um teste sorteado ou certificado como independente.",
        "Os alvos da fonte/base foram perfilados agregadamente nas etapas iniciais (`audit.py`, `validation_v011._split_audit`, relatórios de seleção). Além disso, toda a fonte orientou regras de integração. Esta exposição agregada não equivale a treino individual, mas impede afirmar sem ressalvas que o remanescente é completamente intocado. O split original foi agrupado deterministicamente, sem estratificação por alvo; quintis foram usados no piloto/desenvolvimento, não para refazer o split agora. Nova divisão dos mesmos registros examinados não restaura independência.",
        "O preview_100_linhas.csv foi lido exclusivamente pela projeção track_id, sem seus alvos/proxies; os grupos correspondentes foram excluídos. O script pessoal exp_base.py documenta outra inspeção head(5) da base original. Workbooks de preview/revisão e JSON de head foram inventariados, mas não abertos para evitar exposição adicional; a extensão exata de suas inspeções e de outras aberturas manuais permanece não certificada. Portanto, o inventário não é garantia de ausência de inspeção individual anterior.",
        "Opção mais forte: amostra externa/prospectiva, protocolo e pipeline congelados antes da abertura, identidades de artista/composição/gravação verificadas sem olhar popularidade, avaliador/gestor separado. Remanescentes locais só podem sustentar avaliação condicional com inventário de exposição e regra de elegibilidade pré-registrada; se não for possível demonstrar não exposição relevante, tratá-los como exploratórios. O V0.6 serve agora para explicação, não seleção de futuras mudanças.",
        "Sem evidência suficiente: ano original de gravação/lançamento; igualdade exata de textos LFM2b–LRCLIB ou de gravações; prevalência verdadeira de erros de flags; aliases externos não codificados; motivo externo de ausência de faixas no dataset; distribuição de popularidade dos novos candidatos (deliberadamente não lida); efeito causal das regras; ganho de qualquer revisão proposta.",
        "## 8. Reprodutibilidade e verificações",
        "Comandos executados, códigos de saída e limitações operacionais: seção `verification_commands` do run summary. CLI diagnóstica: `.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.diagnostics_v070`; renderização: `.\\.venv\\Scripts\\python.exe -X utf8 -m tcc_music_popularity.diagnostics_report_v070`. Ambos produzem somente artefatos V0.7; não chamar módulos de treino/coleta. Reexecutar a CLI recalcula diagnósticos a partir dos mesmos dados autorizados e substitui apenas suas saídas V0.7; não altera artefatos científicos anteriores.",
        f"Reconciliação MAE/RMSE/R² com as métricas publicadas: {len(err['reconciliation'])} comparações, diferença máxima {max(r['abs_difference'] for r in err['reconciliation']):.17g} (tolerância 1e-10). Joins 1:1 e contagens do funil conferidos; ausência de cruzamentos de grupos e igualdade do catálogo verificadas. Os testes da interface usam dados sintéticos via AppTest, não uma avaliação científica. Não houve inspeção manual de browser com dados novos.",
        "## Fontes locais específicas",
        "- `AGENTS.md`; `reports/final_sampling_protocol_v1_0.md`; `reports/final_analysis_protocol_v1_0.md`; `reports/final_sampling_report_v1_0.md`.\n- `reports/lyrics_scale_report_v0_4.md`; `reports/embeddings_scale_report_v0_4.md`; `reports/cohort_reconciliation_v0_4.md`.\n- `reports/final_development_execution_plan_v0_5.md`; `reports/final_matrix_audit_v0_5.md`; `reports/final_model_manifest_v0_5.json`; `reports/final_development_report_v0_5.md`.\n- `reports/final_holdout_evaluation_plan_v0_5.md`; `reports/final_holdout_report_v0_6.md`; `reports/run_summary_final_holdout_v0_6.json`.\n- `reports/feature_manifest_v0_1_1_revision.csv`: linhas year/genre (semântica parcial, fonte Spotify_1Million_Tracks).\n- `src/tcc_music_popularity/spotify.py`: normalização e coorte temporal; `normalization.py`: padrões de versão/base_title/composition_key; `matching.py`: candidatos e aceitação 1:1.\n- `src/tcc_music_popularity/final_study_v040.py`: load_target_free_source, select_representatives_without_target, deterministic_main_and_reserve.\n- `src/tcc_music_popularity/modeling_recalibration_v031.py`: build_representation_transformer; `final_development_v050.py`: tune/tune_fold e freeze_models.\n- `apps/streamlit_demo.py`; `src/tcc_music_popularity/local_demo.py`; `local_demo_delivery.py`: apresentação, chaves, predict e integridade.",
    ]
    write("reports/diagnostico_amostra_modelos_v0_7.md", "\n\n".join(parts))
    private_report()
    print("Relatório V0.7 e dossiê privado gerados; nenhum alvo adicional lido.")


def private_report():
    cases = load(f"{PRIVATE}/reported_cases_inference.json")
    audit = {r["composition_key"]: r for r in load(f"{PRIVATE}/matched_artists_audio_lfm.json")}
    lyrics = {r["composition_key"]: r for r in load(f"{PRIVATE}/artists_lrclib_metadata.json")}
    # Human interpretation is local/private too: do not hard-code individual results in Git code.
    reasons = load(f"{PRIVATE}/case_interpretations.json")
    parts = [
        "# Dossiê privado dos três casos — V0.7",
        "Arquivo local ignorado pelo Git. Não publicar. Sem texto de letra ou vetores de embedding. Todos os números individuais vêm exclusivamente do holdout V0.6 já aberto.",
    ]
    for case in cases:
        row = case["metadata"]
        key = row["composition_key"]
        a, lyric_metadata = audit[key], lyrics[key]
        parts += [
            f"## {row['artist_name_raw']} — {row['track_name_raw']}",
            reasons[key],
            table(["Campo", "Valor"], [[k, v] for k, v in row.items()]),
            table(
                ["Origem", "Artista", "Título", "Ano/duração"],
                [
                    [
                        "Spotify",
                        row["artist_name_raw"],
                        row["track_name_raw"],
                        f"year={row['year']}; {row['duration_ms']} ms",
                    ],
                    [
                        "LFM2b",
                        a["lfm_artist_name_raw"],
                        a["lfm_track_name_raw"],
                        f"lfm_release_year={a['lfm_release_year']}",
                    ],
                    [
                        "LRCLIB",
                        lyric_metadata["selected_returned_artist"],
                        lyric_metadata["selected_returned_title"],
                        f"{lyric_metadata['selected_returned_duration_seconds']} s; Δ={lyric_metadata['selected_duration_difference_seconds']} s",
                    ],
                ],
            ),
            f"Matching: {a['match_method']}; status={a['match_status']}; version_compatible={a['version_compatible']}; temporal_compatible={a['temporal_compatible']}. Registro LFM: `{a['lfm_record_key']}`. Letra: {lyric_metadata['final_status']}. Alvo observado: {case['observed']!r}.",
            table(
                [
                    "Modelo",
                    "Previsão completa (float repr)",
                    "Erro absoluto completo",
                    "Diferença V0.6",
                    "UI",
                ],
                [
                    [
                        label(m),
                        repr(p),
                        repr(case["absolute_errors"][m]),
                        repr(case["difference_from_saved"][m]),
                        case["ui_two_decimals"][m],
                    ]
                    for m, p in case["predictions"].items()
                ],
            ),
            "As colunas, tipos e ordem conferem com os manifestos; Baseline/LFM coincidem com a base congelada para as mesmas chaves. O fingerprint das 603 features congeladas está no JSON; não expomos o vetor. Seleção diferente apaga valores, e revelar exige estimar antes. Alvo lido por track_id + spotify_row_id.",
        ]
        for model, info in case["pipeline_diagnostics"].items():
            parts += [
                f"### {label(model)}: diagnóstico da entrada e decomposição",
                f"Input={info['input_features']}; transformado={info['transformed_features']}; categorias desconhecidas={info['unknown_categories']}; imputadas={info['imputed_features']}; fora do min/max numérico={info['outside_training_numeric_range_excluding_embeddings']}; dimensões de embedding fora do min/max={info['embedding_dimensions_outside_training_range_count']}. Valores dentro dos limites univariados não garantem suporte conjunto.",
                table(
                    ["Parcela", "Contribuição em pontos"],
                    [
                        ["intercepto", info["intercept"]],
                        *list(info["block_contributions"].items()),
                        ["soma reconstruída", info["prediction_reconstructed"]],
                    ],
                ),
                table(
                    ["Termo transformado (8 maiores |contribuições|)", "Contribuição"],
                    [
                        [r["transformed_feature"], r["contribution_points"]]
                        for r in info["contributions"][:8]
                    ],
                ),
            ]
    parts += [
        "## Limitação reproduzível nas flags, sem correção",
        "`classify_version('Live And Let Die')['live']` retorna True porque a regex busca live como palavra em qualquer posição. A palavra faz parte do título e não fornece por si evidência de versão ao vivo. Duas linhas desse título dos artistas auditados carecem de contexto explícito live-at/-live; a verdade da gravação permanece não confirmada. Trata-se de regra lexical insuficiente, não prova de erro de associação da interface. Há também 1.246 títulos com unplugged/recorded at/concert/session sem flag na fonte (78 integrados, 4 finais). Não houve alteração de flag, chave, dado ou modelo.",
        "## Inventário privado",
        "- `artist_track_trace.json` e `.csv`: todas as 232 faixas dos três artistas; primeira etapa de exclusão e indicadores de presença.\n- `artist_composition_version_groups.json`: grupos com múltiplas versões e representante aceito; a ordenação é a regra original sem alvo.\n- `case_representative_alternatives.json`: todas as alternativas Spotify das três chaves específicas.\n- `original_lfm_artist_metadata.json`, `matching_candidates_artists.json`, `matched_artists_audio_lfm.json`: metadata e motivos do matching.\n- `artists_lrclib_metadata.json`: status e metadados retornados, sem texto.\n- `reported_cases_inference.json`: floats completos, inputs por nome/tipo no manifesto, fingerprint da linha e todas as contribuições.\n- `all_group_metrics.json`: inclui células pequenas que não podem ir ao relatório público.\n- `historically_unused_metadata_candidates.json` e `not_previously_sampled_group_candidates.json`: inventários sem alvo, não novos testes.\n- `version_context_without_flag.json`: candidatos lexicais para revisão, não erros confirmados.",
    ]
    write(f"{PRIVATE}/casos_relatados.md", "\n\n".join(parts))
    pl.from_dicts(load(f"{PRIVATE}/artist_track_trace.json")).write_csv(
        ROOT / PRIVATE / "artist_track_trace.csv"
    )


if __name__ == "__main__":
    render()
