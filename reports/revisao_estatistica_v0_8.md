# Revisão estatística exploratória — V0.8

## Síntese da rodada completa

Os oito pipelines novos reduziram o MAE frente ao Elastic Net V0.5 do mesmo bloco, em cinco de cinco folds. **Nenhum satisfez integralmente a regra operacional de avanço.** A melhor redução de MAE foi do boosting Baseline (2,72%), acompanhada de piora de P95 (3,06%) e aumento de erros >20 (284 → 319). Splines reduziram MAE entre 0,94% e 1,23%, abaixo dos 2% exigidos. Esses resultados não substituem a avaliação V0.6 nem o candidato congelado do demonstrador.

As letras tiveram contribuição incremental pequena no Tradicional com spline (−0,29% de MAE frente ao seu Baseline, somente três folds melhores e P95 maior). Nos demais blocos textuais com spline e em todos os blocos textuais do boosting, MAE foi maior que o Baseline da própria família. `absolute_error` foi selecionada em 15/20 folds do boosting; `squared_error`, em 5/20.

Verificações finais: **26 testes passaram**, Ruff e formatação aprovados; `prepare`, `benchmark`, `run` e `verify` encerraram com código **0**. As referências e os 40 pipelines recarregados reproduziram suas previsões com diferença máxima zero. Comandos completos e resultados estão em `run_summary_revisao_v0_8.json` e `docs/revisao_estatistica_v0_8.md`.

Rodada motivada pelo diagnóstico posterior ao teste V0.6. Não é confirmação independente. Foram usados exclusivamente 7.648 representantes do desenvolvimento, 3.749 grupos de artista e as mesmas atribuições dos cinco folds externos e três internos por treino. Nenhum holdout, previsão individual do holdout ou novo alvo foi carregado. A proposta científica antiga não foi usada.

## Protocolo e execução

Protocolo selado antes do teste técnico em 2026-10-15T17:46:19.450850+00:00. SHA-256: `75ed87336475bae2f7ba6f8a9141dd3fdd144bc6f63c4ba9cab9a53be5cb8c50`. Código, manifesto, três entradas e versões selados. OOF Elastic Net/Dummy reproduzidas globalmente e nos folds, com tolerância absoluta 1e-10 e relativa zero. Nenhum modelo V0.5 foi ajustado novamente. As fábricas de transformações criam objetos novos em cada treino; as PCAs permanecem separadas e explicam pelo menos 90% da variância de cada bloco no respectivo treino.

Spline altera somente year. Boosting recebe one-hot denso explícito, sem categorias nativas e sem informação nova. Seleção exclusivamente por MAE interno médio; os hiperparâmetros selecionados variam entre folds e não definem um novo modelo de produção. Não houve refit no desenvolvimento completo, clipping, calibração, pesos pelo alvo ou seleção de exemplos.

Execução: 1200 tentativas internas e 40 externas; 0 configurações malsucedidas; 0 warnings. Tempo somado dos 40 folds: 15.92 minutos. Tempo desta invocação, incluindo montagem das previsões: 15.97 minutos. Teste técnico adicional: três ajustes, sem selecionar por desempenho. Detalhes de tempo e todas as ocorrências estão no JSON; tarefas paralelas não somam tempo de parede.

## Métricas OOF globais

Erros em pontos da popularidade registrada; proporções nas tabelas abaixo são percentuais. MAE não representa intervalo individual nem porcentagem de acerto.

| Pipeline | MAE | RMSE | R² | Mediana \|e\| | P90 | P95 | ≤5 % | ≤10 % | ≤20 % | >20 % | n >20 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elastic_net__baseline | 7.0940 | 9.2138 | 0.5298 | 5.8596 | 14.3249 | 18.1946 | 43.6192 | 76.0068 | 96.2866 | 3.7134 | 284 |
| elastic_net__traditional | 7.0612 | 9.1883 | 0.5324 | 5.7894 | 14.4007 | 18.2594 | 44.2992 | 76.3337 | 96.4043 | 3.5957 | 275 |
| elastic_net__deep | 7.1625 | 9.2801 | 0.5230 | 5.8830 | 14.3652 | 18.4157 | 43.0962 | 74.9477 | 96.3389 | 3.6611 | 280 |
| elastic_net__combined | 7.1631 | 9.2955 | 0.5214 | 5.8159 | 14.5594 | 18.2470 | 43.8154 | 75.1831 | 96.2343 | 3.7657 | 288 |
| dummy__baseline | 10.7222 | 13.4364 | -0.0000 | 9.0059 | 21.9600 | 25.0387 | 27.9942 | 54.4195 | 87.3562 | 12.6438 | 967 |
| spline_en__baseline | 7.0069 | 9.1020 | 0.5411 | 5.7515 | 14.2328 | 18.1579 | 44.0377 | 76.4252 | 96.2866 | 3.7134 | 284 |
| spline_en__traditional | 6.9866 | 9.0929 | 0.5420 | 5.7860 | 14.2384 | 18.3204 | 44.8353 | 76.7782 | 96.4304 | 3.5696 | 273 |
| spline_en__deep | 7.0866 | 9.1811 | 0.5331 | 5.7937 | 14.3183 | 18.1719 | 43.7108 | 75.7191 | 96.3912 | 3.6088 | 276 |
| spline_en__combined | 7.0956 | 9.2051 | 0.5306 | 5.8059 | 14.4386 | 18.2595 | 44.3645 | 75.6407 | 96.3258 | 3.6742 | 281 |
| hist_gb__baseline | 6.9013 | 9.1902 | 0.5322 | 5.3829 | 14.5694 | 18.7516 | 46.8881 | 77.7981 | 95.8290 | 4.1710 | 319 |
| hist_gb__traditional | 6.9918 | 9.2338 | 0.5277 | 5.5355 | 14.6262 | 18.8552 | 45.5413 | 76.7913 | 95.8421 | 4.1579 | 318 |
| hist_gb__deep | 7.0386 | 9.2726 | 0.5237 | 5.5848 | 14.6249 | 18.7601 | 45.5152 | 76.3860 | 95.8682 | 4.1318 | 316 |
| hist_gb__combined | 7.0537 | 9.2580 | 0.5252 | 5.6642 | 14.7250 | 18.6890 | 45.0314 | 76.2422 | 96.0120 | 3.9880 | 305 |


## Comparações de algoritmo contra Elastic Net V0.5 correspondente

Redução de MAE positiva indica melhora. ΔRMSE, ΔP95 e Δ proporção >20 positivos indicam piora. Promissor exige ≥2% de redução do MAE, melhora em ≥4/5 folds e não piorar RMSE/P95 em mais de 2%. O limiar é operacional, não universal.

| Modelo | Redução MAE % | Folds melhores | ΔRMSE % | ΔP95 % | Δ >20 (p.p.) | Promissor |
| --- | --- | --- | --- | --- | --- | --- |
| spline_en__baseline | 1.2278 | 5 | -1.2141 | -0.2016 | 0.0000 | não |
| spline_en__traditional | 1.0568 | 5 | -1.0389 | 0.3338 | -0.0262 | não |
| spline_en__deep | 1.0588 | 5 | -1.0668 | -1.3240 | -0.0523 | não |
| spline_en__combined | 0.9417 | 5 | -0.9716 | 0.0685 | -0.0915 | não |
| hist_gb__baseline | 2.7164 | 5 | -0.2565 | 3.0618 | 0.4576 | não |
| hist_gb__traditional | 0.9819 | 5 | 0.4946 | 3.2631 | 0.5622 | não |
| hist_gb__deep | 1.7293 | 5 | -0.0818 | 1.8702 | 0.4707 | não |
| hist_gb__combined | 1.5272 | 5 | -0.4024 | 2.4223 | 0.2223 | não |


## Contribuição incremental das letras dentro de cada família

Cada comparação usa o Baseline da própria família, não o Elastic Net antigo. Ganho por trocar algoritmo não demonstra ganho das letras.

| Modelo | Baseline de referência | Redução MAE % | Folds melhores | ΔRMSE % | ΔP95 % | Δ >20 (p.p.) |
| --- | --- | --- | --- | --- | --- | --- |
| spline_en__traditional | spline_en__baseline | 0.2901 | 3 | -0.1000 | 0.8949 | -0.1438 |
| spline_en__deep | spline_en__baseline | -1.1379 | 0 | 0.8700 | 0.0772 | -0.1046 |
| spline_en__combined | spline_en__baseline | -1.2664 | 0 | 1.1337 | 0.5597 | -0.0392 |
| hist_gb__traditional | hist_gb__baseline | -1.3122 | 0 | 0.4740 | 0.5526 | -0.0131 |
| hist_gb__deep | hist_gb__baseline | -1.9896 | 0 | 0.8962 | 0.0453 | -0.0392 |
| hist_gb__combined | hist_gb__baseline | -2.2083 | 0 | 0.7384 | -0.3340 | -0.1831 |


## Trade-offs de cauda

- spline_en__traditional versus elastic_net__traditional: ΔMAE=-0.074620; ΔRMSE=-0.095456; ΔP95=0.060941; Δ>20=-0.0262 p.p.
- spline_en__combined versus elastic_net__combined: ΔMAE=-0.067451; ΔRMSE=-0.090314; ΔP95=0.012495; Δ>20=-0.0915 p.p.
- spline_en__traditional versus spline_en__baseline: ΔMAE=-0.020329; ΔRMSE=-0.009104; ΔP95=0.162490; Δ>20=-0.1438 p.p.
- hist_gb__baseline versus elastic_net__baseline: ΔMAE=-0.192704; ΔRMSE=-0.023629; ΔP95=0.557076; Δ>20=0.4576 p.p.
- hist_gb__traditional versus elastic_net__traditional: ΔMAE=-0.069337; ΔRMSE=0.045441; ΔP95=0.595831; Δ>20=0.5622 p.p.
- hist_gb__deep versus elastic_net__deep: ΔMAE=-0.123860; ΔRMSE=-0.007590; ΔP95=0.344402; Δ>20=0.4707 p.p.
- hist_gb__combined versus elastic_net__combined: ΔMAE=-0.109392; ΔRMSE=-0.037407; ΔP95=0.441996; Δ>20=0.2223 p.p.

## Perdas selecionadas no boosting

| Bloco | squared_error (folds) | absolute_error (folds) |
| --- | --- | --- |
| baseline | 0 | 5 |
| traditional | 1 | 4 |
| deep | 2 | 3 |
| combined | 2 | 3 |


A perda foi escolhida apenas pelos três MAEs internos. Não se escolheu uma perda global pelo resultado OOF externo.

## Resultados e hiperparâmetros por fold

| Modelo | Fold | n | MAE | RMSE | R² | P95 | >20 % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| elastic_net__baseline | 0 | 1529 | 7.3048 | 9.3840 | 0.5165 | 18.6352 | 3.5971 |
| elastic_net__baseline | 1 | 1529 | 6.9096 | 9.0293 | 0.5522 | 17.5719 | 3.4009 |
| elastic_net__baseline | 2 | 1528 | 6.9735 | 9.0426 | 0.5328 | 17.4388 | 3.5340 |
| elastic_net__baseline | 3 | 1529 | 7.1366 | 9.2573 | 0.5325 | 18.0891 | 3.9241 |
| elastic_net__baseline | 4 | 1533 | 7.1452 | 9.3493 | 0.5146 | 18.9734 | 4.1096 |
| elastic_net__traditional | 0 | 1529 | 7.2072 | 9.3123 | 0.5239 | 18.4375 | 3.6625 |
| elastic_net__traditional | 1 | 1529 | 6.8842 | 9.0251 | 0.5526 | 17.9213 | 3.2701 |
| elastic_net__traditional | 2 | 1528 | 6.9496 | 9.0270 | 0.5345 | 17.6386 | 3.4031 |
| elastic_net__traditional | 3 | 1529 | 7.1078 | 9.2123 | 0.5370 | 17.9460 | 3.7279 |
| elastic_net__traditional | 4 | 1533 | 7.1568 | 9.3589 | 0.5136 | 18.8504 | 3.9139 |
| elastic_net__deep | 0 | 1529 | 7.3428 | 9.4141 | 0.5134 | 18.6699 | 3.7279 |
| elastic_net__deep | 1 | 1529 | 7.0162 | 9.1400 | 0.5411 | 17.6277 | 3.3355 |
| elastic_net__deep | 2 | 1528 | 6.9682 | 9.0672 | 0.5303 | 17.8786 | 3.2723 |
| elastic_net__deep | 3 | 1529 | 7.1855 | 9.2767 | 0.5305 | 17.9563 | 3.7933 |
| elastic_net__deep | 4 | 1533 | 7.2991 | 9.4951 | 0.4993 | 18.8055 | 4.1748 |
| elastic_net__combined | 0 | 1529 | 7.3383 | 9.4488 | 0.5098 | 18.1510 | 3.8587 |
| elastic_net__combined | 1 | 1529 | 7.0101 | 9.1387 | 0.5413 | 17.7915 | 3.6625 |
| elastic_net__combined | 2 | 1528 | 6.9498 | 9.0668 | 0.5303 | 17.8756 | 3.3377 |
| elastic_net__combined | 3 | 1529 | 7.1815 | 9.3119 | 0.5269 | 18.0010 | 3.7933 |
| elastic_net__combined | 4 | 1533 | 7.3350 | 9.5027 | 0.4985 | 19.1287 | 4.1748 |
| dummy__baseline | 0 | 1529 | 10.7303 | 13.4957 | -0.0000 | 25.0012 | 12.8188 |
| dummy__baseline | 1 | 1529 | 10.7964 | 13.4949 | -0.0003 | 25.9637 | 14.1923 |
| dummy__baseline | 2 | 1528 | 10.5862 | 13.2301 | -0.0000 | 25.0010 | 11.9110 |
| dummy__baseline | 3 | 1529 | 10.8378 | 13.5397 | -0.0001 | 26.0400 | 12.2956 |
| dummy__baseline | 4 | 1533 | 10.6605 | 13.4195 | -0.0000 | 25.0268 | 12.0026 |
| spline_en__baseline | 0 | 1529 | 7.2660 | 9.3035 | 0.5248 | 18.3566 | 3.5317 |
| spline_en__baseline | 1 | 1529 | 6.8802 | 8.9851 | 0.5566 | 17.9003 | 3.4009 |
| spline_en__baseline | 2 | 1528 | 6.8638 | 8.9346 | 0.5439 | 17.1667 | 3.5340 |
| spline_en__baseline | 3 | 1529 | 6.9888 | 9.0895 | 0.5493 | 18.4944 | 4.3819 |
| spline_en__baseline | 4 | 1533 | 7.0354 | 9.1918 | 0.5308 | 18.5981 | 3.7182 |
| spline_en__traditional | 0 | 1529 | 7.1852 | 9.2496 | 0.5303 | 18.4985 | 3.4663 |
| spline_en__traditional | 1 | 1529 | 6.8439 | 8.9462 | 0.5604 | 17.9643 | 3.3355 |
| spline_en__traditional | 2 | 1528 | 6.8498 | 8.9269 | 0.5447 | 17.2990 | 3.3377 |
| spline_en__traditional | 3 | 1529 | 6.9890 | 9.0926 | 0.5490 | 18.2778 | 3.9895 |
| spline_en__traditional | 4 | 1533 | 7.0645 | 9.2431 | 0.5256 | 18.9014 | 3.7182 |
| spline_en__deep | 0 | 1529 | 7.3105 | 9.3534 | 0.5197 | 18.6389 | 3.5971 |
| spline_en__deep | 1 | 1529 | 6.9786 | 9.0950 | 0.5457 | 18.1220 | 3.2701 |
| spline_en__deep | 2 | 1528 | 6.8902 | 8.9699 | 0.5403 | 17.5250 | 3.5340 |
| spline_en__deep | 3 | 1529 | 7.0596 | 9.1227 | 0.5460 | 17.8755 | 3.9241 |
| spline_en__deep | 4 | 1533 | 7.1938 | 9.3578 | 0.5137 | 18.8586 | 3.7182 |
| spline_en__combined | 0 | 1529 | 7.3056 | 9.3898 | 0.5159 | 18.5621 | 3.8587 |
| spline_en__combined | 1 | 1529 | 6.9718 | 9.0786 | 0.5473 | 17.8059 | 3.4009 |
| spline_en__combined | 2 | 1528 | 6.8895 | 8.9883 | 0.5384 | 17.5777 | 3.4686 |
| spline_en__combined | 3 | 1529 | 7.0826 | 9.1764 | 0.5406 | 18.2190 | 3.7279 |
| spline_en__combined | 4 | 1533 | 7.2281 | 9.3850 | 0.5109 | 18.7450 | 3.9139 |
| hist_gb__baseline | 0 | 1529 | 7.1589 | 9.3945 | 0.5154 | 18.9133 | 4.4474 |
| hist_gb__baseline | 1 | 1529 | 6.7295 | 9.0307 | 0.5521 | 18.0164 | 3.9241 |
| hist_gb__baseline | 2 | 1528 | 6.7461 | 8.9886 | 0.5384 | 18.5257 | 3.7958 |
| hist_gb__baseline | 3 | 1529 | 6.8288 | 9.1981 | 0.5384 | 18.6894 | 4.3165 |
| hist_gb__baseline | 4 | 1533 | 7.0427 | 9.3317 | 0.5164 | 19.2146 | 4.3705 |
| hist_gb__traditional | 0 | 1529 | 7.1811 | 9.4658 | 0.5080 | 19.1972 | 4.4474 |
| hist_gb__traditional | 1 | 1529 | 6.8223 | 9.1507 | 0.5401 | 18.2169 | 3.9895 |
| hist_gb__traditional | 2 | 1528 | 6.8503 | 9.0575 | 0.5313 | 18.4181 | 3.7958 |
| hist_gb__traditional | 3 | 1529 | 7.0101 | 9.0881 | 0.5494 | 18.6157 | 4.1857 |
| hist_gb__traditional | 4 | 1533 | 7.0951 | 9.3984 | 0.5095 | 19.4717 | 4.3705 |
| hist_gb__deep | 0 | 1529 | 7.2104 | 9.5268 | 0.5017 | 19.1980 | 4.5782 |
| hist_gb__deep | 1 | 1529 | 6.9424 | 9.2395 | 0.5311 | 18.5130 | 4.1857 |
| hist_gb__deep | 2 | 1528 | 6.7920 | 8.8788 | 0.5496 | 17.5273 | 3.4686 |
| hist_gb__deep | 3 | 1529 | 7.1195 | 9.2321 | 0.5350 | 17.8284 | 3.8587 |
| hist_gb__deep | 4 | 1533 | 7.1284 | 9.4707 | 0.5019 | 19.4186 | 4.5662 |
| hist_gb__combined | 0 | 1529 | 7.2668 | 9.3377 | 0.5213 | 18.3318 | 3.4009 |
| hist_gb__combined | 1 | 1529 | 6.9840 | 9.2905 | 0.5259 | 19.0082 | 4.3819 |
| hist_gb__combined | 2 | 1528 | 6.8530 | 9.0847 | 0.5285 | 18.2273 | 3.9267 |
| hist_gb__combined | 3 | 1529 | 7.0600 | 9.1732 | 0.5409 | 18.1326 | 3.7933 |
| hist_gb__combined | 4 | 1533 | 7.1043 | 9.4002 | 0.5093 | 18.9839 | 4.4357 |


| Modelo | Fold | Parâmetros selecionados | MAE interno | PCA LFM/MiniLM | Tempo fold s | Warnings |
| --- | --- | --- | --- | --- | --- | --- |
| spline_en__baseline | 0 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 6.9771 | {'lfm': None, 'embedding': None} | 4.2700 | 0 |
| spline_en__baseline | 1 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.1018 | {'lfm': None, 'embedding': None} | 0.7762 | 0 |
| spline_en__baseline | 2 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0932 | {'lfm': None, 'embedding': None} | 0.8296 | 0 |
| spline_en__baseline | 3 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0949 | {'lfm': None, 'embedding': None} | 0.7618 | 0 |
| spline_en__baseline | 4 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.8} | 7.0653 | {'lfm': None, 'embedding': None} | 0.8008 | 0 |
| spline_en__traditional | 0 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 6.9873 | {'lfm': 77, 'embedding': None} | 2.1296 | 0 |
| spline_en__traditional | 1 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0823 | {'lfm': 77, 'embedding': None} | 2.0875 | 0 |
| spline_en__traditional | 2 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0779 | {'lfm': 76, 'embedding': None} | 2.1875 | 0 |
| spline_en__traditional | 3 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0923 | {'lfm': 77, 'embedding': None} | 2.5704 | 0 |
| spline_en__traditional | 4 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0545 | {'lfm': 76, 'embedding': None} | 2.0517 | 0 |
| spline_en__deep | 0 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.0855 | {'lfm': None, 'embedding': 184} | 3.9249 | 0 |
| spline_en__deep | 1 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.2175 | {'lfm': None, 'embedding': 185} | 3.8947 | 0 |
| spline_en__deep | 2 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.2183 | {'lfm': None, 'embedding': 184} | 3.9374 | 0 |
| spline_en__deep | 3 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.1748 | {'lfm': None, 'embedding': 185} | 4.0206 | 0 |
| spline_en__deep | 4 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.1612 | {'lfm': None, 'embedding': 184} | 3.8801 | 0 |
| spline_en__combined | 0 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.1280 | {'lfm': 77, 'embedding': 184} | 5.3300 | 0 |
| spline_en__combined | 1 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.2274 | {'lfm': 77, 'embedding': 185} | 5.3181 | 0 |
| spline_en__combined | 2 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.2480 | {'lfm': 76, 'embedding': 184} | 5.2971 | 0 |
| spline_en__combined | 3 | {'n_knots': 5, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.2065 | {'lfm': 77, 'embedding': 185} | 5.1727 | 0 |
| spline_en__combined | 4 | {'n_knots': 3, 'alpha': 0.003, 'l1_ratio': 0.95} | 7.1919 | {'lfm': 76, 'embedding': 184} | 5.2254 | 0 |
| hist_gb__baseline | 0 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 6.9387 | {'lfm': None, 'embedding': None} | 13.1377 | 0 |
| hist_gb__baseline | 1 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 10} | 7.0608 | {'lfm': None, 'embedding': None} | 13.0208 | 0 |
| hist_gb__baseline | 2 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.0126 | {'lfm': None, 'embedding': None} | 12.5154 | 0 |
| hist_gb__baseline | 3 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.0590 | {'lfm': None, 'embedding': None} | 12.6219 | 0 |
| hist_gb__baseline | 4 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 6.9525 | {'lfm': None, 'embedding': None} | 12.2768 | 0 |
| hist_gb__traditional | 0 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.0578 | {'lfm': 77, 'embedding': None} | 30.1591 | 0 |
| hist_gb__traditional | 1 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1665 | {'lfm': 77, 'embedding': None} | 28.4559 | 0 |
| hist_gb__traditional | 2 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1454 | {'lfm': 76, 'embedding': None} | 27.4806 | 0 |
| hist_gb__traditional | 3 | {'loss': 'squared_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1472 | {'lfm': 77, 'embedding': None} | 28.3353 | 0 |
| hist_gb__traditional | 4 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.0631 | {'lfm': 76, 'embedding': None} | 29.6793 | 0 |
| hist_gb__deep | 0 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1374 | {'lfm': None, 'embedding': 184} | 66.1767 | 0 |
| hist_gb__deep | 1 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.2273 | {'lfm': None, 'embedding': 185} | 65.6740 | 0 |
| hist_gb__deep | 2 | {'loss': 'squared_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.2319 | {'lfm': None, 'embedding': 184} | 60.9932 | 0 |
| hist_gb__deep | 3 | {'loss': 'squared_error', 'max_leaf_nodes': 15, 'l2_regularization': 10} | 7.2317 | {'lfm': None, 'embedding': 185} | 56.6513 | 0 |
| hist_gb__deep | 4 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1470 | {'lfm': None, 'embedding': 184} | 56.6135 | 0 |
| hist_gb__combined | 0 | {'loss': 'squared_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1228 | {'lfm': 77, 'embedding': 184} | 75.8864 | 0 |
| hist_gb__combined | 1 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.2412 | {'lfm': 77, 'embedding': 185} | 75.1419 | 0 |
| hist_gb__combined | 2 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.2557 | {'lfm': 76, 'embedding': 184} | 75.3458 | 0 |
| hist_gb__combined | 3 | {'loss': 'squared_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.2267 | {'lfm': 77, 'embedding': 185} | 75.3037 | 0 |
| hist_gb__combined | 4 | {'loss': 'absolute_error', 'max_leaf_nodes': 15, 'l2_regularization': 1} | 7.1466 | {'lfm': 76, 'embedding': 184} | 75.4255 | 0 |


## Estratos descritivos

Faixas, períodos e flags foram predefinidos. n<30 marcado como grupo pequeno; n=0 também é mostrado. Não se calcula R² dentro dos estratos. Todas as métricas dos 13 modelos e de cada estrato estão no CSV; aqui são apresentados os oito novos pipelines. Nenhum estrato orientou tuning. Flags individuais sobrepõem-se; suas contagens não devem ser somadas. Year descreve o campo da fonte, não ano original certificado.

### Faixas do alvo

| Estrato | Modelo | n | Artistas | n<30 | MAE | RMSE | P95 | >20 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [0,10) | spline_en__baseline | 729 | 461 | não | 9.0518 | 10.8752 | 18.8918 | 3.9781 |
| [10,20) | spline_en__baseline | 1949 | 1223 | não | 6.3864 | 7.6772 | 13.9880 | 0.3079 |
| [20,30) | spline_en__baseline | 2187 | 1449 | não | 5.1491 | 6.2999 | 11.8729 | 0.0457 |
| [30,40) | spline_en__baseline | 1590 | 1242 | não | 5.9625 | 7.7262 | 16.2935 | 1.6352 |
| [40,50) | spline_en__baseline | 749 | 649 | não | 8.8290 | 11.2213 | 22.5511 | 9.2123 |
| [50,60) | spline_en__baseline | 319 | 276 | não | 14.3737 | 16.6588 | 27.7745 | 26.6458 |
| [60,70) | spline_en__baseline | 98 | 88 | não | 18.6411 | 20.7674 | 32.8803 | 47.9592 |
| [70,80) | spline_en__baseline | 26 | 24 | sim | 28.2364 | 30.3121 | 44.5299 | 76.9231 |
| [80,90) | spline_en__baseline | 1 | 1 | sim | 42.4721 | 42.4721 | 42.4721 | 100.0000 |
| [90,100] | spline_en__baseline | 0 | 0 | sim | — | — | — | — |
| [0,10) | spline_en__traditional | 729 | 461 | não | 8.6820 | 10.5922 | 18.3572 | 3.7037 |
| [10,20) | spline_en__traditional | 1949 | 1223 | não | 6.3321 | 7.7368 | 14.3163 | 0.6157 |
| [20,30) | spline_en__traditional | 2187 | 1449 | não | 5.2909 | 6.4907 | 12.2636 | 0.0914 |
| [30,40) | spline_en__traditional | 1590 | 1242 | não | 6.0377 | 7.7864 | 15.9174 | 1.4465 |
| [40,50) | spline_en__traditional | 749 | 649 | não | 8.7792 | 11.2522 | 22.7109 | 8.2777 |
| [50,60) | spline_en__traditional | 319 | 276 | não | 13.9073 | 16.2175 | 26.5715 | 24.7649 |
| [60,70) | spline_en__traditional | 98 | 88 | não | 18.4191 | 20.5321 | 31.4367 | 47.9592 |
| [70,80) | spline_en__traditional | 26 | 24 | sim | 28.1590 | 30.0686 | 42.7251 | 76.9231 |
| [80,90) | spline_en__traditional | 1 | 1 | sim | 42.3772 | 42.3772 | 42.3772 | 100.0000 |
| [90,100] | spline_en__traditional | 0 | 0 | sim | — | — | — | — |
| [0,10) | spline_en__deep | 729 | 461 | não | 8.9822 | 10.8648 | 17.9477 | 4.1152 |
| [10,20) | spline_en__deep | 1949 | 1223 | não | 6.4600 | 7.8214 | 14.3071 | 0.5644 |
| [20,30) | spline_en__deep | 2187 | 1449 | não | 5.2796 | 6.4964 | 12.5954 | 0.1829 |
| [30,40) | spline_en__deep | 1590 | 1242 | não | 6.1777 | 7.8975 | 15.7940 | 1.5723 |
| [40,50) | spline_en__deep | 749 | 649 | não | 8.7826 | 11.1689 | 21.7302 | 8.0107 |
| [50,60) | spline_en__deep | 319 | 276 | não | 14.1578 | 16.4665 | 27.9821 | 24.7649 |
| [60,70) | spline_en__deep | 98 | 88 | não | 18.5437 | 20.6992 | 31.3135 | 46.9388 |
| [70,80) | spline_en__deep | 26 | 24 | sim | 28.2995 | 30.4650 | 45.3499 | 76.9231 |
| [80,90) | spline_en__deep | 1 | 1 | sim | 43.3239 | 43.3239 | 43.3239 | 100.0000 |
| [90,100] | spline_en__deep | 0 | 0 | sim | — | — | — | — |
| [0,10) | spline_en__combined | 729 | 461 | não | 8.7456 | 10.6935 | 18.2071 | 4.3896 |
| [10,20) | spline_en__combined | 1949 | 1223 | não | 6.4850 | 7.9405 | 14.6852 | 0.7696 |
| [20,30) | spline_en__combined | 2187 | 1449 | não | 5.4002 | 6.6469 | 12.7878 | 0.2286 |
| [30,40) | spline_en__combined | 1590 | 1242 | não | 6.2050 | 7.9352 | 16.3730 | 1.5094 |
| [40,50) | spline_en__combined | 749 | 649 | não | 8.7697 | 11.2243 | 22.2759 | 7.7437 |
| [50,60) | spline_en__combined | 319 | 276 | não | 13.8878 | 16.2290 | 27.3079 | 25.0784 |
| [60,70) | spline_en__combined | 98 | 88 | não | 18.4058 | 20.5063 | 30.1540 | 47.9592 |
| [70,80) | spline_en__combined | 26 | 24 | sim | 28.1337 | 30.1778 | 44.5099 | 73.0769 |
| [80,90) | spline_en__combined | 1 | 1 | sim | 42.3005 | 42.3005 | 42.3005 | 100.0000 |
| [90,100] | spline_en__combined | 0 | 0 | sim | — | — | — | — |
| [0,10) | hist_gb__baseline | 729 | 461 | não | 9.5527 | 11.1395 | 17.7688 | 3.0178 |
| [10,20) | hist_gb__baseline | 1949 | 1223 | não | 5.1656 | 6.4519 | 12.3680 | 0.3592 |
| [20,30) | hist_gb__baseline | 2187 | 1449 | não | 4.6047 | 5.6807 | 10.8717 | 0.0000 |
| [30,40) | hist_gb__baseline | 1590 | 1242 | não | 6.5260 | 8.2899 | 16.6564 | 1.6352 |
| [40,50) | hist_gb__baseline | 749 | 649 | não | 10.0973 | 12.4233 | 24.4229 | 12.0160 |
| [50,60) | hist_gb__baseline | 319 | 276 | não | 15.6396 | 18.0610 | 30.4507 | 32.2884 |
| [60,70) | hist_gb__baseline | 98 | 88 | não | 19.8675 | 21.9860 | 35.3463 | 51.0204 |
| [70,80) | hist_gb__baseline | 26 | 24 | sim | 29.3313 | 31.5071 | 50.6017 | 76.9231 |
| [80,90) | hist_gb__baseline | 1 | 1 | sim | 40.9087 | 40.9087 | 40.9087 | 100.0000 |
| [90,100] | hist_gb__baseline | 0 | 0 | sim | — | — | — | — |
| [0,10) | hist_gb__traditional | 729 | 461 | não | 10.1372 | 11.5202 | 18.2124 | 3.2922 |
| [10,20) | hist_gb__traditional | 1949 | 1223 | não | 5.3741 | 6.7476 | 13.2593 | 0.4105 |
| [20,30) | hist_gb__traditional | 2187 | 1449 | não | 4.6282 | 5.6513 | 10.8511 | 0.0000 |
| [30,40) | hist_gb__traditional | 1590 | 1242 | não | 6.3837 | 8.0929 | 16.1597 | 1.1950 |
| [40,50) | hist_gb__traditional | 749 | 649 | não | 10.1728 | 12.3798 | 23.9588 | 11.2150 |
| [50,60) | hist_gb__traditional | 319 | 276 | não | 15.4204 | 17.8212 | 29.0289 | 34.1693 |
| [60,70) | hist_gb__traditional | 98 | 88 | não | 20.1555 | 22.1696 | 35.7329 | 53.0612 |
| [70,80) | hist_gb__traditional | 26 | 24 | sim | 30.0627 | 31.9715 | 49.3481 | 80.7692 |
| [80,90) | hist_gb__traditional | 1 | 1 | sim | 42.0334 | 42.0334 | 42.0334 | 100.0000 |
| [90,100] | hist_gb__traditional | 0 | 0 | sim | — | — | — | — |
| [0,10) | hist_gb__deep | 729 | 461 | não | 10.5268 | 11.8747 | 18.5254 | 3.8409 |
| [10,20) | hist_gb__deep | 1949 | 1223 | não | 5.5449 | 6.9103 | 13.6109 | 0.3079 |
| [20,30) | hist_gb__deep | 2187 | 1449 | não | 4.6028 | 5.6306 | 10.7726 | 0.0000 |
| [30,40) | hist_gb__deep | 1590 | 1242 | não | 6.2744 | 7.9911 | 15.8923 | 1.1321 |
| [40,50) | hist_gb__deep | 749 | 649 | não | 10.0447 | 12.1973 | 23.5235 | 11.0814 |
| [50,60) | hist_gb__deep | 319 | 276 | não | 15.6523 | 17.9223 | 29.2771 | 34.4828 |
| [60,70) | hist_gb__deep | 98 | 88 | não | 20.1737 | 22.3655 | 35.1111 | 50.0000 |
| [70,80) | hist_gb__deep | 26 | 24 | sim | 29.6198 | 31.6277 | 48.8104 | 80.7692 |
| [80,90) | hist_gb__deep | 1 | 1 | sim | 43.7905 | 43.7905 | 43.7905 | 100.0000 |
| [90,100] | hist_gb__deep | 0 | 0 | sim | — | — | — | — |
| [0,10) | hist_gb__combined | 729 | 461 | não | 10.6297 | 11.8843 | 18.3679 | 3.1550 |
| [10,20) | hist_gb__combined | 1949 | 1223 | não | 5.5642 | 6.9597 | 13.7833 | 0.3079 |
| [20,30) | hist_gb__combined | 2187 | 1449 | não | 4.5982 | 5.6129 | 10.6326 | 0.0000 |
| [30,40) | hist_gb__combined | 1590 | 1242 | não | 6.2530 | 7.9238 | 15.7595 | 0.9434 |
| [40,50) | hist_gb__combined | 749 | 649 | não | 10.1649 | 12.2407 | 23.7610 | 10.5474 |
| [50,60) | hist_gb__combined | 319 | 276 | não | 15.6066 | 17.8975 | 29.1702 | 34.1693 |
| [60,70) | hist_gb__combined | 98 | 88 | não | 19.9478 | 21.9538 | 33.4629 | 52.0408 |
| [70,80) | hist_gb__combined | 26 | 24 | sim | 29.4255 | 31.6118 | 49.5204 | 80.7692 |
| [80,90) | hist_gb__combined | 1 | 1 | sim | 42.4184 | 42.4184 | 42.4184 | 100.0000 |
| [90,100] | hist_gb__combined | 0 | 0 | sim | — | — | — | — |


### Período

| Estrato | Modelo | n | Artistas | n<30 | MAE | RMSE | P95 | >20 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <2000 | spline_en__baseline | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | spline_en__baseline | 910 | 581 | não | 7.2772 | 9.4890 | 19.4362 | 4.6154 |
| 2005-2009 | spline_en__baseline | 1177 | 771 | não | 6.7951 | 8.8490 | 17.7924 | 3.2285 |
| 2010-2014 | spline_en__baseline | 1876 | 1213 | não | 6.9260 | 9.0854 | 18.3130 | 3.7313 |
| 2015-2019 | spline_en__baseline | 3436 | 2169 | não | 6.9363 | 8.8538 | 17.5414 | 3.3178 |
| 2020-2023 | spline_en__baseline | 249 | 195 | não | 8.6025 | 11.9062 | 23.7825 | 8.0321 |
| >=2024 | spline_en__baseline | 0 | 0 | sim | — | — | — | — |
| <2000 | spline_en__traditional | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | spline_en__traditional | 910 | 581 | não | 7.0980 | 9.3594 | 19.1141 | 4.3956 |
| 2005-2009 | spline_en__traditional | 1177 | 771 | não | 6.7568 | 8.7976 | 17.9289 | 3.0586 |
| 2010-2014 | spline_en__traditional | 1876 | 1213 | não | 6.9079 | 9.0271 | 18.1885 | 3.3582 |
| 2015-2019 | spline_en__traditional | 3436 | 2169 | não | 6.9499 | 8.8747 | 17.8022 | 3.3178 |
| 2020-2023 | spline_en__traditional | 249 | 195 | não | 8.7644 | 12.3582 | 25.7651 | 8.0321 |
| >=2024 | spline_en__traditional | 0 | 0 | sim | — | — | — | — |
| <2000 | spline_en__deep | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | spline_en__deep | 910 | 581 | não | 7.2664 | 9.5158 | 19.0264 | 4.3956 |
| 2005-2009 | spline_en__deep | 1177 | 771 | não | 6.8696 | 8.9187 | 17.4419 | 3.4834 |
| 2010-2014 | spline_en__deep | 1876 | 1213 | não | 7.0093 | 9.1358 | 18.0374 | 3.4648 |
| 2015-2019 | spline_en__deep | 3436 | 2169 | não | 7.0271 | 8.9403 | 17.8782 | 3.2596 |
| 2020-2023 | spline_en__deep | 249 | 195 | não | 8.8598 | 12.2626 | 25.9270 | 7.2289 |
| >=2024 | spline_en__deep | 0 | 0 | sim | — | — | — | — |
| <2000 | spline_en__combined | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | spline_en__combined | 910 | 581 | não | 7.2175 | 9.5347 | 19.5883 | 4.6154 |
| 2005-2009 | spline_en__combined | 1177 | 771 | não | 6.9034 | 8.9234 | 17.3106 | 3.3985 |
| 2010-2014 | spline_en__combined | 1876 | 1213 | não | 7.0010 | 9.1126 | 18.1662 | 3.2516 |
| 2015-2019 | spline_en__combined | 3436 | 2169 | não | 7.0429 | 8.9828 | 17.9669 | 3.4342 |
| 2020-2023 | spline_en__combined | 249 | 195 | não | 8.9999 | 12.4453 | 25.3212 | 8.0321 |
| >=2024 | spline_en__combined | 0 | 0 | sim | — | — | — | — |
| <2000 | hist_gb__baseline | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | hist_gb__baseline | 910 | 581 | não | 6.7026 | 9.0497 | 18.4975 | 4.0659 |
| 2005-2009 | hist_gb__baseline | 1177 | 771 | não | 6.3440 | 8.6546 | 17.1344 | 3.4834 |
| 2010-2014 | hist_gb__baseline | 1876 | 1213 | não | 6.9120 | 9.2644 | 19.2019 | 4.4776 |
| 2015-2019 | hist_gb__baseline | 3436 | 2169 | não | 6.9868 | 9.0764 | 18.6794 | 3.9290 |
| 2020-2023 | hist_gb__baseline | 249 | 195 | não | 9.0009 | 12.5443 | 25.3587 | 8.8353 |
| >=2024 | hist_gb__baseline | 0 | 0 | sim | — | — | — | — |
| <2000 | hist_gb__traditional | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | hist_gb__traditional | 910 | 581 | não | 6.8912 | 9.0889 | 18.3287 | 3.4066 |
| 2005-2009 | hist_gb__traditional | 1177 | 771 | não | 6.4488 | 8.6862 | 17.4290 | 3.4834 |
| 2010-2014 | hist_gb__traditional | 1876 | 1213 | não | 6.8603 | 9.1401 | 18.5798 | 4.2644 |
| 2015-2019 | hist_gb__traditional | 3436 | 2169 | não | 7.1083 | 9.2069 | 19.1155 | 4.1327 |
| 2020-2023 | hist_gb__traditional | 249 | 195 | não | 9.3102 | 12.6947 | 26.3303 | 9.6386 |
| >=2024 | hist_gb__traditional | 0 | 0 | sim | — | — | — | — |
| <2000 | hist_gb__deep | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | hist_gb__deep | 910 | 581 | não | 6.8501 | 9.0846 | 18.1408 | 3.8462 |
| 2005-2009 | hist_gb__deep | 1177 | 771 | não | 6.5083 | 8.7492 | 17.0127 | 3.7383 |
| 2010-2014 | hist_gb__deep | 1876 | 1213 | não | 6.9813 | 9.2215 | 18.4218 | 4.2111 |
| 2015-2019 | hist_gb__deep | 3436 | 2169 | não | 7.1488 | 9.2316 | 18.8643 | 3.9581 |
| 2020-2023 | hist_gb__deep | 249 | 195 | não | 9.1446 | 12.6788 | 25.3988 | 8.8353 |
| >=2024 | hist_gb__deep | 0 | 0 | sim | — | — | — | — |
| <2000 | hist_gb__combined | 0 | 0 | sim | — | — | — | — |
| 2000-2004 | hist_gb__combined | 910 | 581 | não | 6.9436 | 9.1119 | 17.1499 | 3.2967 |
| 2005-2009 | hist_gb__combined | 1177 | 771 | não | 6.5189 | 8.7212 | 16.8834 | 3.4834 |
| 2010-2014 | hist_gb__combined | 1876 | 1213 | não | 6.8853 | 9.1139 | 18.4224 | 3.8913 |
| 2015-2019 | hist_gb__combined | 3436 | 2169 | não | 7.1969 | 9.2640 | 18.8141 | 4.0163 |
| 2020-2023 | hist_gb__combined | 249 | 195 | não | 9.2760 | 12.6322 | 26.1989 | 9.2369 |
| >=2024 | hist_gb__combined | 0 | 0 | sim | — | — | — | — |


### Flags de versão

| Estrato | Modelo | n | Artistas | n<30 | MAE | RMSE | P95 | >20 % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| any_version=False | spline_en__baseline | 7264 | 3648 | não | 7.0138 | 9.0972 | 18.1679 | 3.7307 |
| any_version=True | spline_en__baseline | 384 | 290 | não | 6.8753 | 9.1924 | 17.9578 | 3.3854 |
| remaster=False | spline_en__baseline | 7605 | 3731 | não | 7.0015 | 9.0956 | 18.1022 | 3.6818 |
| remaster=True | spline_en__baseline | 43 | 36 | não | 7.9632 | 10.1703 | 22.0921 | 9.3023 |
| remix=False | spline_en__baseline | 7555 | 3717 | não | 7.0001 | 9.0892 | 18.1513 | 3.7194 |
| remix=True | spline_en__baseline | 93 | 88 | não | 7.5590 | 10.0853 | 18.0478 | 3.2258 |
| live=False | spline_en__baseline | 7448 | 3717 | não | 7.0176 | 9.1096 | 18.1919 | 3.7594 |
| live=True | spline_en__baseline | 200 | 141 | não | 6.6080 | 8.8113 | 16.2261 | 2.0000 |
| acoustic=False | spline_en__baseline | 7630 | 3746 | não | 7.0067 | 9.1026 | 18.1560 | 3.7090 |
| acoustic=True | spline_en__baseline | 18 | 18 | sim | 7.0857 | 8.8147 | 13.8569 | 5.5556 |
| radio_edit=False | spline_en__baseline | 7636 | 3741 | não | 7.0055 | 9.0990 | 18.1504 | 3.7061 |
| radio_edit=True | spline_en__baseline | 12 | 12 | sim | 7.8887 | 10.8473 | 20.1866 | 8.3333 |
| mono_stereo=False | spline_en__baseline | 7645 | 3747 | não | 7.0087 | 9.1036 | 18.1607 | 3.7148 |
| mono_stereo=True | spline_en__baseline | 3 | 3 | sim | 2.3913 | 2.4384 | 2.7453 | 0.0000 |
| instrumental=False | spline_en__baseline | 7645 | 3748 | não | 7.0069 | 9.1024 | 18.1607 | 3.7148 |
| instrumental=True | spline_en__baseline | 3 | 3 | sim | 7.0825 | 7.8472 | 9.8747 | 0.0000 |
| demo=False | spline_en__baseline | 7631 | 3747 | não | 7.0158 | 9.1104 | 18.1665 | 3.7217 |
| demo=True | spline_en__baseline | 17 | 14 | sim | 3.0112 | 3.7465 | 6.9492 | 0.0000 |
| any_version=False | spline_en__traditional | 7264 | 3648 | não | 6.9793 | 9.0737 | 18.2700 | 3.5793 |
| any_version=True | spline_en__traditional | 384 | 290 | não | 7.1236 | 9.4476 | 18.4832 | 3.3854 |
| remaster=False | spline_en__traditional | 7605 | 3731 | não | 6.9816 | 9.0846 | 18.2814 | 3.5503 |
| remaster=True | spline_en__traditional | 43 | 36 | não | 7.8698 | 10.4517 | 21.7228 | 6.9767 |
| remix=False | spline_en__traditional | 7555 | 3717 | não | 6.9801 | 9.0785 | 18.2279 | 3.5606 |
| remix=True | spline_en__traditional | 93 | 88 | não | 7.5109 | 10.1942 | 19.0393 | 4.3011 |
| live=False | spline_en__traditional | 7448 | 3717 | não | 6.9844 | 9.0902 | 18.4196 | 3.5983 |
| live=True | spline_en__traditional | 200 | 141 | não | 7.0661 | 9.1896 | 16.9825 | 2.5000 |
| acoustic=False | spline_en__traditional | 7630 | 3746 | não | 6.9859 | 9.0934 | 18.3187 | 3.5780 |
| acoustic=True | spline_en__traditional | 18 | 18 | sim | 7.2712 | 8.8451 | 15.5667 | 0.0000 |
| radio_edit=False | spline_en__traditional | 7636 | 3741 | não | 6.9846 | 9.0900 | 18.3137 | 3.5621 |
| radio_edit=True | spline_en__traditional | 12 | 12 | sim | 8.2123 | 10.7810 | 20.6831 | 8.3333 |
| mono_stereo=False | spline_en__traditional | 7645 | 3747 | não | 6.9879 | 9.0943 | 18.3229 | 3.5710 |
| mono_stereo=True | spline_en__traditional | 3 | 3 | sim | 3.6605 | 3.7057 | 4.3114 | 0.0000 |
| instrumental=False | spline_en__traditional | 7645 | 3748 | não | 6.9866 | 9.0933 | 18.3229 | 3.5710 |
| instrumental=True | spline_en__traditional | 3 | 3 | sim | 6.8492 | 7.8655 | 9.6964 | 0.0000 |
| demo=False | spline_en__traditional | 7631 | 3747 | não | 6.9950 | 9.1010 | 18.3472 | 3.5775 |
| demo=True | spline_en__traditional | 17 | 14 | sim | 3.1803 | 4.0403 | 7.8672 | 0.0000 |
| any_version=False | spline_en__deep | 7264 | 3648 | não | 7.0783 | 9.1585 | 18.1398 | 3.6206 |
| any_version=True | spline_en__deep | 384 | 290 | não | 7.2432 | 9.5995 | 18.4099 | 3.3854 |
| remaster=False | spline_en__deep | 7605 | 3731 | não | 7.0782 | 9.1702 | 18.1534 | 3.5897 |
| remaster=True | spline_en__deep | 43 | 36 | não | 8.5738 | 10.9444 | 21.5226 | 6.9767 |
| remix=False | spline_en__deep | 7555 | 3717 | não | 7.0780 | 9.1673 | 18.1518 | 3.6135 |
| remix=True | spline_en__deep | 93 | 88 | não | 7.7904 | 10.2428 | 18.5575 | 3.2258 |
| live=False | spline_en__deep | 7448 | 3717 | não | 7.0872 | 9.1774 | 18.1796 | 3.6386 |
| live=True | spline_en__deep | 200 | 141 | não | 7.0646 | 9.3208 | 17.4698 | 2.5000 |
| acoustic=False | spline_en__deep | 7630 | 3746 | não | 7.0861 | 9.1806 | 18.1710 | 3.6042 |
| acoustic=True | spline_en__deep | 18 | 18 | sim | 7.2912 | 9.4023 | 16.4535 | 5.5556 |
| radio_edit=False | spline_en__deep | 7636 | 3741 | não | 7.0854 | 9.1788 | 18.1685 | 3.6014 |
| radio_edit=True | spline_en__deep | 12 | 12 | sim | 7.8743 | 10.5591 | 19.5213 | 8.3333 |
| mono_stereo=False | spline_en__deep | 7645 | 3747 | não | 7.0885 | 9.1828 | 18.1732 | 3.6102 |
| mono_stereo=True | spline_en__deep | 3 | 3 | sim | 2.3750 | 2.6261 | 3.4559 | 0.0000 |
| instrumental=False | spline_en__deep | 7645 | 3748 | não | 7.0863 | 9.1812 | 18.1732 | 3.6102 |
| instrumental=True | spline_en__deep | 3 | 3 | sim | 8.0016 | 8.9602 | 11.4491 | 0.0000 |
| demo=False | spline_en__deep | 7631 | 3747 | não | 7.0955 | 9.1895 | 18.1785 | 3.6168 |
| demo=True | spline_en__deep | 17 | 14 | sim | 3.0990 | 3.9571 | 6.6571 | 0.0000 |
| any_version=False | spline_en__combined | 7264 | 3648 | não | 7.0802 | 9.1749 | 18.2215 | 3.6757 |
| any_version=True | spline_en__combined | 384 | 290 | não | 7.3865 | 9.7601 | 18.5289 | 3.6458 |
| remaster=False | spline_en__combined | 7605 | 3731 | não | 7.0889 | 9.1949 | 18.2214 | 3.6555 |
| remaster=True | spline_en__combined | 43 | 36 | não | 8.2762 | 10.8674 | 23.3635 | 6.9767 |
| remix=False | spline_en__combined | 7555 | 3717 | não | 7.0879 | 9.1887 | 18.2179 | 3.6664 |
| remix=True | spline_en__combined | 93 | 88 | não | 7.7255 | 10.4554 | 19.6362 | 4.3011 |
| live=False | spline_en__combined | 7448 | 3717 | não | 7.0883 | 9.1955 | 18.2946 | 3.7057 |
| live=True | spline_en__combined | 200 | 141 | não | 7.3673 | 9.5556 | 17.2253 | 2.5000 |
| acoustic=False | spline_en__combined | 7630 | 3746 | não | 7.0945 | 9.2047 | 18.2537 | 3.6697 |
| acoustic=True | spline_en__combined | 18 | 18 | sim | 7.5533 | 9.4112 | 17.6894 | 5.5556 |
| radio_edit=False | spline_en__combined | 7636 | 3741 | não | 7.0947 | 9.2034 | 18.2362 | 3.6668 |
| radio_edit=True | spline_en__combined | 12 | 12 | sim | 7.7057 | 10.2806 | 19.5665 | 8.3333 |
| mono_stereo=False | spline_en__combined | 7645 | 3747 | não | 7.0972 | 9.2067 | 18.2682 | 3.6756 |
| mono_stereo=True | spline_en__combined | 3 | 3 | sim | 2.9861 | 3.3816 | 4.2815 | 0.0000 |
| instrumental=False | spline_en__combined | 7645 | 3748 | não | 7.0952 | 9.2053 | 18.2682 | 3.6756 |
| instrumental=True | spline_en__combined | 3 | 3 | sim | 8.2017 | 8.8670 | 11.2321 | 0.0000 |
| demo=False | spline_en__combined | 7631 | 3747 | não | 7.1033 | 9.2132 | 18.2854 | 3.6823 |
| demo=True | spline_en__combined | 17 | 14 | sim | 3.6448 | 4.2900 | 7.4325 | 0.0000 |
| any_version=False | hist_gb__baseline | 7264 | 3648 | não | 6.9119 | 9.1933 | 18.8634 | 4.2263 |
| any_version=True | hist_gb__baseline | 384 | 290 | não | 6.7009 | 9.1312 | 18.0935 | 3.1250 |
| remaster=False | hist_gb__baseline | 7605 | 3731 | não | 6.9035 | 9.1900 | 18.7599 | 4.1683 |
| remaster=True | hist_gb__baseline | 43 | 36 | não | 6.5114 | 9.2278 | 18.1180 | 4.6512 |
| remix=False | hist_gb__baseline | 7555 | 3717 | não | 6.8912 | 9.1764 | 18.7777 | 4.1827 |
| remix=True | hist_gb__baseline | 93 | 88 | não | 7.7175 | 10.2522 | 18.5502 | 3.2258 |
| live=False | hist_gb__baseline | 7448 | 3717 | não | 6.9155 | 9.2043 | 18.8214 | 4.2025 |
| live=True | hist_gb__baseline | 200 | 141 | não | 6.3712 | 8.6470 | 16.2396 | 3.0000 |
| acoustic=False | hist_gb__baseline | 7630 | 3746 | não | 6.9011 | 9.1899 | 18.7832 | 4.1809 |
| acoustic=True | hist_gb__baseline | 18 | 18 | sim | 6.9795 | 9.3306 | 17.2729 | 0.0000 |
| radio_edit=False | hist_gb__baseline | 7636 | 3741 | não | 6.9000 | 9.1872 | 18.7084 | 4.1645 |
| radio_edit=True | hist_gb__baseline | 12 | 12 | sim | 7.7342 | 10.9418 | 22.1085 | 8.3333 |
| mono_stereo=False | hist_gb__baseline | 7645 | 3747 | não | 6.9008 | 9.1902 | 18.7599 | 4.1727 |
| mono_stereo=True | hist_gb__baseline | 3 | 3 | sim | 8.1011 | 9.0541 | 12.2675 | 0.0000 |
| instrumental=False | hist_gb__baseline | 7645 | 3748 | não | 6.9018 | 9.1906 | 18.7599 | 4.1727 |
| instrumental=True | hist_gb__baseline | 3 | 3 | sim | 5.7094 | 7.9376 | 12.3183 | 0.0000 |
| demo=False | hist_gb__baseline | 7631 | 3747 | não | 6.9086 | 9.1982 | 18.7821 | 4.1803 |
| demo=True | hist_gb__baseline | 17 | 14 | sim | 3.5962 | 4.2819 | 7.4729 | 0.0000 |
| any_version=False | hist_gb__traditional | 7264 | 3648 | não | 6.9852 | 9.2234 | 18.9439 | 4.1850 |
| any_version=True | hist_gb__traditional | 384 | 290 | não | 7.1171 | 9.4271 | 17.7559 | 3.6458 |
| remaster=False | hist_gb__traditional | 7605 | 3731 | não | 6.9943 | 9.2355 | 18.8568 | 4.1552 |
| remaster=True | hist_gb__traditional | 43 | 36 | não | 6.5514 | 8.9186 | 18.1015 | 4.6512 |
| remix=False | hist_gb__traditional | 7555 | 3717 | não | 6.9804 | 9.2204 | 18.8613 | 4.1694 |
| remix=True | hist_gb__traditional | 93 | 88 | não | 7.9230 | 10.2600 | 18.1823 | 3.2258 |
| live=False | hist_gb__traditional | 7448 | 3717 | não | 6.9953 | 9.2369 | 18.8875 | 4.1756 |
| live=True | hist_gb__traditional | 200 | 141 | não | 6.8644 | 9.1151 | 16.5550 | 3.5000 |
| acoustic=False | hist_gb__traditional | 7630 | 3746 | não | 6.9898 | 9.2316 | 18.8634 | 4.1678 |
| acoustic=True | hist_gb__traditional | 18 | 18 | sim | 7.8740 | 10.1120 | 17.8763 | 0.0000 |
| radio_edit=False | hist_gb__traditional | 7636 | 3741 | não | 6.9904 | 9.2295 | 18.8275 | 4.1383 |
| radio_edit=True | hist_gb__traditional | 12 | 12 | sim | 7.9192 | 11.6094 | 24.2646 | 16.6667 |
| mono_stereo=False | hist_gb__traditional | 7645 | 3747 | não | 6.9912 | 9.2333 | 18.8568 | 4.1596 |
| mono_stereo=True | hist_gb__traditional | 3 | 3 | sim | 8.6022 | 10.2493 | 14.4678 | 0.0000 |
| instrumental=False | hist_gb__traditional | 7645 | 3748 | não | 6.9925 | 9.2344 | 18.8568 | 4.1596 |
| instrumental=True | hist_gb__traditional | 3 | 3 | sim | 5.4195 | 7.2358 | 11.2035 | 0.0000 |
| demo=False | hist_gb__traditional | 7631 | 3747 | não | 6.9969 | 9.2407 | 18.8630 | 4.1672 |
| demo=True | hist_gb__traditional | 17 | 14 | sim | 4.7052 | 5.2938 | 8.4466 | 0.0000 |
| any_version=False | hist_gb__deep | 7264 | 3648 | não | 7.0346 | 9.2615 | 18.8117 | 4.1850 |
| any_version=True | hist_gb__deep | 384 | 290 | não | 7.1149 | 9.4787 | 17.9436 | 3.1250 |
| remaster=False | hist_gb__deep | 7605 | 3731 | não | 7.0394 | 9.2734 | 18.7626 | 4.1289 |
| remaster=True | hist_gb__deep | 43 | 36 | não | 6.9043 | 9.1227 | 16.9450 | 4.6512 |
| remix=False | hist_gb__deep | 7555 | 3717 | não | 7.0279 | 9.2606 | 18.7664 | 4.1562 |
| remix=True | hist_gb__deep | 93 | 88 | não | 7.9108 | 10.1968 | 18.2091 | 2.1505 |
| live=False | hist_gb__deep | 7448 | 3717 | não | 7.0435 | 9.2736 | 18.7801 | 4.1488 |
| live=True | hist_gb__deep | 200 | 141 | não | 6.8547 | 9.2325 | 16.6441 | 3.5000 |
| acoustic=False | hist_gb__deep | 7630 | 3746 | não | 7.0380 | 9.2723 | 18.7669 | 4.1415 |
| acoustic=True | hist_gb__deep | 18 | 18 | sim | 7.2745 | 9.3989 | 17.0073 | 0.0000 |
| radio_edit=False | hist_gb__deep | 7636 | 3741 | não | 7.0365 | 9.2669 | 18.7492 | 4.1252 |
| radio_edit=True | hist_gb__deep | 12 | 12 | sim | 8.3941 | 12.3411 | 24.6251 | 8.3333 |
| mono_stereo=False | hist_gb__deep | 7645 | 3747 | não | 7.0379 | 9.2721 | 18.7626 | 4.1334 |
| mono_stereo=True | hist_gb__deep | 3 | 3 | sim | 8.8291 | 10.2681 | 13.3887 | 0.0000 |
| instrumental=False | hist_gb__deep | 7645 | 3748 | não | 7.0386 | 9.2727 | 18.7626 | 4.1334 |
| instrumental=True | hist_gb__deep | 3 | 3 | sim | 7.0510 | 8.8277 | 13.4427 | 0.0000 |
| demo=False | hist_gb__deep | 7631 | 3747 | não | 7.0448 | 9.2800 | 18.7668 | 4.1410 |
| demo=True | hist_gb__deep | 17 | 14 | sim | 4.2736 | 4.8772 | 9.5793 | 0.0000 |
| any_version=False | hist_gb__combined | 7264 | 3648 | não | 7.0465 | 9.2480 | 18.7722 | 4.0474 |
| any_version=True | hist_gb__combined | 384 | 290 | não | 7.1888 | 9.4470 | 17.8828 | 2.8646 |
| remaster=False | hist_gb__combined | 7605 | 3731 | não | 7.0564 | 9.2610 | 18.6911 | 3.9974 |
| remaster=True | hist_gb__combined | 43 | 36 | não | 6.5747 | 8.7279 | 16.6554 | 2.3256 |
| remix=False | hist_gb__combined | 7555 | 3717 | não | 7.0391 | 9.2409 | 18.7051 | 4.0106 |
| remix=True | hist_gb__combined | 93 | 88 | não | 8.2419 | 10.5594 | 18.1164 | 2.1505 |
| live=False | hist_gb__combined | 7448 | 3717 | não | 7.0570 | 9.2614 | 18.7505 | 4.0011 |
| live=True | hist_gb__combined | 200 | 141 | não | 6.9320 | 9.1331 | 15.6399 | 3.5000 |
| acoustic=False | hist_gb__combined | 7630 | 3746 | não | 7.0540 | 9.2582 | 18.7144 | 3.9974 |
| acoustic=True | hist_gb__combined | 18 | 18 | sim | 6.8978 | 9.1925 | 17.3282 | 0.0000 |
| radio_edit=False | hist_gb__combined | 7636 | 3741 | não | 7.0522 | 9.2543 | 18.6834 | 3.9811 |
| radio_edit=True | hist_gb__combined | 12 | 12 | sim | 7.9828 | 11.3721 | 22.5516 | 8.3333 |
| mono_stereo=False | hist_gb__combined | 7645 | 3747 | não | 7.0534 | 9.2580 | 18.6911 | 3.9895 |
| mono_stereo=True | hist_gb__combined | 3 | 3 | sim | 7.8171 | 9.2608 | 12.5743 | 0.0000 |
| instrumental=False | hist_gb__combined | 7645 | 3748 | não | 7.0534 | 9.2580 | 18.6911 | 3.9895 |
| instrumental=True | hist_gb__combined | 3 | 3 | sim | 7.6525 | 9.4505 | 14.3483 | 0.0000 |
| demo=False | hist_gb__combined | 7631 | 3747 | não | 7.0590 | 9.2650 | 18.7125 | 3.9969 |
| demo=True | hist_gb__combined | 17 | 14 | sim | 4.6505 | 5.2475 | 8.1868 | 0.0000 |


## Interpretação e limites

Candidatos que satisfazem a regra operacional contra a referência V0.5 correspondente: nenhum. Isso autoriza discutir uma avaliação futura independente, não alterar o estudo encerrado ou reutilizar seu holdout como confirmação. O demonstrador continua com os modelos congelados e Tradicional predefinido.

Não foram calculados intervalos ou p-valores. Os resultados OOF continuam exploratórios, pois a motivação veio após o diagnóstico do holdout. As análises são associativas/preditivas, sem causalidade.

O diagnóstico V0.7 documenta 9,6363% de matching aceito na fonte Spotify e disponibilidade/aceite de letras não uniforme; esses denominadores são contexto histórico, não dados recarregados nesta rodada. Mudar o estimador não recupera faixas sem match, letras indisponíveis, gêneros/idiomas sub-representados, múltiplas versões ambíguas ou falhas semânticas de year/genre/flags. O alvo é um snapshot da faixa representante, não sucesso comercial futuro. O desenvolvimento continua sem valores acima de 80 e com poucos casos de alta popularidade. Não há garantia de desempenho fora deste suporte.

## Integridade, privacidade e reprodução

Preservados por SHA-256: 225 arquivos preexistentes públicos/pessoais, modelos V0.5 e entradas autorizadas. Preservados por tamanho/mtime_ns: 18222 arquivos de dados antigos; não foram abertos holdout/letras para essa auditoria. SHA-256 e metadados são verificações distintas. HEAD e stage inalterados; zero dados/modelos privados rastreados. Todas as escritas ficam nas saídas novas V0.8. Nenhuma alteração no demonstrador, dados, matching, flags, splits, embeddings, modelos ou resultados V0.5–V0.7.

Verificação real concluída: 40 pipelines carregados dos checkpoints reproduzem suas OOF com diferença máxima 0, tolerância absoluta 1e-10. Cobertura 7.648×8 completa, finita e única; alinhamento, inputs sem alvo, índices de cada transformação e ausência de sobreposição de artistas/composições conferidos.

CLI no ambiente existente (nenhuma dependência nova):

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 prepare
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 benchmark
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 run
.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.statistical_revision_v080 verify
```

Prepare/benchmark recusam sobrescrever uma execução existente; em retomada, executar somente run após verificar o selo. Não apagar checkpoints antigos. Predições e 40 modelos estão no diretório privado V0.8. Relatórios contêm somente agregados; CSVs continuam ignorados pela regra preexistente. Comandos de teste/lint e seus códigos de saída são registrados no run summary na entrega.
