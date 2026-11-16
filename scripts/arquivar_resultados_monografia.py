"""Preserva fontes acadêmicas e agregados, sem copiar bases, letras ou modelos."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "reports/preservacao_monografia_20261106"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    expected = {}

    def register(mapping, base=""):
        for name, value in mapping.items():
            if not isinstance(value, str) or len(value) != 64:
                continue
            path = Path(base) / name
            rel = path.relative_to(ROOT).as_posix() if path.is_absolute() else path.as_posix()
            if rel in expected and expected[rel] != value:
                raise ValueError(f"Selos históricos divergentes: {rel}")
            expected[rel] = value

    manifests = [
        "reports/monografia_consolidada_200k_v1/PROVENIENCIA_AGREGADOS.json",
        "reports/monografia_template_200k_v2/proveniencia_figuras.json",
        "reports/monografia_template_200k_v3/proveniencia_extensao.json",
    ]
    for name in manifests:
        register(json.loads((ROOT / name).read_text(encoding="utf-8"))["inputs"])
    for name in [
        "reports/monografia_consolidada_200k_v1/PRESERVACAO_ANTERIOR.json",
        "reports/monografia_template_200k_v3/PRESERVACAO_ANTERIOR.json",
    ]:
        register(json.loads((ROOT / name).read_text(encoding="utf-8")))
    prep = json.loads(
        (ROOT / "reports/preparacao_descritiva_catalogo_20261106.json").read_text(encoding="utf-8")
    )
    register(prep["preserved_previous_files"])
    v3 = json.loads(
        (ROOT / "reports/verificacao_monografia_template_200k_v3.json").read_text(encoding="utf-8")
    )
    register(v3["source_hashes"], "reports/monografia_template_200k_v3")
    register({v3["pdf"]: v3["pdf_sha256"], v3["zip"]: v3["zip_sha256"]})
    desc = json.loads(
        (ROOT / "reports/descritiva_catalogo_completo_v1/resumo_descritiva.json").read_text(
            encoding="utf-8"
        )
    )
    register(desc["arquivos"], "reports/descritiva_catalogo_completo_v1")
    files = set(expected)
    for directory in [
        "monografia_consolidada_200k_v1",
        "monografia_template_200k_v2",
        "monografia_template_200k_v3",
        "overleaf_dominio_observado_200k_v1",
        "overleaf_resultados_coorte_aceita_v1",
        "descritiva_catalogo_completo_v1",
    ]:
        for path in (ROOT / "reports" / directory).rglob("*"):
            if path.is_file():
                files.add(path.relative_to(ROOT).as_posix())
    for pattern in ["reports/*.zip", "output/pdf/*.pdf", "reports/verificacao_monografia*.json"]:
        files.update(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern))
    files.update(
        {
            "reports/interpretacao_descritiva_catalogo_completo_v1.md",
            "reports/verificacao_descritiva_catalogo_20261106.json",
            "reports/preparacao_descritiva_catalogo_20261106.json",
            "docs/ESTADO_ATUAL.md",
            "docs/CONTEXTO_TCC.md",
            "docs/PLANO_EXECUCAO.md",
            "docs/MAPA_ARTEFATOS.md",
            "docs/decisions.md",
            "docs/data_dictionary.md",
            "docs/provenance.md",
            "scripts/arquivar_resultados_monografia.py",
            "scripts/39_descrever_catalogo_completo.py",
            "src/tcc_music_popularity/catalog_description.py",
            "tests/test_catalog_description.py",
            "configs/quality_rules.yaml",
        }
    )
    records = []
    for rel in sorted(files):
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Arquivo ausente/fora do projeto: {rel}")
        if Path(rel).parts[0] not in {
            "reports",
            "output",
            "docs",
            "src",
            "scripts",
            "tests",
            "configs",
        }:
            raise ValueError(f"Área não permitida: {rel}")
        if path.stat().st_size > 10_000_000:
            raise ValueError(f"Arquivo excede limite do pacote acadêmico: {rel}")
        value = digest(path)
        if rel in expected and value != expected[rel]:
            raise ValueError(f"Conteúdo histórico alterado: {rel}")
        records.append({"arquivo": rel, "bytes": path.stat().st_size, "sha256": value})
    if sum(r["bytes"] for r in records) > 100_000_000:
        raise ValueError("Pacote excede 100 MB; revisar seleção antes de continuar.")
    if DEST.exists():
        raise FileExistsError("Preservação já existe; não será substituída.")
    DEST.mkdir()
    text = (
        "# Preservação da monografia — 06/11/2026\n\n"
        "Pacote local das versões acadêmicas, PDFs, fontes TeX, figuras/tabelas e "
        "agregados utilizados, incluindo a nova descrição completa do catálogo. "
        "Os arquivos originais permanecem nos mesmos caminhos.\n\n"
        "O ZIP preserva os caminhos relativos ao projeto. inventario.json registra "
        "tamanho e SHA-256 de cada membro. Inclui um retrato dos documentos de "
        "continuidade antes da nova amostragem; mudanças posteriores nesses "
        "documentos são normais e não alteram o retrato guardado.\n\n"
        "Bases individuais, letras, embeddings, checkpoints de treino e dump "
        "LRCLIB permanecem em seus locais originais; não foram duplicados. Seus "
        "vínculos e selos continuam nos resumos de proveniência incluídos. "
        "Não é backup externo nem comprovação de disponibilidade do SSD. "
        "A descrição 39 ainda não foi inserida em um novo PDF.\n"
    )
    (DEST / "LEIA_PRIMEIRO.md").write_text(text, encoding="utf-8")
    inventory = {
        "criado_em": datetime.now(UTC).isoformat(),
        "n_arquivos": len(records),
        "bytes_descompactados": sum(r["bytes"] for r in records),
        "selos_anteriores_conferidos": len(expected),
        "base_individual_lida": False,
        "pdfs_alterados": False,
        "arquivos": records,
    }
    (DEST / "inventario.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    target = DEST / "resultados_e_monografias.zip"
    with ZipFile(target, "x", compression=ZIP_DEFLATED) as archive:
        for r in records:
            archive.write(ROOT / r["arquivo"], r["arquivo"])
        archive.write(DEST / "inventario.json", "PRESERVACAO/inventario.json")
        archive.write(DEST / "LEIA_PRIMEIRO.md", "PRESERVACAO/LEIA_PRIMEIRO.md")
    with ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("CRC inválido no arquivo de preservação.")
        for r in records:
            if hashlib.sha256(archive.read(r["arquivo"])).hexdigest() != r["sha256"]:
                raise ValueError(f"Integridade inválida no ZIP: {r['arquivo']}")
            if digest(ROOT / r["arquivo"]) != r["sha256"]:
                raise ValueError(f"Fonte mudou durante preservação: {r['arquivo']}")
    check = {
        "concluido": True,
        "n_arquivos": len(records),
        "zip_bytes": target.stat().st_size,
        "zip_sha256": digest(target),
        "inventario_sha256": digest(DEST / "inventario.json"),
        "crc_e_todos_os_hashes_conferidos": True,
        "copia_externa": False,
        "commit_push": False,
    }
    (DEST / "verificacao.json").write_text(
        json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(check, ensure_ascii=True))


if __name__ == "__main__":
    run()
