# Busca local de letras — script 06

Esta etapa consulta o snapshot LRCLIB já validado no SSD. Não acessa a internet, não gera embeddings, não escolhe outro encoder e não treina modelos. Execute os comandos manualmente. Nenhuma dependência adicional é necessária no ambiente atual.

## Entrada → operação → saída

| Comando | Entrada | Operação | Saída |
|---|---|---|---|
| `--prepare-index` | Checkpoint do script 01 e dump pronto do script 05 | Copia o checkpoint para um workspace novo; percorre somente metadados do catálogo e cria índice normalizado separado | `D:\TCC_LRCLIB\tcc_lookup_v1\lookup.sqlite`, progresso do índice e novo `state.sqlite` privado |
| `--limit 50` | Índice completo e consultas pendentes | Busca candidatos, lê suas letras e aplica regras existentes | Até 50 resultados, caches privados, contagens e velocidade medida |
| `--all` | Mesmas entradas | Percorre todas as pendências locais, em ordem de `query_id` | Mesmas saídas incrementais; sem limite de coorte |
| `--status` | Checkpoints | Somente leitura das contagens | Resumo no terminal, sem letras |

O dump original é aberto em `mode=ro&immutable=1`. A execução não cria índices nem faz alterações nele. O índice auxiliar contém apenas metadados dos artistas presentes no manifesto: identificador LRCLIB, artista/título originais e normalizados, álbum, duração e referência à letra. Os campos originais são preservados.

## 1. Execute primeiro: preparar o índice

Mantenha o SSD conectado como D:, o computador acordado e os scripts de coleta 02/04 encerrados.

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --prepare-index
$LASTEXITCODE
```

Essa preparação inicial pode demorar: percorre a tabela de metadados do catálogo uma única vez. Não varre todas as letras nem repete o `quick_check` do banco de 262 GB. Usa lotes de 5.000 registros com checkpoint transacional. As contagens `scanned` e `indexed` significam, respectivamente, registros do catálogo examinados e metadados guardados para os artistas do universo. **Não são quantidades de letras aceitas.** Ao concluir: `stage: index_ready`, `complete: true`, código `0`.

O índice extra existe porque a igualdade de nomes em minúsculas do LRCLIB não reproduz a normalização conservadora do projeto (acentos, pontuação e título-base). Usar apenas a primeira correspondência poderia ocultar versões e candidatos conflitantes. A preparação local não limita o universo a 2.000 ou 15.000 músicas.

É exigida uma reserva de 5 GiB livres, tanto no volume do workspace quanto durante a construção do índice. O tamanho final do índice e a velocidade em dados reais ainda precisam ser medidos.

## 2. Lote pequeno: 50 consultas

Somente depois do índice completo:

```powershell
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --limit 50
$LASTEXITCODE
```

Traga o resumo final e o código de saída antes da execução completa. `queries_per_second` mede este lote; não inclui a preparação do índice nem o carregamento inicial. Não prometemos cobertura ou velocidade antes dessa medição.

## 3. Todas as pendências, retomada e erros

```powershell
# Após conferir o lote pequeno: todas as pendências locais.
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --all
$LASTEXITCODE

# Progresso: pode executar em outro terminal, sem iniciar outro trabalhador.
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --status

# Depois de corrigir a causa: retentar até 50 erros técnicos locais.
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --retry-errors --limit 50
$LASTEXITCODE
```

Para retomar, repita o comando que estava executando (`--prepare-index`, `--limit 50` ou `--all`). Resultados concluídos são pulados. `--limit 50` sempre significa até 50 pendências nesta invocação, não completar um lote histórico de 50. Ctrl+C mantém as transações concluídas; após reinicialização, a consulta em andamento pode ser retomada, inclusive pelo cache já gravado. Não apague arquivos de lock ou checkpoints.

Cada consulta tem orçamento de 30 segundos, conferido entre leituras e pelo progress handler do SQLite; operações de I/O bloqueadas pelo sistema podem ultrapassar esse prazo. Um erro local interrompe o lote para revisão, conserva o resultado anterior e só é retentado explicitamente, até três tentativas por consulta. Não há loop de retentativa infinita.

Códigos: `0` = ação/lote concluído; `2` = interrupção ou erro local registrado que interrompeu o lote; `1` = falha de preparação/execução. Código `0` em um lote não significa cobertura total. Em `--status`, confira `local_pending`, `local_jobs`, `local_retryable_errors`, `local_exhausted_errors`, `status_counts` e `last_run.stop_reason`. O `updated_at` geral do status é a hora da consulta; **não prova que há processo ativo**. O horário da última execução fica em `last_run.updated_at`; o avanço do índice fica em `index.updated_at`.

## Preservação, regras e proveniência

- Origem preservada: `data/derived/private_manual_lyrics_v1/state.sqlite`.
- Workspace novo: `data/derived/private_local_lyrics_v1/state.sqlite`. Contém cópia consistente do manifesto, relação faixa–consulta–composição, splits e referências aos caches/vetores anteriores. Não modifica os modelos ou resultados científicos.
- Na primeira inicialização, congela-se uma cópia da coleta anterior. Mudanças posteriores na origem não são incorporadas automaticamente; não execute as duas rotas em paralelo.
- Aceitas, instrumentais e ambiguidades anteriores são preservadas. A fila local inclui não consultadas, erros, ausências anteriores e outras pendências não aceitas/não ambíguas. Não zera o limite de tentativas da API: os contadores locais são separados.
- A tabela `local_jobs` guarda status, resultado e referência ao cache anteriores para auditoria. A tabela `queries` guarda o resultado consolidado. `tracks` mantém o vínculo de todas as faixas e versões; não se presume que uma composição seja uma gravação ou uma letra idêntica.
- Caches novos: `data/derived/private_local_lyrics_v1/lrclib_cache_local/`. São privados e ignorados pelo Git. Caches históricos permanecem em suas pastas e são referenciados, sem duplicação ou exclusão. Não mova essas pastas enquanto forem usadas.
- O classificador reaproveita `reclassify_cached_composition`, `_candidate_diagnostics`, `conservative_normalize`, `pilot_base_title` e a equivalência estrita já implementados. Mantém compatibilidade de versão e tolerância de duração da configuração congelada (10 segundos); não usa popularidade, artista como proxy de sucesso nem seleção por erro.
- A enumeração local usa igualdade normalizada de artista e de título OU título-base. Verifica todos os candidatos desse conjunto, e não uma busca aproximada ou a primeira linha. O índice só pode ser usado após completar a varredura.
- Para cada registro LRCLIB, usa o ponteiro explícito `tracks.last_lyrics_id`, verificando `lyrics.track_id`. Versões históricas de edição da letra não são tratadas como músicas adicionais; o ID da revisão consultada é registrado. Ponteiro inconsistente vira erro, nunca ausência.
- **Diferença documentada em relação à API:** a barreira de 20 resultados deixa de se aplicar porque a enumeração do conjunto normalizado é completa no snapshot. As regras de aceitação não mudam. Se houver mais de 500 candidatos, mais de 2 milhões de caracteres em um candidato ou mais de 8 milhões no conjunto, o caso fica `ambiguous_local_incomplete`; nenhum subconjunto é aceito arbitrariamente.
- Letras conflitantes ficam ambíguas. Falta de texto simples não é convertida automaticamente em letra a partir de sincronização ou arquivos externos.
- `not_found` significa ausência no conjunto de metadados normalizados do snapshot fixado de 12/10/2026, não ausência universal nem resposta atual da API. Consultas por nomes alternativos não cobertos pela normalização ficam para outra etapa explicitamente documentada.
- O cache possui um adaptador com os nomes de campos antigos (`requests`, `/api/search`, códigos 200/404) para compatibilidade com o classificador e o leitor de letras. São **marcadores internos de compatibilidade**, não chamadas ou respostas HTTP reais: `transport: sqlite_readonly`, `http_requests: 0` e `legacy_adapter_status_codes_not_http: true` deixam isso explícito.
- O script exige o checkpoint `ready` do script 05 e o tamanho validado. Registra o SHA-256 já verificado, caminho, tamanho e horário de modificação do dump; não recalcula todo o hash a cada lote. Alteração posterior desses metadados, do universo de artistas ou do código bloqueia reutilização do índice.

O formato dos resultados aceitos é compatível com `read_accepted_text` da etapa de embeddings, verificado em teste sintético. **Não execute embeddings agora:** a escolha da rede será revisada depois, como combinado.

## Verificação desta entrega

Somente schema e nomes de índices do dump real foram inspecionados, em modo somente leitura. Não foram executados indexação, busca de letras reais, rede, embeddings ou treinamento. Testes usam SQLite e textos sintéticos e bloqueiam conexões de rede. Não houve commit ou push.

Comandos de verificação executados em 27/10/2026:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_local_lyrics.py tests/test_lrclib_dump.py tests/test_persistent_collection.py tests/test_manual_lyrics.py tests/test_lyrics_scale_v040.py tests/test_final_study_v040.py tests/test_lyrics_embeddings_v020.py tests/test_embeddings_scale_v040.py -p no:cacheprovider --basetemp=.tmp/pytest_local_regression
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/local_lyrics.py scripts/06_buscar_letras_local.py tests/test_local_lyrics.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/local_lyrics.py scripts/06_buscar_letras_local.py tests/test_local_lyrics.py
.\.venv\Scripts\python.exe scripts\06_buscar_letras_local.py --help
```

Resultados finais: **99 testes passaram em 13,17 segundos**, incluindo 21 testes novos; todos os quatro comandos acima encerraram com código **0**. Cobrem equivalência/conflito de letras, normalização, versões e duração, instrumental, referência à última revisão, limites conservadores, retomada da indexação e do cache, erros técnicos limitados, fonte somente leitura, alvo proibido, falta de espaço e preservação de faixas/splits. Ruff apontou uma questão de estilo durante o desenvolvimento, corrigida antes da verificação final.

`git check-ignore` confirmou que o novo SQLite e os caches estão ignorados; `git ls-files -- data/raw data/derived` mostrou apenas `data/raw/.gitkeep`. Os hashes de `manual_lyrics.py`, `manual_embeddings.py` e do `state.sqlite` original permaneceram idênticos aos capturados antes desta implementação. O código não cria nenhum processo em segundo plano.
