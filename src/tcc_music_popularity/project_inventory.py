"""Inventário leve e limitado: nomes, tamanhos e categorias, sem abrir bases/modelos."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE = (
    "auditoria_catalogo_spotify_20261031",
    "amostra_spotify_200k_20261031",
    "recuperacao_letras_200k_v2",
    "parecer_letras_v2",
    "prontidao_dados_200k_v1",
    "descritores_textuais_200k_v1",
)
PENDING = ("avaliacao_letras_200k_v3", "private_sample_lyrics_200k_v3")


def classification(path):
    name = path.as_posix()
    if any(part in name for part in PENDING):
        return (
            "PENDENTE",
            "Diagnóstico v3 concluído; aplicação integral não autorizada nesta consolidação",
        )
    if any(part in name for part in ACTIVE) or "private_sample_lyrics_200k_v2" in name:
        return (
            "ATIVO",
            "Evidência do catálogo/amostra/coorte textual recente; não reexecutar automaticamente",
        )
    if name.startswith("docs/") or name in {"AGENTS.md", "README.md"}:
        if path.name in {
            "methodology_log.md",
            "next_steps_lyrics.md",
            "base_ampliada_v0_9.md",
            "demonstrador_local.md",
            "execucao_estatistica_coorte_aceita.md",
            "protocolo_coorte_aceita_v1.md",
            "execucao_manual_letras.md",
            "execucao_noturna_letras.md",
            "coleta_persistente.md",
            "busca_local_letras.md",
            "auditoria_letras_local.md",
            "revisao_estatistica_v0_8.md",
        }:
            return (
                "HISTÓRICO",
                "Documentação de universo/execução anterior; preservada, não é próxima tarefa",
            )
        return "ATIVO", "Consultar mapa e decisões para distinguir documentos históricos"
    if any(
        token in name
        for token in (
            "readiness",
            "project_inventory",
            "17_auditar",
            "18_inventariar",
            "text_descriptors",
            "19_preparar",
            "multilingual_embeddings",
            "20_preparar",
        )
    ):
        return "ATIVO", "Ferramenta de continuidade/pré-fechamento"
    if name.startswith(("src/", "tests/")):
        return (
            "REUTILIZÁVEL",
            "Lógica/testes; compatibilidade com a coorte nova precisa ser demonstrada",
        )
    if name.startswith("configs/"):
        return "REUTILIZÁVEL", "Configuração histórica; não presumir protocolo atual aprovado"
    if name.startswith("data/raw"):
        if "lfm2b" in name:
            return "HISTÓRICO", "Fonte imutável da integração antiga; não elegibilidade recente"
        return "ATIVO", "Fonte imutável; conteúdo não inspecionado pelo inventário"
    return "HISTÓRICO", "Preservar; consultar MAPA_ARTEFATOS para finalidade e escopo"


def inventory(root=ROOT):
    paths = set()
    for folder in ("src", "scripts", "tests", "configs", "docs", "reports", "apps"):
        for path in (root / folder).rglob("*"):
            if (
                path.is_file()
                and not {"__pycache__", ".pytest_cache"} & set(path.parts)
                and not path.name.startswith("inventario_projeto_")
            ):
                paths.add(path)
    paths.update(p for p in root.iterdir() if p.is_file() and p.name != ".env")
    # Somente dois níveis de derivados; não percorrer caches, pesos ou milhões de arquivos.
    for folder in ("raw", "processed", "interim", "derived", "rejected"):
        parent = root / "data" / folder
        if parent.exists():
            paths.update(p for p in parent.iterdir() if p.is_file() and p.name != ".gitkeep")
            for directory in (p for p in parent.iterdir() if p.is_dir()):
                paths.update(
                    p
                    for p in directory.iterdir()
                    if p.is_file() and p.name not in {".env", "kaggle.json"}
                )
    records = []
    for path in sorted(paths):
        relative = path.relative_to(root)
        category, note = classification(relative)
        stat = path.stat()
        records.append(
            {
                "path": relative.as_posix(),
                "category": category,
                "bytes": stat.st_size,
                "modified_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                "evidence_level": "existência/metadados; não certifica execução nem validade",
                "note": note,
            }
        )
    return {
        "created_utc": datetime.now(UTC).isoformat(),
        "root": str(root),
        "scope": "diretórios de código/documentação/relatórios; dados até 2 níveis; SSD excluído",
        "files": records,
    }


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports/inventario_projeto_20261101.json"
    )
    args = parser.parse_args()
    result = inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(result['files'])} arquivos inventariados; apenas metadados; {args.output}")
