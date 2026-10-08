# Modelagem piloto da popularidade musical — v0.3

## Escopo e interpretação

Validação interna preditiva de `spotify_popularity` (0–100), sem interpretação causal, sem acesso ao holdout oficial e sem treinamento de modelo final. A unidade é uma composição aceita na v0.2, representada por uma única observação Spotify. Isso evita múltiplas versões na matriz, mas limita a generalização para outras gravações da mesma composição.

## Universo comum

- Linhas/composições/embeddings: 1441 / 1441 / 1441.
- Artistas agrupadores: 1201.
- Holdout acessado: não; linhas fora de `development_train`: 0.
- Casos não ingleses: 20.

## Validação e pré-processamento

Cinco folds externos agrupados por `artist_group_id`, com três folds internos agrupados para tuning; seed 20261007. Os folds são idênticos entre blocos e algoritmos. Imputação, indicadores de ausência, one-hot encoding, padronização linear, `VarianceThreshold` e PCA foram ajustados exclusivamente no treino pertinente. Hash das atribuições: `eb37c9d19dbc298b585991f55e75158b7a3a0e0aeab70a0c33c184450830f940`.

Grade pré-definida: Elastic Net com `alpha` em [0.03, 0.3] e `l1_ratio` em [0.1, 0.8]; HistGradientBoosting com pares (`learning_rate`, `max_leaf_nodes`) (0.05, 15) e (0.1, 31), `max_iter=100`, `min_samples_leaf=20` e `l2_regularization=1`. Seleção interna por MAE.

## Auditoria dos folds

| Fold | n | Artistas | Alvo médio | Alvo mediano | Ano mín. | Ano med. | Ano máx. |
|---|---|---|---|---|---|---|---|
| 0 | 289 | 242 | 25.495 | 25.000 | 2000 | 2014.000 | 2022 |
| 1 | 289 | 239 | 25.578 | 24.000 | 2000 | 2014.000 | 2021 |
| 2 | 287 | 240 | 25.780 | 24.000 | 2000 | 2015.000 | 2021 |
| 3 | 289 | 239 | 25.702 | 24.000 | 2000 | 2014.000 | 2023 |
| 4 | 287 | 241 | 25.502 | 24.000 | 2000 | 2014.000 | 2020 |

## Referência ingênua

| Modelo | MAE | RMSE | R² | Spearman |
|---|---|---|---|---|
| DummyRegressor (média do treino) | 10.488 | 13.278 | -0.000 | -0.006 |

## Modelos principais — embeddings raw

### elastic_net

| Bloco | MAE | RMSE | R² | Spearman | MAE treino | Gap val−treino | Tempo (s) |
|---|---|---|---|---|---|---|---|
| baseline | 7.392 | 9.635 | 0.473 | 0.698 | 7.015 | 0.377 | 8.269 |
| traditional | 7.813 | 10.142 | 0.417 | 0.658 | 6.465 | 1.348 | 12.460 |
| deep | 9.031 | 11.691 | 0.225 | 0.483 | 8.173 | 0.857 | 15.013 |
| combined | 8.897 | 11.559 | 0.242 | 0.501 | 7.789 | 1.108 | 24.679 |

### hist_gradient_boosting

| Bloco | MAE | RMSE | R² | Spearman | MAE treino | Gap val−treino | Tempo (s) |
|---|---|---|---|---|---|---|---|
| baseline | 7.725 | 10.118 | 0.419 | 0.658 | 5.835 | 1.889 | 24.422 |
| traditional | 7.944 | 10.445 | 0.381 | 0.628 | 4.645 | 3.299 | 73.543 |
| deep | 8.118 | 10.667 | 0.355 | 0.607 | 4.072 | 4.045 | 106.384 |
| combined | 8.086 | 10.606 | 0.362 | 0.618 | 3.975 | 4.110 | 137.165 |

## Comparações pareadas

Diferenças são candidato menos referência; valores negativos de MAE/RMSE indicam melhora. IC95% por 2.000 reamostragens pareadas e agrupadas por artista.

| Algoritmo | Comparação | Δ MAE | Δ MAE % | IC95% Δ MAE | Δ RMSE | IC95% Δ RMSE | Δ R² |
|---|---|---|---|---|---|---|---|
| elastic_net | traditional vs baseline | 0.421 | 5.690 | [0.211, 0.636] | 0.507 | [0.266, 0.754] | -0.057 |
| elastic_net | deep vs baseline | 1.639 | 22.166 | [1.397, 1.909] | 2.056 | [1.748, 2.364] | -0.249 |
| elastic_net | combined vs baseline | 1.505 | 20.362 | [1.238, 1.762] | 1.924 | [1.631, 2.208] | -0.231 |
| elastic_net | deep vs traditional | 1.218 | 15.589 | [0.928, 1.534] | 1.549 | [1.193, 1.921] | -0.192 |
| elastic_net | combined vs traditional | 1.085 | 13.882 | [0.830, 1.328] | 1.417 | [1.110, 1.715] | -0.174 |
| elastic_net | combined vs deep | -0.133 | -1.477 | [-0.286, 0.027] | -0.132 | [-0.290, 0.036] | 0.017 |
| hist_gradient_boosting | traditional vs baseline | 0.219 | 2.841 | [0.035, 0.405] | 0.328 | [0.128, 0.537] | -0.038 |
| hist_gradient_boosting | deep vs baseline | 0.393 | 5.092 | [0.197, 0.585] | 0.549 | [0.339, 0.756] | -0.065 |
| hist_gradient_boosting | combined vs baseline | 0.361 | 4.679 | [0.159, 0.561] | 0.488 | [0.249, 0.712] | -0.057 |
| hist_gradient_boosting | deep vs traditional | 0.174 | 2.189 | [-0.009, 0.360] | 0.221 | [0.032, 0.413] | -0.026 |
| hist_gradient_boosting | combined vs traditional | 0.142 | 1.787 | [0.013, 0.271] | 0.161 | [0.011, 0.303] | -0.019 |
| hist_gradient_boosting | combined vs deep | -0.032 | -0.393 | [-0.182, 0.104] | -0.061 | [-0.217, 0.088] | 0.007 |

## Diagnósticos agregados da melhor configuração interna

A configuração de menor MAE OOF foi `elastic_net__baseline__raw`. As tabelas abaixo são diagnósticos posteriores, não critérios para reescolher o modelo. Células com menos de 30 observações foram suprimidas.

### Período

| Período | n | MAE | RMSE | R² | Spearman |
|---|---|---|---|---|---|
| 2000–2009 | 422 | 6.951 | 9.040 | 0.339 | 0.584 |
| 2010–2019 | 981 | 7.513 | 9.753 | 0.455 | 0.698 |
| 2020 ou posterior | 38 | 9.183 | 12.545 | 0.392 | 0.680 |

### Gênero (n ≥ 30)

| Gênero (n ≥ 30) | n | MAE | RMSE | R² | Spearman |
|---|---|---|---|---|---|
| acoustic | 39 | 6.504 | 8.275 | 0.174 | 0.334 |
| alt-rock | 73 | 6.497 | 9.003 | -0.044 | 0.378 |
| black-metal | 50 | 7.612 | 9.206 | -0.388 | 0.097 |
| blues | 40 | 6.209 | 7.759 | 0.228 | 0.534 |
| chill | 35 | 7.672 | 10.065 | 0.381 | 0.683 |
| country | 67 | 6.758 | 9.170 | 0.248 | 0.591 |
| dance | 43 | 8.873 | 12.177 | 0.328 | 0.716 |
| death-metal | 74 | 7.027 | 8.244 | -0.022 | 0.285 |
| emo | 92 | 6.115 | 8.006 | 0.384 | 0.610 |
| folk | 56 | 6.242 | 7.590 | 0.305 | 0.585 |
| funk | 31 | 7.927 | 9.878 | 0.066 | 0.359 |
| garage | 56 | 7.208 | 9.130 | 0.268 | 0.493 |
| goth | 33 | 7.952 | 9.131 | -0.262 | 0.128 |
| hard-rock | 47 | 5.860 | 7.452 | 0.203 | 0.495 |
| hardcore | 64 | 6.987 | 8.749 | -0.045 | 0.279 |
| hip-hop | 40 | 7.605 | 9.958 | 0.132 | 0.504 |
| indie-pop | 42 | 10.844 | 14.164 | 0.399 | 0.778 |
| power-pop | 30 | 7.139 | 8.844 | -0.550 | 0.307 |
| singer-songwriter | 33 | 5.362 | 6.632 | 0.122 | 0.440 |
| soul | 35 | 6.624 | 8.037 | 0.450 | 0.706 |

### Quintil observado

| Quintil observado | n | MAE | RMSE | R² | Spearman |
|---|---|---|---|---|---|
| 1 | 289 | 9.824 | 11.337 | -7.600 | 0.218 |
| 2 | 288 | 5.950 | 7.026 | -11.817 | 0.179 |
| 3 | 288 | 4.155 | 5.277 | -5.484 | 0.294 |
| 4 | 288 | 5.069 | 6.509 | -7.626 | 0.155 |
| 5 | 288 | 11.953 | 14.695 | -1.824 | 0.306 |

## Sensibilidade de idioma

As métricas foram recalculadas nas 1.421 observações classificadas como inglesas, retirando 20 casos não ingleses sem reajustar modelos, folds ou escolha de configuração.

| Modelo | MAE amostra completa | MAE só inglês | Δ após remoção | RMSE | R² | Spearman |
|---|---|---|---|---|---|---|
| elastic_net__baseline__raw | 7.392 | 7.390 | -0.003 | 9.635 | 0.475 | 0.699 |
| elastic_net__traditional__raw | 7.813 | 7.758 | -0.055 | 10.060 | 0.428 | 0.666 |
| elastic_net__deep__raw | 9.031 | 9.029 | -0.002 | 11.691 | 0.227 | 0.487 |
| elastic_net__combined__raw | 8.897 | 8.873 | -0.024 | 11.532 | 0.248 | 0.508 |
| hist_gradient_boosting__baseline__raw | 7.725 | 7.733 | 0.008 | 10.131 | 0.420 | 0.658 |
| hist_gradient_boosting__traditional__raw | 7.944 | 7.926 | -0.018 | 10.430 | 0.385 | 0.632 |
| hist_gradient_boosting__deep__raw | 8.118 | 8.123 | 0.005 | 10.672 | 0.356 | 0.609 |
| hist_gradient_boosting__combined__raw | 8.086 | 8.081 | -0.006 | 10.600 | 0.365 | 0.621 |

## Diagnóstico de overfitting

O campo `Gap val−treino` compara MAE de validação externa com MAE de treino após o tuning interno. Gaps positivos e grandes sugerem overfitting; não constituem teste formal. Parâmetros por fold e métricas por fold estão no CSV agregado.

## Limitações

Resultados restritos às 1.441 composições com letras aceitas, sujeitos a viés de seleção da disponibilidade de letras e à escolha de uma versão Spotify representante. O bootstrap reflete incerteza interna por artista, não incerteza de um holdout independente. A popularidade é a observada no snapshot e não mede causalidade nem sucesso futuro.

## Recomendação

**revisar os blocos de variáveis**. O baseline obteve o menor MAE OOF nos dois algoritmos; os blocos com letras não produziram ganho incremental nesta amostra. Antes de ampliar a coleta, convém revisar representação, regularização e redundância dos blocos de letras.

## Privacidade e preservação

Matriz, folds e predições individuais permanecem em área ignorada pelo Git. Relatórios e figuras contêm somente agregados. A Base v0.1.1 e o split congelado permaneceram byte a byte idênticos.

## Verificação final

| Comando/verificação | Código | Resultado |
|---|---|---|
| pytest -q (suíte completa) | 0 | 78 testes aprovados |
| pytest -q tests/test_modeling_pilot_v030.py | 0 | 10 testes específicos aprovados |
| ruff check src tests | 0 | All checks passed |
| ruff format --check . | 0 | 70 arquivos formatados |
| git diff --check | 0 | sem erros |
| hashes Base v0.1.1 e split | 0 | preservados byte a byte |
| auditoria dos 3 Parquets privados e OOF | 0 | 1441 linhas; 13 predições completas; holdout 0 |
| auditoria de leakage por artista/composição | 0 | sobreposições 0/0 |
| auditoria de privacidade pública e Git | 0 | marcadores proibidos 0; privado tracked/staged 0/0 |
| git status --short | 0 | resultados v0.3 não staged; nenhum commit/push após modelagem |

Status: **aprovado**. Arquivos privados tracked/staged: 0/0. Hashes congelados preservados: True.
