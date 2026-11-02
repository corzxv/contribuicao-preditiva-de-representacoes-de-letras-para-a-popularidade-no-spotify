# Preparar o dump LRCLIB no SSD externo

Esta etapa **somente baixa, extrai e verifica** o banco oficial no SSD. Não busca músicas, não classifica matches, não gera embeddings e não altera os checkpoints existentes. O adaptador de consulta local será uma etapa posterior, após verificar o schema real. Não inicie os scripts 02/04 enquanto estiver preparando e validando esse novo caminho.

## Executar no PowerShell

Com o SSD conectado como **D:** e o computador sem suspensão:

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\05_preparar_dump_lrclib.py --dest "D:\TCC_LRCLIB" --prepare
$LASTEXITCODE
```

Esse comando cria a pasta exclusiva no SSD e executa download → extração → verificação. Não grava o dump no C:. Não exige instalação de biblioteca nova no ambiente atual (`requests` já está instalada).

O arquivo fixado é `lrclib-db-dump-20261012T090639Z.sqlite3.gz`, da [lista oficial de dumps](https://lrclib.net/db-dumps):

| Item | Bytes | GiB aproximados |
|---|---:|---:|
| Compactado | 47.837.763.733 | 44,55 |
| Banco SQLite descompactado | 261.755.867.136 | 243,78 |
| Ambos | 309.593.630.869 | 288,33 |
| Reserva mínima adicional exigida pelo script | 21.474.836.480 | 20 |

Na primeira execução, `--prepare` exige aproximadamente **308,33 GiB livres**. Na retomada, desconta os bytes já confirmados. A pasta não pode ser a raiz do disco nem ficar dentro do repositório. Nenhum arquivo pessoal é removido. O compactado é preservado após a extração.

## Progresso e retomada

Em outro terminal na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe scripts\05_preparar_dump_lrclib.py --dest "D:\TCC_LRCLIB" --status
```

`--status` somente lê o JSON salvo, sem internet. Os campos `download_percent` e `extraction_percent` indicam avanço em bytes. As etapas são:

- `downloading`: transferindo o arquivo compactado.
- `waiting_retry`: pausa após falha técnica, com tentativas limitadas.
- `verifying_saved_prefix`: conferindo o SHA-256 dos bytes já salvos; pode levar alguns minutos.
- `extracting_rechecking_prefix`: relendo o início do gzip para conferir uma extração interrompida.
- `extracting`: gravando o restante do banco descompactado.
- `checking_sqlite`: verificação de consistência; a extração pode estar em 100%, mas ainda não terminou esta conferência.
- **`ready`**: download, extração, CRC e `quick_check` concluídos.
- `stopped` / `failed`: veja `reason`; preserve os arquivos antes de retomar ou pedir revisão.

Para parar, pressione **Ctrl+C uma vez**, aguarde o prompt e só então desconecte o SSD. Para retomar, repita exatamente o comando `--prepare`. Não renomeie nem apague os arquivos parciais.

O download continua do prefixo confirmado, usando Range e o mesmo ETag. Se o servidor ignorar a retomada ou mudar o arquivo, o script bloqueia a operação sem anexar bytes incorretos. Falhas técnicas têm até cinco retentativas adicionais por fase HTTP, com backoff e respeito a `Retry-After`.

**A extração de gzip não tem retomada instantânea:** ela relê e descompacta o prefixo já concluído, verifica o hash e só então anexa o restante. Não baixa novamente o compactado. Isso custa tempo de leitura/CPU, mas evita reescrever o banco inteiro ou aceitar um prefixo corrompido.

Cada bloco gravado é sincronizado e confirmado no checkpoint. Após uma queda abrupta, somente uma eventual cauda ainda não confirmada do `.part`/`.extracting` pertencente a este script pode ser truncada, depois de verificar o prefixo. Arquivos finais nunca são truncados nem sobrescritos.

## Comandos opcionais

```powershell
# Somente download, deixando a extração para outro momento.
.\.venv\Scripts\python.exe scripts\05_preparar_dump_lrclib.py --dest "D:\TCC_LRCLIB" --download-only

# Extrair e verificar um download já concluído por este script; sem acesso à rede.
.\.venv\Scripts\python.exe scripts\05_preparar_dump_lrclib.py --dest "D:\TCC_LRCLIB" --extract-only
```

O limite padrão é de 48 horas por invocação; pode ser informado explicitamente com `--max-hours 48`. Códigos: `0` = ação solicitada concluída (`ready` apenas em prepare/extract); `2` = interrupção ou limite de tempo; `1` = falha que precisa ser conferida. Uma nova invocação recebe novo orçamento de tempo e preserva os arquivos salvos.

## Arquivos e integridade

Todos ficam em `D:\TCC_LRCLIB`, fora do Git:

- `lrclib-db-dump-20261012T090639Z.sqlite3.gz`: compactado oficial.
- O mesmo nome terminado em `.gz.part`: download ainda não concluído.
- `lrclib-db-dump-20261012T090639Z.sqlite3`: banco para futura consulta somente leitura.
- O mesmo nome terminado em `.sqlite3.extracting`: extração em andamento.
- `dump_progress.json`: origem fixada, contagens, hashes e resultados da verificação.
- `execution.lock` e arquivo `.tmp` do checkpoint: controle de execução; não representam consultas ou letras adicionais.

O script compara tamanho e ETag remoto com os metadados verificados do arquivo oficial e calcula SHA-256 local. O ETag multipart **não é um SHA-256 publicado**, e os metadados oficiais consultados não forneceram um checksum SHA-256 independente. A verificação local inclui CRC completo do gzip, tamanho/cabeçalho SQLite e `PRAGMA quick_check` em `mode=ro&immutable=1`. Isso detecta problemas de transporte/armazenamento e consistência, mas não equivale a uma assinatura digital do publicador.

Nenhuma letra é exibida. O schema consultado no fim contém apenas nomes de tabelas/colunas. O dump continua sendo um snapshot de 12/10/2026, não uma garantia de cobertura de todas as consultas da API atual.

## O que trazer de volta

Ao final, envie o código de saída e estes campos do JSON: `status`, `download_percent`, `extraction_percent`, `gzip_crc_verified`, `sqlite_quick_check` e `database_path`. Se houver falha, envie também `error_type` e `reason`, sem letras ou arquivos do banco.

A entrega foi testada com bancos SQLite pequenos e sintéticos, rede bloqueada, interrupções simuladas e arquivos temporários. Não foi executado o download real nem escrita no SSD pelo assistente. O tempo real de transferência, extração e validação ainda não foi medido.

## Verificações da implementação — 27/10/2026

Comandos executados na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_lrclib_dump.py tests/test_persistent_collection.py tests/test_manual_lyrics.py tests/test_lyrics_scale_v040.py tests/test_final_study_v040.py tests/test_lyrics_embeddings_v020.py tests/test_embeddings_scale_v040.py -p no:cacheprovider --basetemp=.tmp/pytest_dump_regression_c
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/lrclib_dump.py scripts/05_preparar_dump_lrclib.py tests/test_lrclib_dump.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/lrclib_dump.py scripts/05_preparar_dump_lrclib.py tests/test_lrclib_dump.py
```

Resultado final: **78 testes passaram em 11,89 segundos**, incluindo 17 testes do novo módulo; pytest, Ruff e formatação encerraram com código **0**. Os cenários incluem interrupção, retomada, Range ignorado, ETag alterado, corrupção, espaço insuficiente, limite de tempo e bloqueio transitório do checkpoint no Windows. Uma execução anterior da regressão apresentou `WinError 5` ao substituir um checkpoint sintético no módulo antigo de coleta persistente; a repetição completa passou sem modificar esse módulo. O novo módulo possui retentativa curta e testada para esse bloqueio transitório.

Os hashes SHA-256 de `manual_lyrics.py`, `manual_embeddings.py`, `persistent_collection.py` e do checkpoint real `data/derived/private_manual_lyrics_v1/state.sqlite` foram comparados antes/depois e permaneceram idênticos. Nenhuma coleta, embedding, treinamento, commit ou push foi executado nesta entrega. As alterações pessoais existentes foram preservadas.
