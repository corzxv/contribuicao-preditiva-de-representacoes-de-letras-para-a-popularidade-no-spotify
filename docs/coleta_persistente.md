# Coleta persistente, sem perder o progresso

Esta é uma **entrada opcional 04**, que chama a coleta original e utiliza o mesmo banco privado. Os scripts 01/02/03, o matching, os splits e o selo anterior não foram modificados. Não é preciso preparar a base novamente, migrar o banco ou copiar os caches.

## Primeiro: teste limitado

Confirme que o terminal da coleta anterior já voltou ao prompt. Execute apenas uma coleta por vez; não rode 02, 03 e 04 simultaneamente.

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\04_coletar_persistente.py --limit 100 --max-restarts 0 --max-hours 2
$LASTEXITCODE
```

Este teste tenta até 100 consultas novas, mas **não reinicia automaticamente** se o circuit breaker disparar. Pode começar em `cooling_down` se ainda houver uma pausa pendente da última parada; isso é esperado. Traga o último JSON e o código de saída, sem enviar letras ou caches.

O JSON final inclui contagens, tentativas HTTP (`http_attempts`), códigos HTTP (`http_status_counts`), tempo acumulado nas chamadas (`http_elapsed_seconds`) e tempo total incluindo pausas (`elapsed_seconds`). Esses tempos não são uma previsão para o universo inteiro. A reutilização de conexões pode reduzir custos de conexão, mas **não há ganho de velocidade real medido nesta entrega**, nem garantia de resolver HTTP 503.

## Depois: continuar automaticamente

Após conferir o teste, execute:

```powershell
.\.venv\Scripts\python.exe scripts\04_coletar_persistente.py --all --retry-errors-after --max-restarts 48 --max-hours 192
```

- Primeiro percorre as consultas novas. Depois, com `--retry-errors-after`, trata os erros transitórios ainda elegíveis.
- Mantém o circuit breaker original. Quando ele dispara, salva o progresso, aguarda e retoma automaticamente: pausas de **30, 60 e até 120 minutos** após paradas sucessivas.
- Respeita `Retry-After` do servidor (segundos ou data HTTP) em respostas 429/503, inclusive se isso exigir uma espera maior.
- Mantém **até três ciclos por consulta** e até três tentativas por endpoint em cada ciclo. Não reabre ambiguidades, ausências ou tentativas esgotadas.
- Limites desta invocação: **48 retomadas automáticas** e **192 horas (8 dias)** incluindo pausas. São limites de execução, não previsão de duração. Erros de schema, arquivos alterados e erros inesperados não entram em repetição automática.
- Não faz requisições simultâneas: uma sessão HTTP reutiliza conexões sequencialmente, sem retentativas extras escondidas na biblioteca. Timeout de 20 segundos, intervalo mínimo, backoff e ambas as consultas `/api/get` e `/api/search` permanecem.
- Um reinício manual não apaga uma pausa pendente. As contagens de retomadas e o orçamento de horas são por invocação; os ciclos máximos de cada consulta permanecem registrados no banco.

O fluxo é persistente, mas não infinito. Se chegar aos limites, analise o resumo antes de executar novamente. `completed` significa que terminou o escopo elegível solicitado, **não** que todas as músicas têm letras: ambiguidades, ausências e erros esgotados continuam registrados.

## Acompanhar, interromper e retomar

Em outro terminal, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe scripts\04_coletar_persistente.py --status
```

- `current_counts`: contagens atuais, lidas do banco sem executar coleta.
- `supervisor`: último estado salvo, motivo e `next_retry_at` (horário com fuso UTC).
- `last_collection`: último checkpoint da coleta original; durante uma pausa, ele pode mostrar `stopped` enquanto o supervisor mostra `cooling_down`. Isso não é contradição.

O estado salvo, sozinho, não comprova que o processo continua vivo após queda de energia. Mantenha o terminal aberto e o computador ligado, sem suspensão. Para parar, Ctrl+C uma vez e aguarde o prompt. Para retomar, repita o comando 04 com os mesmos argumentos. Não apague arquivos nem rode 01 novamente.

Se quiser tratar **somente** erros transitórios, sem consultas novas:

```powershell
.\.venv\Scripts\python.exe scripts\04_coletar_persistente.py --all --retry-errors --max-restarts 48 --max-hours 192
```

Códigos de saída: `0` = escopo encerrado; `2` = parada controlada (limite, interrupção ou proteção sem retomada autorizada); outros códigos não zero = falha que exige revisão. Os comandos não iniciam embeddings ou treinamento.

## Preservação e implementação

A entrada reutiliza `manual_lyrics.collect`, `LRCLIBClient`, a validação original dos caches e a classificação V0.1.2, sem alterar seu código. Apenas injeta um transporte com `requests.Session`, uma conexão por vez, TLS verificado e `HTTPAdapter(max_retries=0)`. O suporte normal de proxy do ambiente é conservado. Redirecionamentos HTTP não são seguidos automaticamente; uma mudança do endpoint deve ser revisada, não mascarada.

Dependência: `requests` **2.34.2 já instalada no ambiente verificado**; nenhuma instalação ou atualização foi realizada. A nova entrada registra sua versão no protocolo privado e bloqueia mudança posterior não revisada.

Arquivos novos de execução ficam na mesma pasta privada `data/derived/private_manual_lyrics_v1`:

- `persistent_protocol.json`: selo do supervisor, versão da dependência e referência ao selo original; não substitui o selo existente.
- `persistent_progress.json`: estado, próximo horário permitido e contadores agregados.
- `persistent_supervisor_lock/`: bloqueio entre duas instâncias do 04, inclusive durante as pausas. O bloqueio original continua protegendo cada rodada de coleta.

O banco e os caches anteriores continuam como referência; não são reinicializados. O código não altera dados científicos, encoder, features, aceitação ou split. Todos os novos estados e caches permanecem ignorados pelo Git. Não houve commit/push, requisição LRCLIB ou execução na base real durante a implementação.

## Verificação offline

Os testes usam bancos temporários, respostas HTTP e relógios simulados. A rede real é bloqueada. Cobrem sessão reutilizada, ausência de retentativas ocultas, `Retry-After`, privacidade de erros, classificação original, retomada após cache salvo, pausas, limites de tempo/retomada, teto de três ciclos, selo preservado e bloqueio de supervisores concorrentes. Os testes anteriores de coleta e embeddings também são executados como regressão. Não foi feito benchmark de rede real: o lote limitado acima é necessário para medir o efeito nesta máquina e neste serviço.

Resultado em 25/10/2026: **61 testes aprovados, saída 0**:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_persistent_collection.py tests/test_manual_lyrics.py tests/test_lyrics_scale_v040.py tests/test_final_study_v040.py tests/test_lyrics_embeddings_v020.py tests/test_embeddings_scale_v040.py -p no:cacheprovider --basetemp=.tmp/pytest_persistent_d
```

Ruff, `ruff format --check` nos três arquivos Python novos e `04_coletar_persistente.py --help` retornaram 0. A comparação SHA-256 antes/depois confirmou que os scripts 01/02/03, os módulos `manual_lyrics.py`/`manual_embeddings.py` e o banco real `state.sqlite` permaneceram idênticos. Os novos caminhos de estado foram confirmados como ignorados; nenhum arquivo da pasta privada está rastreado pelo Git.
