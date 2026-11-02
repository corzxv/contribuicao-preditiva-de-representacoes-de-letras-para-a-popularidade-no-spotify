"""Audita arquivos versionados sem abrir dados privados ou executar a pipeline."""

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
EXCLUDED = {
    "docs/next_steps_lyrics.md",
    "docs/demonstrador_local.md",
    "tests/test_local_demo_ui.py",
    "reports/run_summary.json",
    "reports/run_summary_v0_1_1_revision.json",
    "reports/tables/spotify_audit.json",
    "reports/tables/match_review_sample_v0_1_1.json",
    "reports/matching_temporal_audit_v0_1_1_revision.md",
    "reports/handoff_base_v0_1_1.md",
    "reports/handoff_base_v0_1_1_revision.md",
    "reports/fixture_run_summary.json",
}
ROOT_FILES = {
    ".env.example",
    ".gitignore",
    ".gitattributes",
    ".python-version",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "requirements-lock.txt",
    "requirements-cientificos.txt",
}
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".jsonl",
    ".tex",
    ".bib",
    ".txt",
    ".toml",
}
SECRET_PATTERNS = {
    "token_github": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "token_huggingface": re.compile(r"\bhf_[A-Za-z0-9]{30,}"),
    "chave_privada": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    "credencial_url": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
    "chave_aws": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}
INDIVIDUAL_COLUMNS = {
    "trackid",
    "spotifytrackid",
    "compositionkey",
    "textcomponentid",
    "plainlyrics",
    "syncedlyrics",
    "acceptedtext",
}


def normalize_key(value):
    return re.sub(r"[^a-z]", "", value.lower())


def allowed_path(name):
    """Lista de publicação; arquivos excluídos continuam disponíveis no disco."""
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name or name in EXCLUDED:
        return False
    if name in ROOT_FILES:
        return True
    if name in {
        "output/pdf/monografia_template_200k_v2.pdf",
        "reports/monografia_template_200k_v2.zip",
    }:
        return True
    if name.startswith(".github/workflows/"):
        return p.suffix in {".yml", ".yaml"}
    if name.startswith("data/"):
        return name in {
            f"data/{part}/.gitkeep" for part in ("raw", "interim", "processed", "rejected")
        }
    if name.startswith("configs/"):
        return p.suffix in {".yaml", ".json"} and name != "configs/data_sources.yaml"
    if name.startswith(("src/tcc_music_popularity/", "scripts/")):
        return p.suffix == ".py" and "__pycache__" not in p.parts
    if name.startswith("tests/"):
        return p.suffix == ".py" or (
            name.startswith("tests/fixtures/") and p.suffix in {".csv", ".jsonl"}
        )
    if name.startswith("docs/"):
        return p.suffix in {".md", ".json"}
    if name.startswith("reports/"):
        return p.name != "owner.json" and (
            p.name == ".gitkeep"
            or p.suffix in {".md", ".json", ".csv", ".png", ".svg", ".tex", ".bib"}
        )
    return False


def individual_payload(value):
    """Distingue metadados de schema de exemplos com identificadores individuais."""
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = normalize_key(key)
            if normalized in {"trackid", "spotifytrackid", "trackids", "spotifytrackids"}:
                candidates = item if isinstance(item, list) else [item]
                if any(
                    isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9]{22}", v) for v in candidates
                ):
                    return True
            if (
                normalized in {"plainlyrics", "syncedlyrics", "acceptedtext"}
                and isinstance(item, str)
                and "\n" in item
                and len(item) > 80
            ):
                return True
            if individual_payload(item):
                return True
    elif isinstance(value, list):
        return any(individual_payload(item) for item in value)
    return False


def inspect_bytes(name, content):
    """Retorna somente categorias de problema, nunca valores de segredos/textos."""
    issues = []
    if not allowed_path(name):
        issues.append("caminho_fora_da_publicacao")
    if len(content) > MAX_BYTES:
        return issues + ["arquivo_excede_8_mib"]
    suffix = PurePosixPath(name).suffix
    if suffix == ".zip":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(i.file_size for i in archive.infolist()) > MAX_TOTAL:
                    return issues + ["pacote_excede_orcamento"]
                for item in archive.infolist():
                    if item.is_dir():
                        continue
                    nested = "reports/monografia_template_200k_v2/" + item.filename
                    issues.extend(inspect_bytes(nested, archive.read(item)))
        except zipfile.BadZipFile:
            issues.append("pacote_zip_invalido")
    elif suffix in TEXT_EXTENSIONS or name == ".env.example":
        text = content.decode("utf-8-sig", errors="replace")
        issues.extend(label for label, pattern in SECRET_PATTERNS.items() if pattern.search(text))
        if suffix == ".csv" and not name.startswith("tests/fixtures/"):
            header = next(csv.reader(io.StringIO(text)), [])
            if any(normalize_key(c) in INDIVIDUAL_COLUMNS for c in header):
                issues.append("tabela_individual_ou_letra")
        if suffix == ".json":
            try:
                if individual_payload(json.loads(text)):
                    issues.append("conteudo_individual_ou_letra")
            except json.JSONDecodeError:
                issues.append("json_invalido")
    return sorted(set(issues))


def git(*args, root=ROOT):
    return subprocess.check_output(["git", *args], cwd=root)


def audit(root=ROOT, plan=False):
    """Na publicação, lê blobs do índice; --planejar apenas classifica arquivos."""
    tracked = set(git("ls-files", "-z", root=root).decode().split("\0")) - {""}
    names = set(tracked)
    if plan:
        names.update(
            git("ls-files", "--others", "--exclude-standard", "-z", root=root).decode().split("\0")
        )
        names.discard("")
    results, excluded, total = [], [], 0
    for name in sorted(names):
        if plan and not allowed_path(name):
            excluded.append({"path": name, "tracked": name in tracked})
            continue
        content = (root / name).read_bytes() if plan else git("show", f":{name}", root=root)
        total += len(content)
        results.append(
            {
                "path": name,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "issues": inspect_bytes(name, content),
            }
        )
    if total > MAX_TOTAL:
        raise ValueError("Publicação excede orçamento de 64 MiB; revisar arquivos")
    return {
        "mode": "planejamento" if plan else "indice_git",
        "files": results,
        "excluded": excluded,
        "bytes": total,
        "issues": sum(bool(r["issues"]) for r in results),
    }


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--planejar",
        action="store_true",
        help="Classifica candidatos sem adicionar arquivos ao Git",
    )
    parser.add_argument("--saida", type=Path, help="Salva o inventário sem conteúdo individual")
    args = parser.parse_args()
    result = audit(plan=args.planejar)
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "mode": result["mode"],
                "files": len(result["files"]),
                "excluded": len(result["excluded"]),
                "bytes": result["bytes"],
                "issues": result["issues"],
            }
        )
    )
    for row in result["files"]:
        if row["issues"]:
            print(json.dumps({"path": row["path"], "issues": row["issues"]}, ensure_ascii=False))
    return 1 if result["issues"] else 0
