# Protocolo final de análise — v1.0

## Pergunta e interpretação

Avaliar se descritores tradicionais e embeddings das letras acrescentam capacidade preditiva à popularidade Spotify além de metadados e características acústicas. As conclusões serão preditivas e associativas, nunca causais.

## Unidade e resposta

Uma composição musical, representada por exatamente um `track_id` Spotify escolhido deterministicamente sem popularidade. A resposta é `spotify_popularity`, contínua entre 0 e 100. O alvo do holdout permanecerá selado até uma avaliação final única.

## Blocos congelados

1. Baseline: 23 variáveis permitidas, sem PCA.
2. Tradicional: Baseline + 196 descritores LFM2b; PCA de 90% somente no bloco LFM2b e ajustada no treino.
3. Profundo: Baseline + 384 dimensões MiniLM; PCA de 90% somente no MiniLM e ajustada no treino.
4. Combinado: Baseline + PCAs separadas de 90% para LFM2b e MiniLM, concatenadas após os ajustes no treino.

## Algoritmos e métricas

Elastic Net é o algoritmo primário, com a grade ampliada v0.3.1: alpha em {0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30} e l1_ratio em {0.05, 0.1, 0.25, 0.5, 0.8, 0.95}. Ridge é secundária, com alpha em {0.0001, 0.001, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000}. HistGradientBoosting não será modelo final principal. A análise residual fica restrita ao piloto/apêndice.

MAE é a métrica primária. RMSE, R² e Spearman são secundárias. Diferenças de MAE e RMSE serão avaliadas por bootstrap pareado agrupado por artista, conforme protocolo congelado antes da abertura do holdout.

## Holdout

O split permanece 75% `development_train` e 25% `holdout_test`. O holdout pode receber coleta e features congeladas, mas sua popularidade não será carregada, descrita, usada para ajuste, usada em métricas ou utilizada para decisões metodológicas. Os quatro modelos serão comparados na mesma amostra comum de composições com letras aceitas.
