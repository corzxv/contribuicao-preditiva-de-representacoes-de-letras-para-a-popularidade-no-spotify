# Execução manual: descrição e regressões da coorte aceita

Leia o protocolo em [protocolo_coorte_aceita_v1.md](protocolo_coorte_aceita_v1.md).
O assistente preparou código e testes; não executou preparação, benchmark ou treinamento
na base real. Nenhuma dependência adicional: os scripts usam o ambiente do projeto
(Polars, NumPy, SciPy, scikit-learn, matplotlib, joblib e threadpoolctl).

## Primeiro comando: preparar e descrever

Cole somente as linhas de código, sem copiar o prefixo `PS C:\...>` do terminal.

```powershell
Set-Location "C:\Users\Concursos Felipe\Documents\UnB\TCC"
.\.venv\Scripts\python.exe scripts\09_descrever_coorte_letras.py --prepare --audit "data\derived\private_local_lyrics_audit\20261028T221245_413067Z"
$LASTEXITCODE
```

Entrada → índice auditado + metadados e splits + features autorizadas da V0.1.1.
Operação → verifica hashes, escolhe representantes aceitos sem alvo, materializa
somente desenvolvimento, cria componentes e folds, descreve dados.
Saída → `data/derived/private_statistical_cohort_v1/`:

- `summary.json`: quantidades e estágio final;
- `development.parquet`, `accepted_links.parquet`: matriz e rastreabilidade privadas;
- `folds.json`, `seal.json`: partições e hashes congelados;
- `dictionary.csv`, `coverage.csv`, `coverage_by_genre.csv`;
- `description/`: tabelas de ausências, quantis, categorias, correlações, relações
  por faixas das preditoras, distribuição da resposta e `leitura.md`.

Não há treinamento, rede, leitura de letras completas ou geração de embeddings aqui.
O primeiro script pode levar alguns minutos; mostra as etapas, não uma porcentagem
fictícia. Não se atribui distribuição normal/Poisson/beta automaticamente aos dados.

**Traga primeiro o JSON final e o código de saída.** Os campos decisivos são
`development_accepted_tracks`, `development_compositions`, `analysis_components`,
`collapsed_versions`, `holdout_targets_loaded` e `inputs_unchanged`. Confira também
`description/summary.json`. A contagem de composições será menor ou igual a 58.705,
não 78.323 para treino. O holdout permanece reservado.

Para ler os resumos:

```powershell
.\.venv\Scripts\python.exe scripts\09_descrever_coorte_letras.py --status
Get-Content "data\derived\private_statistical_cohort_v1\description\summary.json" -Raw
```

Se preparação for interrompida, ela não sobrescreve uma pasta parcial. Use um nome
novo e mantenha esse MESMO `--workspace` em todos os comandos seguintes:

```powershell
.\.venv\Scripts\python.exe scripts\09_descrever_coorte_letras.py --prepare --audit "data\derived\private_local_lyrics_audit\20261028T221245_413067Z" --workspace "data\derived\private_statistical_cohort_v1_tentativa2"
```

Não apague ou edite manualmente o selo para forçar uma retomada. Alertas de auditoria,
fontes alteradas, incompatibilidade de grupos ou alvos inválidos exigem revisão.

## Depois da leitura descritiva: benchmark técnico

```powershell
.\.venv\Scripts\python.exe scripts\10_modelar_baseline_tradicional.py --benchmark --threads 4
$LASTEXITCODE
```

Entrada → matriz e folds selados.
Operação → oito ajustes pequenos em grupos completos do treino do fold 0, sem
usar desempenho para escolher configurações. Nenhum ajuste de produção é substituído.
Saída → `benchmark.json`: tempo por família/bloco e avisos. Este comando JÁ treina
modelos técnicos locais temporários; execute somente quando quiser iniciar os ajustes.
Não extrapole cegamente o tempo de 3.000 para cerca de 58 mil linhas: custo não é linear.

## Rodada completa e retomada

Após saída 0 do benchmark e conferência da descrição:

```powershell
.\.venv\Scripts\python.exe scripts\10_modelar_baseline_tradicional.py --run --threads 4
$LASTEXITCODE
```

Entrada → mesmos dados, folds, protocolo e ambiente.
Operação → 480 ajustes internos planejados + 50 externos. Pode haver menos ajustes
internos se uma configuração falhar; falhas são registradas e não aceitas como sucesso.
Os dois blocos são executados sequencialmente, com a mesma validação. Evita disputar
CPU/memória com embeddings. Nenhum refit final de produção ou acesso ao alvo do holdout.
Saída → `models/`, `oof.parquet`, `metrics.csv`, `paired_comparisons.csv`,
`selected_parameters.csv`, `diagnostics/`, `results.md` e `verification.json`.

Para retomar depois de Ctrl+C ou reinício, use **o mesmo comando `--run`**. Checkpoints
completos são verificados e reutilizados; o ajuste externo incompleto é refeito.
Não abra dois treinamentos simultâneos no mesmo workspace. O bloqueio é liberado pelo
sistema quando o processo termina. Uma preparação real concluída não precisa ser repetida.

Em outro terminal, consultar progresso é seguro:

```powershell
.\.venv\Scripts\python.exe scripts\10_modelar_baseline_tradicional.py --status
```

O status mostra quantos dos 50 checkpoints terminaram, o modelo/fold atual e benchmark.
O timestamp registra início do ajuste, não é heartbeat: ficar igual durante um ajuste
não prova travamento. Para verificar depois, sem novos ajustes:

```powershell
.\.venv\Scripts\python.exe scripts\10_modelar_baseline_tradicional.py --verify --threads 4
$LASTEXITCODE
```

`--run` já faz reprodução ao terminar. `--verify` é útil após reinício ou para auditoria;
recarrega os 50 pipelines e confere as previsões com atol=1e-8 e rtol=1e-10.
Código 0 = concluído; 1 = erro/condição inválida; 2 = interrupção do treinamento pelo usuário.
Leia `$LASTEXITCODE` imediatamente após o comando relevante; status tem seu próprio código.

## Como interpretar e o que vem depois

As métricas antigas e novas não têm o mesmo denominador. Dentro desta rodada, compare
Baseline/Tradicional da mesma família e examine MAE, RMSE, R², P95, erros >20 e folds.
`selected_inner` avalia a seleção da família dentro do treino; não atribua sua diferença
entre blocos só aos descritores quando escolher famílias distintas.

Não declarar vencedor por menor MAE isolado. Os intervalos são exploratórios e
condicionados às previsões OOF; diagnóstico de resíduos não autoriza remover os casos
que o modelo errou. Nenhum script altera automaticamente grade ou protocolo com base
nos resultados. Se a análise justificar mudança, ela terá uma nova versão explícita.

Depois: preparar benchmark do encoder de embeddings e a geração retomável em nova
configuração. O script 03 existente NÃO foi convertido para E5 nesta entrega.
Preservar representantes e folds para comparar os quatro blocos na mesma amostra.
Não executar geração no checkpoint de coleta durante esta rodada: sua alteração
invalidaria a proveniência auditada. Não há necessidade de manter o SSD do dump ocupado
para estes scripts: são usados o índice auditado e os arquivos locais do projeto.

Nenhum dado, modelo ou previsão individual deve ir ao Git. Toda saída desta etapa
fica em `data/derived/`, já ignorada. Sem commit/push.

## Verificações efetivamente executadas pelo assistente

Em 28/10/2026, somente dados sintéticos e inspeção de documentação/metadados:

| Comando | Saída |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest tests/test_statistical_cohort.py tests/test_final_study_v040.py tests/test_local_lyrics_audit.py tests/test_statistical_revision_v080.py -p no:cacheprovider --basetemp=.tmp/pytest_statistical_cohort_v1_final` | 0; 48 testes passaram em 22,75 s |
| `.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/cohort_statistics.py src/tcc_music_popularity/cohort_regression.py tests/test_statistical_cohort.py scripts/09_descrever_coorte_letras.py scripts/10_modelar_baseline_tradicional.py` | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/cohort_statistics.py src/tcc_music_popularity/cohort_regression.py tests/test_statistical_cohort.py scripts/09_descrever_coorte_letras.py scripts/10_modelar_baseline_tradicional.py` | 0; cinco arquivos formatados |
| `.\.venv\Scripts\python.exe scripts/09_descrever_coorte_letras.py --help` | 0 |
| `.\.venv\Scripts\python.exe scripts/10_modelar_baseline_tradicional.py --help` | 0 |
| `git diff --check` | 0 |
| `git check-ignore data/derived/private_statistical_cohort_v1/development.parquet data/derived/private_statistical_cohort_v1/models/example.joblib data/derived/private_statistical_cohort_v1/oof.parquet` | 0; três caminhos ignorados |
| `.\.venv\Scripts\python.exe -m ruff check .` | 1; somente B018 preexistente em `exp_base.py:8`, preservado |

O teste integral gera dados inventados, prepara a coorte, executa grade reduzida de
teste, salva/recarrega 50 modelos de folds, reproduz previsões com diferença zero e
confere que a retomada não reajusta checkpoints completos. Outros testes verificam
ausências, categorias desconhecidas, imputação restrita ao treino, grupos transitivos,
folds internos, alvo fora de X, filtro do holdout, corrupção de checkpoints, alterações
de fonte, bootstrap pareado e equivalência da correlação otimizada ao Spearman exato.
A rede é bloqueada nos testes novos. A grade de produção tem teste de contagem (530).

Não foi criado o diretório da execução real. Não foram executados preparação,
descrição, benchmark ou ajustes sobre os dados reais. Resultados, desempenho, tempo
e convergência na coorte completa ainda precisam ser verificados pela execução manual.
`git ls-files` nos diretórios de dados retornou somente os três `.gitkeep`; o stage
permaneceu vazio. Alterações pessoais anteriores foram preservadas.
