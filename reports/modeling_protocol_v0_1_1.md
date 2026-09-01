# Protocolo dos quatro modelos — Base v0.1.1

## Objetivo

Estimar `spotify_popularity`, popularidade histórica observada no snapshot, fora da amostra dentro da população Spotify–LFM2b matched. Não serão feitas afirmações causais.

## Amostra, split e avaliação

- Os quatro modelos usarão a mesma amostra final comum e os mesmos `track_id`, grupos e splits.
- O holdout final é `holdout_test`, com 25.001342% das linhas nesta versão.
- Seleção de variáveis, imputação, padronização, PCA e tuning ocorrerão somente nos 75% de desenvolvimento.
- Validação cruzada posterior ficará restrita a `development_train` e respeitará `split_group_id`.
- Métricas principais: MAE, RMSE e R².
- Resultados também serão estratificados por período, gênero e faixa de popularidade.
- Diferenças de desempenho deverão incluir intervalos de incerteza.
- `DummyRegressor` será benchmark técnico, não quinto modelo científico.

## 1. Baseline

Metadados autorizados (`year`, `genre` e flags de versão Spotify) e 13 características acústicas. Features atuais após remoção de constantes: **23**.

## 2. Tradicional

Todas as features do baseline mais descritores tradicionais LFM2b não constantes. Features atuais: **220**.

## 3. Profundo

Baseline mais embeddings futuros das letras integrais. Letras e embeddings ainda não foram coletados; este modelo não pode ser treinado nesta etapa.

## 4. Combinado

Baseline, descritores tradicionais e embeddings futuros. Também permanece bloqueado até existir a amostra comum com embeddings.

## Regras de comparabilidade

Quando a amostra com letras/embeddings for formada, o split será recuperado por `track_id`/grupo. Os quatro modelos usarão somente observações comuns e exatamente os mesmos splits.
