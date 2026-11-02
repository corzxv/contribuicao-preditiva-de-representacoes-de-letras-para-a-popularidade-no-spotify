# Revisão estatística exploratória V0.8

Esta rodada usa somente o desenvolvimento V0.5 e não altera os modelos ou a avaliação V0.6. Sua motivação é posterior à abertura do teste: OOF aninhada não a transforma em confirmação independente. A autoridade científica é o pedido específico V0.8 e seu protocolo selado, não a proposta anterior.

## Executar ou retomar no Windows

Na raiz do projeto, com o ambiente existente:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 prepare
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 benchmark
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 run
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 verify
```

`prepare` sela protocolo, código, entradas e inventário de preservação. `benchmark` executa os três ajustes técnicos predefinidos. Ambos recusam sobrescrever resultados existentes. Em uma retomada, usar `run`, que confere o selo e os hashes dos checkpoints antes de reutilizar folds concluídos; depois usar `verify`. Uma inconsistência interrompe a execução, sem apagar arquivos ou ampliar a grade.

Não há dependência nova, rede, coleta, processamento de letras ou recálculo de embeddings. Não executar módulos antigos de preparação/treinamento para retomar esta rodada. Os modelos V0.8 são pipelines de validação externa, não substitutos prontos para o demonstrador. Não foi ajustado modelo final no desenvolvimento completo.

## Proveniência e informação permitida

Entradas tabulares permitidas, todas no diretório privado de desenvolvimento V0.5:

- `development_matrix.parquet`: 7.648 representantes e somente os preditores autorizados, chaves, grupo e alvo de desenvolvimento.
- `fold_assignments.parquet`: cinco folds externos e três internos de cada treino externo, reutilizados sem novo sorteio.
- `oof_predictions.parquet`: somente quatro Elastic Net, Dummy e campos de alinhamento; Ridge não é referência nesta rodada.

As listas de informação e sua ordem vêm do manifesto V0.5: 23, 219, 407 e 603 inputs respectivamente. O alvo fica separado de X. As transformações são novas e ajustadas no treino pertinente; PCA90 separada para LFM2b/MiniLM. Caches em memória não cruzam conjuntos de treino. O protocolo e o resumo registram configurações completas, versões e SHA-256.

## Dicionário das saídas agregadas

`reports/revisao_estatistica_metricas_v0_8.csv`:

- `model`: família e bloco; `elastic_net__*` e `dummy__baseline` são referências V0.5, `spline_en__*` e `hist_gb__*` são novos pipelines.
- `scope`: `overall`, `fold`, `target_band`, `year_period` ou `version_flag`; `stratum` identifica o recorte e `fold` identifica a validação externa quando aplicável.
- `n`, `artists`: número de composições e grupos operacionais de artista no recorte. `small_group_n_lt30` identifica células pequenas, inclusive vazias.
- `mae`, `rmse`, `median_abs_error`, `p90_abs_error`, `p95_abs_error`: pontos da popularidade observada. Quantis com interpolação linear. `r2` existe somente no conjunto global e nos folds, não nos estratos estreitos.
- `prop_abs_le5`, `prop_abs_le10`, `prop_abs_le20`, `prop_abs_gt20`: frações entre 0 e 1; no Markdown são exibidas em porcentagem. Não significam probabilidade individual, sucesso comercial ou porcentagem de acerto.
- `n_abs_gt20`, `n_prediction_lt0`, `n_prediction_gt100`: contagens. Previsões fora da escala nominal não são cortadas.
- Campos `*_seconds`: tempos da execução V0.8; vazios para referências e estratos. Somar tempos das tarefas paralelas não equivale a tempo de parede.
- `warning_count`, `failed_configurations`: ocorrências de execução, não exclusões de músicas. Células vazias têm métricas vazias, não erro zero.

`reports/revisao_estatistica_comparacoes_v0_8.csv`:

- `comparison_kind=algorithm_vs_v05`: oito comparações com Elastic Net V0.5 do mesmo bloco.
- `comparison_kind=lyrics_within_family`: seis comparações textuais com Baseline da mesma família nova.
- `new_*`, `reference_*`, `delta_*`: estimativas agregadas e diferença novo menos referência. Deltas positivos de erro significam piora; delta de R² tem interpretação oposta.
- `mae_reduction_percent`: positivo indica melhora; `rmse_change_percent` e `p95_change_percent`: positivo indica piora.
- `folds_mae_improved`: número dos cinco folds com MAE estritamente menor.
- `operational_rule_met`: satisfaz a regra predefinida nessa comparação. `candidate_promising` só classifica candidato nas comparações com V0.5, não nas comparações incrementais.
- `mae_improved_but_tail_worse`: alerta para MAE menor acompanhado de P95 ou frequência >20 pior. O relatório também explicita eventuais trade-offs de RMSE.

O JSON público contém agregados, tempos, escolhas por fold, auditorias e hashes; o relatório Markdown os interpreta. Nenhum desses arquivos contém chaves de músicas ou vetores individuais de previsão.

## Saídas privadas e preservação

Somente `data/derived/private_statistical_revision_v0_8/` recebe dados/modelos novos:

- `seal.json`, `preservation_before.json`: selos e inventário privado.
- `benchmark.json`, `progress.json`, `run.json`, `verification.json`: execução e verificações.
- `tuning/`: todas as configurações internas, scores, warnings e falhas.
- `parts/`: 40 pipelines serializados, previsões dos folds, índices exatos dos treinos/validações e metadados com hashes. Carregar somente arquivos locais confiáveis; joblib não é formato seguro para arquivos de terceiros.
- `oof_predictions.parquet`: uma linha por composição, chaves de alinhamento, alvo de desenvolvimento, fold e oito colunas `prediction__{familia}__{bloco}`. Não publicar nem incluir no Git.

A auditoria preserva por SHA-256 arquivos públicos/pessoais anteriores, os modelos congelados V0.5 e as três entradas permitidas. Outros dados anteriores são conferidos por tamanho e `mtime_ns`, sem abrir holdout, letras ou caches. Essa distinção deve ser mantida: verificação por metadados não é alegação de recomputar todos os hashes de todas as bases.

O diretório privado é coberto pelo `.gitignore` já existente. CSVs agregados também continuam ignorados pela regra global anterior; isso não foi alterado nem houve inclusão forçada. Nenhum commit, push ou alteração de stage faz parte desta execução. Não publicar resultados individuais, metadados privados ou modelos junto ao relatório.

## Verificação da execução entregue

Execução integral: 1.200 ajustes internos, 40 externos e três ajustes técnicos adicionais; zero warnings e zero configurações malsucedidas. Tempo de execução principal: 958,0534661 segundos (15,97 minutos), sem incluir os testes e a verificação posterior.

Os estágios `prepare`, `benchmark`, `run` e `verify` encerraram com código **0**. As cinco referências OOF foram reproduzidas globalmente e por fold (30 conferências); a diferença máxima foi zero. Os 40 pipelines novos foram recarregados e suas previsões conferidas: diferença máxima zero, tolerância absoluta 1e-10 e relativa zero. As 7.648 linhas possuem oito previsões completas e finitas, com uma validação externa por linha.

Testes pertinentes executados, em diretório temporário novo cuja inexistência foi conferida antes:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_statistical_revision_v080.py tests/test_final_development_v050.py::test_separate_pca_and_imputation_fit_only_on_training_rows tests/test_final_development_v050.py::test_transformation_cache_refuses_different_train_sets -p no:cacheprovider --basetemp=.tmp/pytest_v080_c
```

Resultado: **26 passed in 6.29s**, código **0**. Para repetir, usar outro diretório temporário novo; não apagar resultados anteriores inadvertidamente.

```powershell
.\.venv\Scripts\python.exe -m ruff check src/tcc_music_popularity/statistical_revision_v080.py src/tcc_music_popularity/statistical_revision_report_v080.py tests/test_statistical_revision_v080.py
.\.venv\Scripts\python.exe -m ruff format --check src/tcc_music_popularity/statistical_revision_v080.py src/tcc_music_popularity/statistical_revision_report_v080.py tests/test_statistical_revision_v080.py
```

Resultados: **All checks passed**, **3 files already formatted**, ambos código **0**. A auditoria preservou 225 hashes e os metadados de 18.222 arquivos de dados antigos; HEAD/stage não mudaram. Zero dados/modelos privados rastreados. Não foi executada a suíte inteira: testes sem relação com esta rodada poderiam reabrir bases e alvos fora do escopo.

## Síntese dos resultados observados

Todos os oito novos pipelines reduziram o MAE em relação ao Elastic Net V0.5 do mesmo bloco, em cinco de cinco folds. Isso não basta para avançar pela regra predefinida:

- Splines: reduções de MAE entre 0,94% e 1,23%, inferiores ao limiar de 2%.
- Boosting Baseline: MAE 7,09399 → 6,90128 (−2,72%), mas P95 18,19456 → 18,75163 (+3,06%); erros >20 passaram de 284 para 319. Os demais blocos de boosting reduziram o MAE em menos de 2% e também aumentaram a frequência de erros >20.
- `absolute_error` foi selecionada em 15 dos 20 folds de boosting; `squared_error`, em cinco. Baseline: 5/0; Tradicional: 4/1; Profundo: 3/2; Combinado: 3/2, respectivamente.
- Letras dentro das famílias: Tradicional com spline reduziu MAE apenas 0,29% contra seu Baseline, em três de cinco folds, e aumentou P95. Os outros blocos textuais com spline e todos os blocos textuais do boosting tiveram MAE maior que o Baseline da própria família.

**Nenhum candidato satisfez integralmente a regra operacional.** Não promover automaticamente um modelo, reabrir o holdout ou alterar o demonstrador. Persistem as limitações de matching, disponibilidade/aceite de letras, cobertura de gêneros/idiomas, versões e semântica dos metadados. Há só 27 observações de desenvolvimento com popularidade ≥70 e nenhuma acima de 80. Trocar algoritmo não resolve essas limitações de cobertura. Os resultados são exploratórios, sem nova confirmação independente ou interpretação causal.
