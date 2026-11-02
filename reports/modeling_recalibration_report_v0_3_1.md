# Recalibração dirigida da modelagem piloto — v0.3.1

## Escopo

Teste dirigido de regularização, dimensionalidade e contribuição residual das letras. Nenhum algoritmo foi escolhido retrospectivamente, nenhuma nova letra foi consultada e o holdout oficial não foi acessado.

## Reprodução da v0.3

Amostra: 1441 composições; chave: `artist_group_id`; folds: [289, 289, 287, 289, 287]; hash: `eb37c9d19dbc298b585991f55e75158b7a3a0e0aeab70a0c33c184450830f940`.
Baseline v0.3 reproduzido: MAE 7.392; histórico: 7.392; diferença 0.000. O Baseline com grade ampliada obteve MAE 7.158.

## Modelos principais

| Algoritmo | Bloco | Representação | MAE | RMSE | R² | Spearman | MAE treino | Gap | PCA LFM | PCA MiniLM |
|---|---|---|---|---|---|---|---|---|---|---|
| ridge | baseline | raw | 7.196 | 9.342 | 0.505 | 0.708 | 6.619 | 0.576 | — | — |
| ridge | traditional | raw | 7.755 | 10.106 | 0.421 | 0.677 | 5.946 | 1.809 | — | — |
| ridge | deep | raw | 9.358 | 12.031 | 0.179 | 0.429 | 8.224 | 1.133 | — | — |
| ridge | combined | raw | 9.160 | 11.840 | 0.205 | 0.461 | 8.075 | 1.084 | — | — |
| ridge | traditional | pca90 | 7.289 | 9.434 | 0.495 | 0.707 | 6.253 | 1.036 | 71.600 | — |
| ridge | deep | pca90 | 7.692 | 9.901 | 0.444 | 0.671 | 5.994 | 1.697 | — | 165.200 |
| ridge | combined | pca90 | 7.842 | 10.125 | 0.419 | 0.668 | 5.676 | 2.167 | 71.600 | 165.200 |
| elastic_net | baseline | raw | 7.158 | 9.288 | 0.511 | 0.712 | 6.647 | 0.510 | — | — |
| elastic_net | traditional | raw | 7.603 | 9.867 | 0.448 | 0.680 | 6.225 | 1.378 | — | — |
| elastic_net | deep | raw | 8.962 | 11.539 | 0.245 | 0.496 | 8.092 | 0.870 | — | — |
| elastic_net | combined | raw | 8.981 | 11.556 | 0.243 | 0.505 | 8.614 | 0.366 | — | — |
| elastic_net | traditional | pca90 | 7.233 | 9.350 | 0.504 | 0.711 | 6.296 | 0.936 | 71.600 | — |
| elastic_net | deep | pca90 | 7.609 | 9.784 | 0.457 | 0.677 | 6.043 | 1.566 | — | 165.200 |
| elastic_net | combined | pca90 | 7.709 | 9.966 | 0.437 | 0.675 | 5.743 | 1.966 | 71.600 | 165.200 |

## Modelos residuais

| Bloco corretor | MAE | RMSE | R² | Spearman | MAE treino cross-fit | Gap |
|---|---|---|---|---|---|---|
| traditional | 7.321 | 9.550 | 0.483 | 0.701 | 7.450 | -0.130 |
| deep | 7.372 | 9.626 | 0.474 | 0.699 | 7.492 | -0.121 |
| combined | 7.333 | 9.588 | 0.479 | 0.701 | 7.471 | -0.138 |

## Comparações contra Baseline/Elastic Net recalculado

Diferenças são candidato menos Baseline; valores negativos indicam melhora. IC95% por 2.000 bootstraps pareados e agrupados por artista.

| Modelo | Δ MAE | Δ MAE % | IC95% Δ MAE | Δ RMSE | IC95% Δ RMSE | Δ R² | Folds melhores | Overfit grave |
|---|---|---|---|---|---|---|---|---|
| elastic_net__combined__pca90 | 0.551 | 7.701 | [0.321, 0.767] | 0.678 | [0.406, 0.924] | -0.074 | 0 | True |
| elastic_net__combined__raw | 1.823 | 25.465 | [1.496, 2.137] | 2.268 | [1.890, 2.650] | -0.268 | 0 | False |
| elastic_net__deep__pca90 | 0.451 | 6.299 | [0.284, 0.623] | 0.496 | [0.320, 0.685] | -0.054 | 0 | False |
| elastic_net__deep__raw | 1.804 | 25.203 | [1.491, 2.127] | 2.251 | [1.885, 2.625] | -0.266 | 0 | False |
| elastic_net__traditional__pca90 | 0.075 | 1.045 | [-0.072, 0.235] | 0.062 | [-0.104, 0.235] | -0.007 | 1 | False |
| elastic_net__traditional__raw | 0.446 | 6.224 | [0.235, 0.658] | 0.579 | [0.345, 0.832] | -0.063 | 0 | False |
| residual_ridge__combined__pca90 | 0.175 | 2.445 | [0.041, 0.318] | 0.299 | [0.139, 0.470] | -0.032 | 1 | False |
| residual_ridge__deep__pca90 | 0.214 | 2.987 | [0.083, 0.355] | 0.338 | [0.176, 0.513] | -0.036 | 0 | False |
| residual_ridge__traditional__pca90 | 0.163 | 2.272 | [0.024, 0.310] | 0.262 | [0.106, 0.432] | -0.028 | 0 | False |
| ridge__baseline__raw | 0.038 | 0.531 | [0.001, 0.077] | 0.054 | [0.000, 0.117] | -0.006 | 1 | False |
| ridge__combined__pca90 | 0.684 | 9.559 | [0.436, 0.919] | 0.837 | [0.548, 1.116] | -0.092 | 0 | True |
| ridge__combined__raw | 2.002 | 27.971 | [1.651, 2.352] | 2.552 | [2.152, 2.967] | -0.306 | 0 | False |
| ridge__deep__pca90 | 0.534 | 7.458 | [0.339, 0.723] | 0.613 | [0.396, 0.858] | -0.067 | 0 | False |
| ridge__deep__raw | 2.200 | 30.735 | [1.854, 2.548] | 2.743 | [2.326, 3.149] | -0.332 | 0 | False |
| ridge__traditional__pca90 | 0.131 | 1.834 | [-0.031, 0.295] | 0.146 | [-0.040, 0.347] | -0.016 | 1 | False |
| ridge__traditional__raw | 0.597 | 8.337 | [0.371, 0.847] | 0.818 | [0.479, 1.183] | -0.090 | 0 | False |

## Hiperparâmetros e coeficientes

Parâmetros, seleção em borda, coeficientes não nulos e normas L2 por bloco/fold estão no CSV agregado e no run summary. A grade Ridge contém 15 valores de 0,0001 a 10.000; a Elastic Net contém 60 combinações.

## Casos não ingleses

Foram retirados apenas na reavaliação 20 casos; nenhum idioma entrou como preditor e nenhum modelo foi reescolhido.

## Regra de decisão

Classificação: **sem ganho incremental**. Exigência registrada: redução de pelo menos 2%, IC95% de ΔMAE inteiramente abaixo de zero, ausência de overfitting grave e melhora em pelo menos quatro folds.

## Limitações

Validação interna em 1.441 composições com letras aceitas; uma observação Spotify representante por composição; múltiplas configurações previamente definidas; resultados não causais e ainda sem confirmação no holdout.

## Privacidade e preservação

Predições, folds, matrizes e resultados individuais permanecem na área ignorada. Relatórios públicos contêm apenas agregados. Base, split, coorte, resultados de letras e embeddings foram preservados byte a byte.

## Verificação final

| Comando/verificação | Código | Resultado |
|---|---|---|
| python -m tcc_music_popularity.cli modeling-recalibration-v031 | 0 | execução completa; 1.049,5 s |
| python -m pytest -q | 0 | 92 testes aprovados |
| python -m pytest -q tests/test_modeling_recalibration_v031.py | 0 | 14 testes aprovados |
| python -m ruff check src tests | 0 | aprovado |
| python -m ruff format --check . | 0 | 82 arquivos formatados |
| git diff --check | 0 | aprovado |
| auditoria de leakage e holdout | 0 | artista 0; composição 0; holdout 0 |
| auditoria OOF privada | 0 | 1.441 linhas; 19 séries completas; 0 não finitos |
| auditoria de privacidade pública | 0 | 0 violações; privados tracked/staged 0/0 |
| verificação de hashes congelados | 0 | base, split, coorte, letras, embeddings e cache preservados |
| git status --short | 0 | executado; recalibração permanece sem commit/push |

Status: **aprovado**. Privados tracked/staged: 0/0. Congelados preservados: True.
