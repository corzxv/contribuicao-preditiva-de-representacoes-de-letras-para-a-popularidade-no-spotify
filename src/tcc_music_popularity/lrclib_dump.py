"""Download fixado e extração retomável no SSD; não consulta músicas nem altera a coleta."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import struct
import time
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from .config import PROJECT_ROOT
from .io import utc_now
from .manual_lyrics import exclusive, require
from .persistent_collection import retry_after_seconds

CHUNK = 8 * 1024 * 1024
OWNER = "tcc-lrclib-dump-v1"
DEFAULT_DESTINATION = Path("D:/TCC_LRCLIB")


@dataclass(frozen=True)
class DumpSpec:
    filename: str
    url: str
    compressed_bytes: int
    database_bytes: int
    etag: str


OFFICIAL_DUMP = DumpSpec(
    filename="lrclib-db-dump-20261012T090639Z.sqlite3.gz",
    url="https://db-dumps.lrclib.net/lrclib-db-dump-20261012T090639Z.sqlite3.gz",
    compressed_bytes=47837763733,
    database_bytes=261755867136,
    etag="9595e9d143bf175845a9e41acd298884-2852",
)


class BudgetExpired(KeyboardInterrupt):
    pass


class RetryableHTTP(Exception):
    def __init__(self, status, delay=0):
        self.status, self.delay = status, delay


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save_json(path, value):
    """Checkpoint sincronizado; antivírus/leitor no Windows pode bloquear replace brevemente."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    for attempt in range(10):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.1)


def paths(destination, spec):
    archive = destination / spec.filename
    database = destination / spec.filename.removesuffix(".gz")
    return {
        "archive": archive,
        "archive_part": archive.with_name(archive.name + ".part"),
        "database": database,
        "database_part": database.with_name(database.name + ".extracting"),
        "state": destination / "dump_progress.json",
    }


def validate_destination(value):
    path = Path(value)
    require(path.is_absolute(), "Informe um caminho absoluto, por exemplo D:\\TCC_LRCLIB.")
    path = path.resolve()
    require(path != Path(path.anchor), "Use uma subpasta exclusiva, não a raiz do disco.")
    require(
        not path.is_relative_to(PROJECT_ROOT.resolve()), "O dump deve ficar fora do repositório."
    )
    require(Path(path.anchor).is_dir(), "Unidade de destino indisponível; conecte o SSD.")
    require(path.parent.is_dir(), "A pasta pai não existe; confira a letra do SSD.")
    return path


class Transfer:
    def __init__(
        self,
        destination,
        spec,
        *,
        reserve_bytes=20 * 1024**3,
        max_hours=48,
        max_retries=5,
        session=None,
        disk_usage=shutil.disk_usage,
        monotonic=time.monotonic,
        sleeper=time.sleep,
    ):
        self.destination, self.spec = destination, spec
        self.files = paths(destination, spec)
        self.reserve_bytes, self.max_retries = reserve_bytes, max_retries
        self.session = session if session is not None else requests.Session()
        self.session.headers.update(
            {"Accept-Encoding": "identity", "User-Agent": "UnB-TCC-LRCLIB-Dump/1.0"}
        )
        self.disk_usage, self.monotonic, self.sleeper = disk_usage, monotonic, sleeper
        self.deadline = monotonic() + max_hours * 3600
        self.last_print = float("-inf")
        self.state = load_json(self.files["state"])
        if self.state:
            require(
                self.state.get("owner") == OWNER and self.state.get("source") == asdict(spec),
                "Checkpoint não corresponde ao dump fixado. Nada será sobrescrito.",
            )
        else:
            require(
                not any(p.exists() for k, p in self.files.items() if k != "state"),
                "Há arquivos sem checkpoint nesta pasta. Preserve-os e use outra subpasta.",
            )
            self.state = {
                "owner": OWNER,
                "source": asdict(spec),
                "downloaded_bytes": 0,
                "download_sha256": hashlib.sha256(b"").hexdigest(),
                "extracted_bytes": 0,
                "database_sha256": hashlib.sha256(b"").hexdigest(),
                "gzip_crc_verified": False,
            }
        for key, maximum in (
            ("downloaded_bytes", spec.compressed_bytes),
            ("extracted_bytes", spec.database_bytes),
        ):
            require(
                type(self.state.get(key)) is int and 0 <= self.state[key] <= maximum,
                "Contador do checkpoint inválido; nada será reinicializado.",
            )

    def close(self):
        self.session.close()

    def check_budget(self):
        if self.monotonic() >= self.deadline:
            raise BudgetExpired

    def save(self, **values):
        self.state.update(values, updated_at=utc_now())
        self.state["download_percent"] = round(
            100 * self.state["downloaded_bytes"] / self.spec.compressed_bytes, 2
        )
        self.state["extraction_percent"] = round(
            100 * self.state["extracted_bytes"] / self.spec.database_bytes, 2
        )
        save_json(self.files["state"], self.state)
        if self.monotonic() - self.last_print >= 10 or values.get("status") in {
            "ready",
            "stopped",
            "failed",
            "downloaded",
        }:
            print(json.dumps(self.state, ensure_ascii=False), flush=True)
            self.last_print = self.monotonic()

    def free_space(self, needed=0):
        free = self.disk_usage(self.destination).free
        require(
            free >= needed + self.reserve_bytes,
            f"Espaço insuficiente: livres={free} bytes; necessários com reserva={needed + self.reserve_bytes} bytes.",
        )
        return free

    def wait(self, seconds):
        end = self.monotonic() + seconds
        while self.monotonic() < end:
            self.check_budget()
            self.sleeper(min(5, end - self.monotonic()))

    def remote_identity(self):
        """HEAD não baixa o banco; ETag multipart não é apresentado como SHA-256."""
        for attempt in range(self.max_retries + 1):
            self.check_budget()
            try:
                with self.session.head(
                    self.spec.url, timeout=(20, 60), allow_redirects=False
                ) as response:
                    if response.status_code in {408, 429, 500, 502, 503, 504}:
                        raise RetryableHTTP(
                            response.status_code,
                            retry_after_seconds(response.headers.get("Retry-After"), time.time()),
                        )
                    require(
                        response.status_code == 200,
                        "HEAD não confirmou o arquivo oficial; revisar sem seguir redirecionamento.",
                    )
                    self.check_headers(response.headers)
                    require(
                        int(response.headers.get("Content-Length", -1))
                        == self.spec.compressed_bytes,
                        "Tamanho remoto mudou; retomada bloqueada.",
                    )
                    return
            except (requests.RequestException, RetryableHTTP) as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(
                        "Falha técnica ao verificar origem; repita o comando depois."
                    ) from None
                self.save(
                    status="waiting_retry", retry_number=attempt + 1, error_type=type(exc).__name__
                )
                self.wait(max(min(60, 2**attempt), getattr(exc, "delay", 0)))

    def check_headers(self, headers):
        require(
            headers.get("ETag", "").strip('"') == self.spec.etag,
            "ETag remoto mudou/ausente; não misturar versões do arquivo.",
        )
        require(
            headers.get("Content-Encoding", "identity").lower() == "identity",
            "Codificação HTTP inesperada; interrompido para não alterar os bytes.",
        )

    def recover_prefix(self, name, count_key, hash_key):
        """Verifica prefixo confirmado; só descarta cauda não confirmada do nosso .part."""
        final, partial = self.files[name], self.files[name + "_part"]
        count = int(self.state[count_key])
        require(
            not (final.exists() and partial.exists()),
            "Arquivo final e parcial coexistem; revisar sem sobrescrever.",
        )
        current = final if final.exists() else partial
        if not current.exists():
            require(count == 0, "Arquivo do checkpoint ausente; não reinicializar silenciosamente.")
            return hashlib.sha256()
        require(
            current.stat().st_size >= count,
            "Arquivo menor que o checkpoint; integridade não confirmada.",
        )
        self.save(status="verifying_saved_prefix", verifying=name, verified_prefix_bytes=0)
        digest = hashlib.sha256()
        with current.open("rb") as handle:
            read = 0
            while read < count:
                self.check_budget()
                block = handle.read(min(CHUNK, count - read))
                require(bool(block), "Prefixo incompleto.")
                digest.update(block)
                read += len(block)
                if self.monotonic() - self.last_print >= 10:
                    self.save(verified_prefix_bytes=read)
        require(
            digest.hexdigest() == self.state[hash_key],
            "SHA-256 local divergiu; preservar o arquivo para revisão.",
        )
        if current.stat().st_size > count:
            require(current == partial, "Arquivo final inesperado; nunca truncar arquivo final.")
            with partial.open("r+b") as handle:
                handle.truncate(count)
                handle.flush()
                os.fsync(handle.fileno())
            self.save(recovered_uncommitted_tail=True)
        return digest

    def checkpoint_write(self, handle, block, digest, count_key, hash_key, status):
        self.check_budget()
        self.free_space(len(block))
        handle.write(block)
        handle.flush()
        os.fsync(handle.fileno())
        digest.update(block)
        self.save(
            **{
                count_key: self.state[count_key] + len(block),
                hash_key: digest.hexdigest(),
                "status": status,
            }
        )

    def finish(self, name, count_key, expected):
        require(self.state[count_key] == expected, "Quantidade final de bytes divergente.")
        final, partial = self.files[name], self.files[name + "_part"]
        if not final.exists():
            require(
                partial.is_file() and partial.stat().st_size == expected,
                "Arquivo parcial incompleto.",
            )
            partial.rename(final)
        require(final.stat().st_size == expected, "Arquivo final com tamanho inesperado.")

    def download(self):
        self.remote_identity()
        digest = self.recover_prefix("archive", "downloaded_bytes", "download_sha256")
        target = self.spec.compressed_bytes
        require(
            self.state["downloaded_bytes"] <= target, "Checkpoint maior que o arquivo esperado."
        )
        self.free_space(target - self.state["downloaded_bytes"])
        retries = 0
        while self.state["downloaded_bytes"] < target:
            self.check_budget()
            offset = self.state["downloaded_bytes"]
            headers = {"Range": f"bytes={offset}-{target - 1}", "If-Match": f'"{self.spec.etag}"'}
            try:
                with self.session.get(
                    self.spec.url,
                    headers=headers,
                    stream=True,
                    timeout=(20, 60),
                    allow_redirects=False,
                ) as response:
                    if response.status_code in {408, 429, 500, 502, 503, 504}:
                        raise RetryableHTTP(
                            response.status_code,
                            retry_after_seconds(response.headers.get("Retry-After"), time.time()),
                        )
                    self.check_headers(response.headers)
                    if response.status_code == 206:
                        match = re.fullmatch(
                            r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", "")
                        )
                        require(match is not None, "Content-Range ausente/inválido.")
                        start, end, total = map(int, match.groups())
                        require(
                            start == offset and total == target and offset <= end < target,
                            "Range remoto divergiu; não anexar bytes.",
                        )
                    else:
                        require(
                            response.status_code == 200 and offset == 0,
                            "Servidor não respeitou a retomada; parcial preservado.",
                        )
                        end = target - 1
                    require(
                        int(response.headers.get("Content-Length", -1)) == end - offset + 1,
                        "Content-Length incompatível com o trecho esperado.",
                    )
                    self.save(status="downloading", retry_number=retries)
                    with self.files["archive_part"].open("ab") as output:
                        for block in response.iter_content(chunk_size=CHUNK):
                            if not block:
                                continue
                            require(
                                self.state["downloaded_bytes"] + len(block) <= end + 1,
                                "Resposta excede o trecho autorizado.",
                            )
                            self.checkpoint_write(
                                output,
                                block,
                                digest,
                                "downloaded_bytes",
                                "download_sha256",
                                "downloading",
                            )
                    if self.state["downloaded_bytes"] != end + 1:
                        raise requests.ConnectionError("Resposta terminou antes do fim esperado")
            except (requests.RequestException, RetryableHTTP) as exc:
                if retries >= self.max_retries:
                    raise RuntimeError(
                        "Tentativas de download esgotadas; parcial preservado para retomada manual."
                    ) from None
                retries += 1
                self.save(
                    status="waiting_retry", retry_number=retries, error_type=type(exc).__name__
                )
                self.wait(max(min(60, 2 ** (retries - 1)), getattr(exc, "delay", 0)))
        self.finish("archive", "downloaded_bytes", target)
        self.save(status="downloaded", downloaded_complete=True)

    def extract(self):
        require(
            self.files["archive"].is_file()
            and self.state["downloaded_bytes"] == self.spec.compressed_bytes,
            "Complete primeiro o download.",
        )
        self.recover_prefix("archive", "downloaded_bytes", "download_sha256")
        self.recover_prefix("database", "extracted_bytes", "database_sha256")
        target = self.spec.database_bytes
        require(
            self.state["extracted_bytes"] <= target,
            "Checkpoint extraído excede o tamanho esperado.",
        )
        if self.files["database"].exists():
            require(
                self.state["gzip_crc_verified"] and self.state["extracted_bytes"] == target,
                "Banco final sem verificação gzip registrada.",
            )
            return
        self.free_space(target - self.state["extracted_bytes"])
        digest = hashlib.sha256()
        confirmed = int(self.state["extracted_bytes"])
        self.save(status="extracting_rechecking_prefix", extraction_prefix_checked_bytes=0)
        with gzip.open(self.files["archive"], "rb") as source:
            read = 0
            while read < confirmed:
                self.check_budget()
                block = source.read(min(CHUNK, confirmed - read))
                require(bool(block), "Gzip terminou antes do prefixo salvo.")
                digest.update(block)
                read += len(block)
                if self.monotonic() - self.last_print >= 10:
                    self.save(extraction_prefix_checked_bytes=read)
            require(
                digest.hexdigest() == self.state["database_sha256"],
                "Prefixo descompactado diverge do checkpoint.",
            )
            self.save(status="extracting")
            with self.files["database_part"].open("ab") as output:
                while True:
                    self.check_budget()
                    block = source.read(CHUNK)
                    if not block:  # gzip valida CRC/trailer ao chegar ao fim.
                        break
                    require(
                        self.state["extracted_bytes"] + len(block) <= target,
                        "Gzip excede o tamanho fixado; interrompido.",
                    )
                    self.checkpoint_write(
                        output, block, digest, "extracted_bytes", "database_sha256", "extracting"
                    )
        require(
            self.state["extracted_bytes"] == target,
            "Tamanho descompactado diverge do cabeçalho verificado.",
        )
        self.save(gzip_crc_verified=True)
        self.finish("database", "extracted_bytes", target)

    def validate_sqlite(self):
        path = self.files["database"]
        self.save(status="checking_sqlite")
        with path.open("rb") as handle:
            header = handle.read(100)
        require(
            len(header) == 100 and header[:16] == b"SQLite format 3\x00",
            "Cabeçalho SQLite inválido.",
        )
        page = struct.unpack(">H", header[16:18])[0]
        page = 65536 if page == 1 else page
        count = struct.unpack(">I", header[28:32])[0]
        require(
            header[24:28] == header[92:96] and count > 0,
            "Contagem de páginas do cabeçalho não confirmada.",
        )
        require(
            page * count == self.spec.database_bytes == path.stat().st_size,
            "Tamanho/paginação SQLite divergente.",
        )

        def heartbeat():
            if self.monotonic() >= self.deadline:
                return 1
            if self.monotonic() - self.last_print >= 10:
                self.save(status="checking_sqlite")
            return 0

        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        ) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA cache_size=-65536")
            db.set_progress_handler(heartbeat, 100000)
            try:
                require(
                    db.execute("PRAGMA quick_check").fetchall() == [("ok",)],
                    "SQLite quick_check não retornou ok.",
                )
                tables = {
                    r[0] for r in db.execute("SELECT name FROM sqlite_schema WHERE type='table'")
                }
                require(
                    {"tracks", "lyrics"} <= tables,
                    "Schema LRCLIB esperado ausente; revisão necessária.",
                )
                schema = {
                    name: [r[1] for r in db.execute(f"PRAGMA table_info({name})")]
                    for name in ("tracks", "lyrics")
                }
            except sqlite3.OperationalError:
                self.check_budget()
                raise
        self.save(
            status="ready",
            sqlite_quick_check="ok",
            schema_columns=schema,
            database_path=str(path),
            publisher_sha256_available=False,
        )


def run(destination, action="prepare", *, spec=OFFICIAL_DUMP, **kwargs):
    require(action in {"prepare", "download", "extract"}, "Ação inválida.")
    with exclusive(destination):
        transfer = Transfer(destination, spec, **kwargs)
        try:
            # Reserva também a extração, antes de iniciar o download completo.
            need_download = (
                max(0, spec.compressed_bytes - transfer.state["downloaded_bytes"])
                if action != "extract"
                else 0
            )
            need_extract = (
                max(0, spec.database_bytes - transfer.state["extracted_bytes"])
                if action != "download"
                else 0
            )
            transfer.free_space(need_download + need_extract)
            transfer.save(status="preflight", action=action)
            if action in {"prepare", "download"}:
                transfer.download()
            if action in {"prepare", "extract"}:
                transfer.extract()
                transfer.validate_sqlite()
            return 0
        except KeyboardInterrupt as exc:
            transfer.save(
                status="stopped",
                reason="time_budget_reached"
                if isinstance(exc, BudgetExpired)
                else "interrupted_resume_same_command",
            )
            return 2
        except Exception as exc:
            transfer.save(
                status="failed",
                error_type=type(exc).__name__,
                reason=str(exc)
                if not isinstance(exc, requests.RequestException)
                else "network_failure",
            )
            return 1
        finally:
            transfer.close()


def cli():
    parser = argparse.ArgumentParser(
        description="Prepara o dump oficial no SSD; não altera nem executa a coleta de músicas."
    )
    parser.add_argument("--dest", type=validate_destination, default=DEFAULT_DESTINATION)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--prepare", action="store_true", help="Baixa, extrai e verifica o banco.")
    modes.add_argument("--download-only", action="store_true")
    modes.add_argument("--extract-only", action="store_true")
    modes.add_argument(
        "--status", action="store_true", help="Somente lê o progresso salvo; sem rede."
    )
    parser.add_argument("--max-hours", type=float, default=48)
    parser.add_argument("--max-retries", type=int, default=5)
    args = parser.parse_args()
    if not math.isfinite(args.max_hours) or args.max_hours <= 0 or args.max_retries < 0:
        parser.error("Limites de execução inválidos.")
    destination = validate_destination(str(args.dest))
    if args.status:
        print(
            json.dumps(
                load_json(paths(destination, OFFICIAL_DUMP)["state"]) or {"status": "not_started"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    action = "download" if args.download_only else "extract" if args.extract_only else "prepare"
    return run(destination, action, max_hours=args.max_hours, max_retries=args.max_retries)
