# Letras e embeddings — execução manual

**Entrada opcional para retomada automática:** veja [Coleta persistente](coleta_persistente.md). O script 04 mantém os checkpoints dos scripts abaixo e acrescenta sessão HTTP reutilizada e pausas automáticas limitadas. Não execute 02 e 04 simultaneamente.

Não há coleta nem geração automática ao abrir os arquivos. Execute uma etapa por vez, no ambiente existente. Nenhuma dependência nova: são usadas as bibliotecas já previstas no projeto, inclusive o extra `embeddings`, além de SQLite da biblioteca padrão. O encoder deve estar no snapshot local já utilizado na V0.4; se estiver ausente, a etapa 03 para, sem baixar outro modelo.

## Comece aqui

No PowerShell, execute **somente a preparação primeiro**:

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\01_preparar_universo_letras.py
$LASTEXITCODE
```

Essa etapa pode demorar para ler os caches locais, mas não usa internet. Traga de volta o JSON agregado da última linha e o código de saída: `tracks`, `compositions`, `queries`, `accepted`, `ambiguous`, `not_found`, `technical_errors`, `not_queried`, `ineligible_tracks` e `history`. Não envie letras, caches, IDs ou vetores.

## Entrada → operação → saída

| Script | Entrada | Operação | Saída privada |
|---|---|---|---|
| `01_preparar_universo_letras.py` | Base integrada V0.1.1, split e matching congelados; caches e resultados anteriores | Projeta apenas metadados permitidos, inventaria todas as faixas, reconcilia caches e prepara consultas sem limite de coorte | `manifest.parquet`, `pending.parquet`, `track_mapping.parquet`, `preparation.json`, `state.sqlite` |
| `02_coletar_letras.py` | Consultas pendentes do manifesto | Consulta LRCLIB, aplica as regras existentes, salva cada tentativa e retoma pelo checkpoint | Caches novos em `lrclib_cache_manual/`, estado, manifesto, fila e `progress.json` atualizados |
| `03_gerar_embeddings.py` | Letras aceitas, vetores anteriores verificáveis e snapshot local congelado | Reutiliza vetores compatíveis; codifica somente o restante em trechos, sem treinamento | `vectors.parquet`, `embedding_index.parquet`, `embedding_export.json`, checkpoints e progresso |

Tudo fica em `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_manual_lyrics_v1`. Essa pasta é ignorada pelas regras existentes do Git; os comandos bloqueiam a execução se ela deixar de estar ignorada ou contiver arquivos rastreados. Os artefatos anteriores são apenas lidos.

## Comandos seguintes

Execute as linhas abaixo separadamente, conforme a etapa desejada. Não inicie dois trabalhos na mesma pasta simultaneamente.

```powershell
# Coleta: lote pequeno de até 100 consultas pendentes.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --limit 100

# Coleta: todas as consultas ainda não realizadas; respeita o circuit breaker.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --all

# Retomar após interrupção: repita o mesmo comando. Não existe flag --resume.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --all

# Retentar somente falhas técnicas transitórias, primeiro em lote pequeno.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --retry-errors --limit 100

# Alternativa: percorrer todas as falhas transitórias ainda dentro do limite.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --retry-errors --all

# Embeddings: conferir primeiro um lote de até 100 consultas aceitas.
.\.venv\Scripts\python.exe scripts\03_gerar_embeddings.py --limit 100 --batch-size 64 --checkpoint-every 32

# Embeddings: todas as aceitas pendentes; repetir este comando também retoma.
.\.venv\Scripts\python.exe scripts\03_gerar_embeddings.py --all --batch-size 64 --checkpoint-every 32

# Consultar contagens atuais, sem coletar nem gerar embeddings.
.\.venv\Scripts\python.exe scripts\02_coletar_letras.py --status

# Última etapa, motivo de parada e progresso registrado.
Get-Content "data\derived\private_manual_lyrics_v1\progress.json" -Raw | ConvertFrom-Json | Format-List

# Código do último comando Python executado: 0 = lote concluído; 2 = parada controlada.
$LASTEXITCODE
```

`--limit` conta consultas, não requisições HTTP, composições ou vetores únicos. Cada consulta pode representar várias faixas com metadados idênticos. `--batch-size` conta trechos por chamada ao encoder; `--checkpoint-every` conta consultas aceitas por transação. Pode diminuir ambos se faltar memória.

Um lote concluído não significa universo concluído. Confira as pendências e os erros; rejeições científicas, ambiguidades e ausências permanecem registradas. `unique_vectors` inclui o banco histórico importado, mesmo antes de todos os vínculos serem concluídos; `embedding_queries_completed` conta os vínculos já concluídos. O arquivo `embedding_export.json` informa os totais efetivamente exportados.

## Retomada e limites

- Use Ctrl+C uma vez e aguarde a gravação final. O estado SQLite é a referência: uma queda abrupta pode deixar os Parquets de consulta atrasados; a próxima execução os reconstrói.
- A coleta salva cada consulta. Os embeddings salvam cada checkpoint; somente um lote ainda não confirmado pode precisar ser recalculado. Não apague `state.sqlite`, seus arquivos auxiliares ou os caches para tentar retomar.
- Cada consulta tem no máximo **três ciclos manuais**. Cada endpoint mantém até três tentativas, timeout de 20 segundos, backoff inicial de 1 segundo e intervalo mínimo de 0,5 segundo, conforme a V0.4. Uma execução percorre a fila uma vez, sem tentar indefinidamente a mesma música.
- São preservadas as paradas existentes: dez erros técnicos consecutivos, mais de 20% de erros nas últimas 50 consultas de rede ou HTTP 429 persistente. Em uma parada, veja `stop_reason`, aguarde a recuperação do serviço e retome manualmente. Não há supervisor ou reinício automático.
- `--retry-errors` trata somente falhas transitórias, incluindo timeouts e HTTP 408/429/500/502/503/504; não reconsulta ambiguidades ou `not_found`. Também recupera uma consulta interrompida. Tentativas esgotadas e `schema_error` ficam para revisão, sem aceite forçado.
- Erro inesperado retorna código não zero. Ausência de arquivo, mudança dos dados/código congelados ou cache aceito alterado bloqueia a continuação. Preserve os arquivos e traga a mensagem, sem conteúdo de letras.

## Critérios preservados e decisões explícitas

**Universo e granularidade.** Usa a base integrada V0.1.1 inteira, não a coorte de 2.000/15.000 nem as cotas da V0.4. A leitura reutiliza `load_target_free_source`: popularidade Spotify e proxies de sucesso não são projetados. O split original permanece associado a cada faixa. Faixas sem chave operacional ou sem artista/título permanecem no mapeamento com motivo de inelegibilidade; nenhuma chave é inventada.

A escolha anterior de representante é marcada para auditoria, mas não limita esta fila. Uma consulta é identificada por composição operacional, split, artista, título completo, duração, álbum e flags de versão. IDs de faixas com consulta exatamente igual compartilham a consulta; versões ou durações diferentes não herdam o resultado só por terem a mesma composição. A chave operacional não identifica universalmente uma gravação ou uma letra.

**Histórico.** Procura recursivamente pastas `lrclib_cache*` em `data/raw`, `data/interim` e `data/derived`, além de resultados/reclassificações Parquet das execuções anteriores. Faz projeção fechada dos campos históricos, sem carregar alvo, texto tabular ou vetores na preparação. Caches são revalidados por consulta exata e classificados pelas regras V0.1.2 já usadas na V0.4: compatibilidade de artista, título, versão e duração (tolerância de 10 segundos quando comparável), unicidade/equivalência estrita dos candidatos e restrições de busca truncada.

Conflitos entre caches compatíveis com textos aceitos diferentes, ou contendo ambiguidade, recebem `ambiguous_history_conflict`; nenhum candidato é escolhido arbitrariamente. Um resultado antigo sem cache compatível verificável é evidência histórica, **não** aceite reutilizável: permanece pendente para consulta. `historical_status_counts` é um inventário por composição, não certificação de compatibilidade de todas as suas versões. Caches inválidos permanecem preservados e inventariados, sem serem interpretados como sucesso/ausência.

Para uma fonte fora das pastas reconhecidas, informe `--cache-dir "C:\caminho\cache"` ou `--results-file "C:\caminho\resultado.parquet"` ao script 01, antes da primeira preparação. Ambas aceitam repetição. Para incluir fontes depois da preparação, preserve a pasta atual e prepare outra com `--workspace data/derived/private_manual_lyrics_v2`; use esse mesmo argumento nos três scripts. Os caches novos da pasta anterior também serão descobertos.

**Embeddings.** Encoder `sentence-transformers/all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, CPU, float32, 384 dimensões. Reutiliza a normalização autorizada, a divisão em até 256 tokens incluindo especiais (254 de conteúdo), sobreposição de 32 tokens e a média ponderada por tokens novos, com L2 por trecho e no vetor final. Nenhum PCA, ajuste do encoder ou preditor é executado.

O banco histórico considera os vetores V0.2 e V0.4 de desenvolvimento/holdout apenas com manifesto/configuração compatíveis; verifica também os hashes de integridade disponíveis na V0.4. Fontes ausentes ou com configuração não confirmada não são reutilizadas. O vínculo atual exige texto aceito independentemente para aquela consulta, hash estrito do candidato, hash do texto normalizado, encoder/revision e configuração compatíveis. Compartilhar vetor por texto idêntico não declara composições ou gravações equivalentes. Dimensão, valores finitos, norma e integridade dos checkpoints são verificados.

O índice preserva `track_id`, composição, split, consulta e hashes do texto. `lyrics_sha256` é a chave estável; `vector_index` pode mudar numa exportação posterior. Use índice e vetores como par, conferindo seus hashes em `embedding_export.json`. Textos completos nunca são impressos; resultados individuais, caches e vetores permanecem privados. A ampliação não redefine o split nem torna o holdout uma nova avaliação independente.

## Funções existentes reaproveitadas

- `final_study_v040`: `load_target_free_source`, `select_representatives_without_target` (auditoria).
- `lyrics_pilot`: `LRCLIBClient`, `_version_flags`, `pilot_base_title`.
- `lyrics_scale_v040`: `cache_is_compatible`.
- `lyrics_pilot_v012` / `lyrics_pilot_v013`: `classify_cached_composition_v012`, `circuit_breaker_reason`.
- `lyrics_ambiguity_v011`: `deduplicate_candidates`, `strict_plain_text_metrics`.
- `lyrics_embeddings_v020`: `normalize_lyrics_text`, `_load_model`, `_set_determinism`, `_tokenize_audit_records`, `_encode_unique_records`, `build_embedding_frame` e hashes auxiliares.

A preparação inicial não foi executada na base real nesta entrega. As verificações usam apenas dados sintéticos, clientes/encoders simulados e ajuda da CLI; não houve novas requisições, embeddings reais ou treinamento neste fluxo.

## Verificação da entrega

Comando executado, com **46 testes aprovados e código de saída 0**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_manual_lyrics.py tests/test_lyrics_scale_v040.py tests/test_final_study_v040.py tests/test_lyrics_embeddings_v020.py tests/test_embeddings_scale_v040.py -p no:cacheprovider --basetemp=.tmp/pytest_manual_lyrics_b
```

Ruff e formatação foram verificados somente nos seis arquivos Python novos, com código 0. A ajuda `--help` dos três scripts também retornou 0, sem executar etapas. `git check-ignore` confirmou a proteção dos caminhos novos de estado, vetores e cache; `git ls-files` não encontrou arquivos rastreados nessa pasta. Alterações anteriores do repositório foram preservadas; não houve commit ou push.

Os testes cobrem projeção sem alvo, versões distintas, reconciliação histórica, limites e retomada inclusive na terceira tentativa, circuit breaker, exclusão mútua, configuração do encoder, integridade/dimensões/NaN dos vetores e associação a todas as faixas/splits sintéticos. Não substituem a primeira preparação offline nem um lote real executado por você.
