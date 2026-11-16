"""Proteções de publicação com dados sintéticos, sem rede ou bases reais."""

import io
import json
import zipfile

import pytest

from tcc_music_popularity.git_publication import allowed_path, inspect_bytes


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/catalogo.csv",
        "data/derived/private/a.json",
        ".env",
        "configs/data_sources.yaml",
        "preview_100_linhas.csv",
        "reports/amostra.parquet",
        "apps/streamlit_demo.py",
        "Template_Relatório_TCC.zip",
        "../credencial.json",
    ],
)
def test_exclui_dados_e_materiais_locais(path):
    assert not allowed_path(path)


def test_agregado_permitido_e_faixa_individual_bloqueada():
    path = "reports/modelagem_200k_v1/integral/metricas_externas.csv"
    assert inspect_bytes(path, b"model,n,mae\nbaseline,77535,8.35\n") == []
    assert "tabela_individual_ou_letra" in inspect_bytes(
        path, b"track_id,prediction\nsynthetic,0\n"
    )


def test_schema_nao_e_confundido_com_identificador_real():
    path = "reports/schema.json"
    assert inspect_bytes(path, json.dumps({"track_id": {"missing": 0}}).encode()) == []
    payload = {"rows": [{"spotify_track_id": "A" * 22}]}
    assert "conteudo_individual_ou_letra" in inspect_bytes(path, json.dumps(payload).encode())


def test_segredo_e_detectado_sem_expor_valor():
    fake = "ghp_" + "A" * 36
    result = inspect_bytes("README.md", fake.encode())
    assert result == ["token_github"] and fake not in repr(result)


@pytest.mark.parametrize(
    "pacote",
    [
        "reports/monografia_template_200k_v2.zip",
        "reports/monografia_template_overleaf.zip",
    ],
)
def test_zip_nao_contorna_restricao_de_dados(pacote):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("dados.csv", "track_id,popularity\nsynthetic,0\n")
    assert "tabela_individual_ou_letra" in inspect_bytes(pacote, stream.getvalue())


def test_zip_atual_aceita_instrucoes_e_rejeita_caminho_ascendente():
    pacote = "reports/monografia_template_overleaf.zip"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("LEIA_PRIMEIRO.txt", "Abrir main.tex no Overleaf.")
    assert inspect_bytes(pacote, stream.getvalue()) == []

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("../fora.csv", "categoria,n\nA,1\n")
    assert inspect_bytes(pacote, stream.getvalue()) == ["caminho_fora_da_publicacao"]
