# Análise residual com cross-fitting — v0.3.1

O Baseline fixo (`alpha=0.03`, `l1_ratio=0.8`) gerou predições cross-fitted no treino externo. Cada resíduo foi calculado para uma observação que não participou do ajuste que a predisse. Uma Ridge, ajustada sobre PCAs textuais dentro dos folds, estimou a correção somada ao Baseline na validação externa.

| Correção | MAE | RMSE | R² | Spearman | Gap | PCA LFM | PCA MiniLM |
|---|---|---|---|---|---|---|---|
| traditional | 7.321 | 9.550 | 0.483 | 0.701 | -0.130 | 71.600 | — |
| deep | 7.372 | 9.626 | 0.474 | 0.699 | -0.121 | — | 165.200 |
| combined | 7.333 | 9.588 | 0.479 | 0.701 | -0.138 | 71.600 | 165.200 |

Resíduos in-sample usados como alvo: 0. Resíduos da validação externa usados no treino: False.

Esta análise é secundária e não substitui os quatro blocos principais.
