# Protocolo revisado dos quatro modelos — Base v0.1.1

## Escopo

Esta revisão apenas documenta decisões futuras de transformação. Nenhuma transformação foi executada, nenhum modelo foi treinado e o split 75%/25% permaneceu idêntico.

## Tratamento futuro das variáveis acústicas e metadados

- `key`: variável categórica nominal ou representação circular; a escolha será feita somente em `development_train`. É proibido tratá-la como contínua ordinal.
- `time_signature`: variável categórica; a codificação será ajustada somente em `development_train`.
- `mode`: variável binária, preservando a codificação 0/1.
- `genre`: variável categórica; a codificação será escolhida e ajustada somente em `development_train`.
- `year`: variável temporal; formas linear e não linear serão comparadas somente no treino.

## Semântica dos descritores revisados

- `lfm_compression_ratio`: semântica confirmada no extrator oficial; continua autorizada.
- `lfm_entropy`: semântica não confirmada; permanece fisicamente na Base v0.1.1 apenas para auditoria e foi removida das listas autorizadas de preditoras.

## Contagens autorizadas

- Baseline: **23** (sem alteração).
- Descritores tradicionais: **197 → 196**.
- Modelo tradicional atual: **220 → 219**.
- Modelo profundo atual: **23** (baseline; embeddings ainda não coletados).
- Modelo combinado atual: **220 → 219** antes de embeddings futuros.

## Comparabilidade e leakage

Todos os modelos futuros deverão usar os mesmos `track_id`, `artist_group_id`, `composition_group_id`, `split_group_id` e partições existentes. Seleção, imputação, codificação, padronização, forma funcional e tuning ocorrerão exclusivamente em `development_train`.
