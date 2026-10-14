# Modelagem final — desenvolvimento v0.5

Uma amostra comum de 7.648 composições; validação aninhada agrupada por artista, cinco folds externos e três internos. Alvo do holdout permanece selado. Previsões e modelos completos permanecem privados.

| Modelo | MAE | RMSE | R² OOF | Spearman | MAE treino | Tempo tuning s | Warnings |
|---|---|---|---|---|---|---|---|
| elastic_net__baseline | 7.09399 | 9.21382 | 0.52975 | 0.72697 | 6.91954 | 5.14859 | 0 |
| elastic_net__traditional | 7.06118 | 9.18831 | 0.53235 | 0.72783 | 6.77770 | 4.51442 | 0 |
| elastic_net__deep | 7.16245 | 9.28014 | 0.52296 | 0.72119 | 6.77945 | 6.47663 | 0 |
| elastic_net__combined | 7.16307 | 9.29546 | 0.52138 | 0.71896 | 6.68208 | 8.15501 | 0 |
| ridge__baseline | 7.09255 | 9.21147 | 0.52999 | 0.72715 | 6.90729 | 1.75627 | 0 |
| ridge__traditional | 7.05631 | 9.18663 | 0.53252 | 0.72802 | 6.76278 | 2.72858 | 0 |
| ridge__deep | 7.16965 | 9.28602 | 0.52235 | 0.72110 | 6.75201 | 4.20649 | 0 |
| ridge__combined | 7.16882 | 9.30412 | 0.52049 | 0.71931 | 6.64103 | 5.83410 | 0 |
| dummy__baseline | 10.72223 | 13.43644 | -0.00003 | -0.00442 | 10.72220 | 0.00000 | 0 |

## Resultados por fold

| Modelo | Fold | n | MAE | RMSE | R² | Spearman | MAE treino | Parâmetros | PCA LFM/MiniLM | Coef. não nulos | Warnings |
|---|---|---|---|---|---|---|---|---|---|---|---|
| elastic_net__baseline | 0 | 1529 | 7.30484 | 9.38405 | 0.51650 | 0.71075 | 6.84827 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 94 | 0 |
| ridge__baseline | 0 | 1529 | 7.30712 | 9.38909 | 0.51598 | 0.71044 | 6.84955 | {"alpha": 3} | {"lfm": null, "embedding": null} | 109 | 0 |
| dummy__baseline | 0 | 1529 | 10.73033 | 13.49565 | -0.00000 | — | 10.71974 | {"strategy": "mean"} | {"lfm": null, "embedding": null} | — | 0 |
| elastic_net__baseline | 1 | 1529 | 6.90957 | 9.02931 | 0.55220 | 0.74976 | 6.94619 | {"alpha": 0.001, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 101 | 0 |
| ridge__baseline | 1 | 1529 | 6.91391 | 9.03281 | 0.55185 | 0.74960 | 6.94786 | {"alpha": 1} | {"lfm": null, "embedding": null} | 109 | 0 |
| dummy__baseline | 1 | 1529 | 10.79636 | 13.49490 | -0.00027 | — | 10.70866 | {"strategy": "mean"} | {"lfm": null, "embedding": null} | — | 0 |
| elastic_net__baseline | 2 | 1528 | 6.97346 | 9.04256 | 0.53285 | 0.72566 | 6.94258 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 95 | 0 |
| ridge__baseline | 2 | 1528 | 6.97856 | 9.04523 | 0.53257 | 0.72548 | 6.93352 | {"alpha": 1} | {"lfm": null, "embedding": null} | 110 | 0 |
| dummy__baseline | 2 | 1528 | 10.58623 | 13.23009 | -0.00000 | — | 10.75587 | {"strategy": "mean"} | {"lfm": null, "embedding": null} | — | 0 |
| elastic_net__baseline | 3 | 1529 | 7.13661 | 9.25731 | 0.53247 | 0.72870 | 6.91160 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 97 | 0 |
| ridge__baseline | 3 | 1529 | 7.13673 | 9.25225 | 0.53298 | 0.72949 | 6.90080 | {"alpha": 1} | {"lfm": null, "embedding": null} | 110 | 0 |
| dummy__baseline | 3 | 1529 | 10.83780 | 13.53974 | -0.00014 | — | 10.69078 | {"strategy": "mean"} | {"lfm": null, "embedding": null} | — | 0 |
| elastic_net__baseline | 4 | 1533 | 7.14525 | 9.34929 | 0.51459 | 0.71937 | 6.94908 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 81 | 0 |
| ridge__baseline | 4 | 1533 | 7.12627 | 9.33171 | 0.51642 | 0.71968 | 6.90469 | {"alpha": 3} | {"lfm": null, "embedding": null} | 109 | 0 |
| dummy__baseline | 4 | 1533 | 10.66051 | 13.41951 | -0.00005 | — | 10.73594 | {"strategy": "mean"} | {"lfm": null, "embedding": null} | — | 0 |
| elastic_net__traditional | 0 | 1529 | 7.20719 | 9.31231 | 0.52387 | 0.71433 | 6.71529 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": 77, "embedding": null} | 169 | 0 |
| ridge__traditional | 0 | 1529 | 7.20704 | 9.32267 | 0.52281 | 0.71319 | 6.71772 | {"alpha": 3} | {"lfm": 77, "embedding": null} | 186 | 0 |
| elastic_net__traditional | 1 | 1529 | 6.88415 | 9.02513 | 0.55261 | 0.75030 | 6.79540 | {"alpha": 0.001, "l1_ratio": 0.95} | {"lfm": 77, "embedding": null} | 179 | 0 |
| ridge__traditional | 1 | 1529 | 6.89155 | 9.03025 | 0.55210 | 0.75030 | 6.79283 | {"alpha": 0.3} | {"lfm": 77, "embedding": null} | 186 | 0 |
| elastic_net__traditional | 2 | 1528 | 6.94962 | 9.02697 | 0.53446 | 0.72636 | 6.85485 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": 76, "embedding": null} | 153 | 0 |
| ridge__traditional | 2 | 1528 | 6.92295 | 8.99848 | 0.53739 | 0.72860 | 6.80282 | {"alpha": 3} | {"lfm": 76, "embedding": null} | 186 | 0 |
| elastic_net__traditional | 3 | 1529 | 7.10784 | 9.21234 | 0.53700 | 0.73131 | 6.76300 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": 77, "embedding": null} | 174 | 0 |
| ridge__traditional | 3 | 1529 | 7.11153 | 9.22271 | 0.53596 | 0.73101 | 6.75188 | {"alpha": 1} | {"lfm": 77, "embedding": null} | 187 | 0 |
| elastic_net__traditional | 4 | 1533 | 7.15677 | 9.35893 | 0.51359 | 0.71547 | 6.75993 | {"alpha": 0.003, "l1_ratio": 0.8} | {"lfm": 76, "embedding": null} | 173 | 0 |
| ridge__traditional | 4 | 1533 | 7.14812 | 9.35266 | 0.51424 | 0.71621 | 6.74863 | {"alpha": 3} | {"lfm": 76, "embedding": null} | 185 | 0 |
| elastic_net__deep | 0 | 1529 | 7.34282 | 9.41407 | 0.51341 | 0.70733 | 6.70314 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": 184} | 273 | 0 |
| ridge__deep | 0 | 1529 | 7.34960 | 9.42931 | 0.51183 | 0.70639 | 6.69495 | {"alpha": 1} | {"lfm": null, "embedding": 184} | 293 | 0 |
| elastic_net__deep | 1 | 1529 | 7.01618 | 9.14002 | 0.54115 | 0.74143 | 6.79225 | {"alpha": 0.001, "l1_ratio": 0.95} | {"lfm": null, "embedding": 185} | 285 | 0 |
| ridge__deep | 1 | 1529 | 7.02291 | 9.14520 | 0.54063 | 0.74100 | 6.78806 | {"alpha": 0.1} | {"lfm": null, "embedding": 185} | 294 | 0 |
| elastic_net__deep | 2 | 1528 | 6.96821 | 9.06716 | 0.53030 | 0.72406 | 6.85957 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": null, "embedding": 184} | 256 | 0 |
| ridge__deep | 2 | 1528 | 6.99652 | 9.07760 | 0.52922 | 0.72405 | 6.79169 | {"alpha": 1} | {"lfm": null, "embedding": 184} | 294 | 0 |
| elastic_net__deep | 3 | 1529 | 7.18549 | 9.27670 | 0.53051 | 0.72765 | 6.76640 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": 185} | 279 | 0 |
| ridge__deep | 3 | 1529 | 7.19167 | 9.27300 | 0.53088 | 0.72818 | 6.75250 | {"alpha": 1} | {"lfm": null, "embedding": 185} | 295 | 0 |
| elastic_net__deep | 4 | 1533 | 7.29909 | 9.49510 | 0.49934 | 0.70461 | 6.77587 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": null, "embedding": 184} | 255 | 0 |
| ridge__deep | 4 | 1533 | 7.28712 | 9.49738 | 0.49910 | 0.70356 | 6.73283 | {"alpha": 3} | {"lfm": null, "embedding": 184} | 293 | 0 |
| elastic_net__combined | 0 | 1529 | 7.33831 | 9.44876 | 0.50981 | 0.70153 | 6.65053 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": 77, "embedding": 184} | 323 | 0 |
| ridge__combined | 0 | 1529 | 7.34075 | 9.46363 | 0.50827 | 0.70318 | 6.59224 | {"alpha": 3} | {"lfm": 77, "embedding": 184} | 370 | 0 |
| elastic_net__combined | 1 | 1529 | 7.01012 | 9.13868 | 0.54128 | 0.74009 | 6.68795 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": 77, "embedding": 185} | 350 | 0 |
| ridge__combined | 1 | 1529 | 7.01246 | 9.14859 | 0.54029 | 0.73954 | 6.67291 | {"alpha": 0.3} | {"lfm": 77, "embedding": 185} | 371 | 0 |
| elastic_net__combined | 2 | 1528 | 6.94977 | 9.06681 | 0.53034 | 0.72277 | 6.75545 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": 76, "embedding": 184} | 323 | 0 |
| ridge__combined | 2 | 1528 | 6.97431 | 9.07645 | 0.52934 | 0.72485 | 6.68597 | {"alpha": 1} | {"lfm": 76, "embedding": 184} | 370 | 0 |
| elastic_net__combined | 3 | 1529 | 7.18153 | 9.31193 | 0.52694 | 0.72487 | 6.64914 | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": 77, "embedding": 185} | 352 | 0 |
| ridge__combined | 3 | 1529 | 7.19384 | 9.32693 | 0.52541 | 0.72441 | 6.63515 | {"alpha": 1} | {"lfm": 77, "embedding": 185} | 372 | 0 |
| elastic_net__combined | 4 | 1533 | 7.33505 | 9.50268 | 0.49854 | 0.70373 | 6.66732 | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": 76, "embedding": 184} | 322 | 0 |
| ridge__combined | 4 | 1533 | 7.32223 | 9.49687 | 0.49915 | 0.70352 | 6.61884 | {"alpha": 3} | {"lfm": 76, "embedding": 184} | 369 | 0 |

## Incremento versus Baseline do mesmo algoritmo

| Modelo | ΔMAE | IC95% ΔMAE | ΔRMSE | IC95% ΔRMSE |
|---|---|---|---|---|
| elastic_net__traditional | -0.03281 | [-0.07723, 0.01431] | -0.02551 | [-0.07770, 0.02859] |
| elastic_net__deep | 0.06847 | [0.02310, 0.11199] | 0.06632 | [0.01837, 0.11364] |
| elastic_net__combined | 0.06909 | [0.01174, 0.12633] | 0.08164 | [0.01972, 0.14655] |
| ridge__traditional | -0.03624 | [-0.08108, 0.01028] | -0.02483 | [-0.07715, 0.02896] |
| ridge__deep | 0.07710 | [0.03198, 0.12022] | 0.07456 | [0.02648, 0.12134] |
| ridge__combined | 0.07627 | [0.01820, 0.13034] | 0.09265 | [0.02945, 0.15643] |

Diferenças negativas favorecem o bloco textual. ICs descritivos por 2.000 bootstraps pareados por artista; condicionam-se às predições OOF e não incluem toda a incerteza de repetir o treinamento. Desenvolvimento não é confirmação independente das escolhas dos pilotos.

Candidato principal da demonstração: `elastic_net__traditional` pelo menor MAE OOF Elastic Net. Todos os quatro Elastic Net, quatro Ridge e Dummy foram preservados. Grades e representações permaneceram congeladas.

## Modelos completos congelados

| Modelo | Parâmetros | PCA | Coef. não nulos | Tempo s |
|---|---|---|---|---|
| elastic_net__baseline | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": null, "embedding": null} | 93 | 0.83 |
| ridge__baseline | {"alpha": 3} | {"lfm": null, "embedding": null} | 110 | 0.54 |
| elastic_net__traditional | {"alpha": 0.003, "l1_ratio": 0.95} | {"lfm": 77, "embedding": null} | 171 | 1.24 |
| ridge__traditional | {"alpha": 1} | {"lfm": 77, "embedding": null} | 187 | 0.92 |
| elastic_net__deep | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": null, "embedding": 185} | 250 | 1.82 |
| ridge__deep | {"alpha": 3} | {"lfm": null, "embedding": 185} | 295 | 1.37 |
| elastic_net__combined | {"alpha": 0.01, "l1_ratio": 0.95} | {"lfm": 77, "embedding": 185} | 323 | 2.50 |
| ridge__combined | {"alpha": 3} | {"lfm": 77, "embedding": 185} | 372 | 1.87 |
| dummy__baseline | {"strategy": "mean"} | {} | — | 0.00 |

## Diagnósticos agregados

### period (n≥30)

| Categoria | Modelo | n | MAE | RMSE | Resíduo médio |
|---|---|---|---|---|---|
| 2000–2009 | elastic_net__baseline | 2087 | 7.1047 | 9.2628 | 0.2813 |
| 2000–2009 | elastic_net__traditional | 2087 | 7.0111 | 9.1546 | 0.2068 |
| 2000–2009 | elastic_net__deep | 2087 | 7.1041 | 9.2823 | 0.2552 |
| 2000–2009 | elastic_net__combined | 2087 | 7.0722 | 9.2506 | 0.1773 |
| 2000–2009 | ridge__baseline | 2087 | 7.1095 | 9.2602 | 0.2895 |
| 2000–2009 | ridge__traditional | 2087 | 7.0017 | 9.1532 | 0.2192 |
| 2000–2009 | ridge__deep | 2087 | 7.1384 | 9.3070 | 0.2748 |
| 2000–2009 | ridge__combined | 2087 | 7.1155 | 9.2947 | 0.2022 |
| 2000–2009 | dummy__baseline | 2087 | 10.5769 | 12.7911 | -6.0542 |
| 2010–2019 | elastic_net__baseline | 5312 | 7.0023 | 8.9947 | -0.0915 |
| 2010–2019 | elastic_net__traditional | 5312 | 6.9855 | 8.9799 | -0.0685 |
| 2010–2019 | elastic_net__deep | 5312 | 7.0905 | 9.0687 | -0.0916 |
| 2010–2019 | elastic_net__combined | 5312 | 7.0952 | 9.0911 | -0.0703 |
| 2010–2019 | ridge__baseline | 5312 | 6.9970 | 8.9872 | -0.0986 |
| 2010–2019 | ridge__traditional | 5312 | 6.9832 | 8.9766 | -0.0702 |
| 2010–2019 | ridge__deep | 5312 | 7.0850 | 9.0605 | -0.0939 |
| 2010–2019 | ridge__combined | 5312 | 7.0862 | 9.0795 | -0.0764 |
| 2010–2019 | dummy__baseline | 5312 | 10.6598 | 13.5218 | 2.1310 |
| 2020 ou posterior | elastic_net__baseline | 249 | 8.9598 | 12.7443 | -0.6544 |
| 2020 ou posterior | elastic_net__traditional | 249 | 9.0945 | 13.0529 | -0.8913 |
| 2020 ou posterior | elastic_net__deep | 249 | 9.1875 | 12.9823 | -0.6495 |
| 2020 ou posterior | elastic_net__combined | 249 | 9.3731 | 13.1740 | -0.7787 |
| 2020 ou posterior | ridge__baseline | 249 | 8.9890 | 12.8208 | -0.6715 |
| 2020 ou posterior | ridge__traditional | 249 | 9.0730 | 13.0729 | -0.8448 |
| 2020 ou posterior | ridge__deep | 249 | 9.2381 | 13.0855 | -0.5908 |
| 2020 ou posterior | ridge__combined | 249 | 9.3779 | 13.2716 | -0.7104 |
| 2020 ou posterior | dummy__baseline | 249 | 13.2717 | 16.5315 | 5.2838 |

### genre (n≥30)

| Categoria | Modelo | n | MAE | RMSE | Resíduo médio |
|---|---|---|---|---|---|
| acoustic | elastic_net__baseline | 206 | 8.1138 | 9.9466 | -0.1421 |
| acoustic | elastic_net__traditional | 206 | 8.0146 | 9.7755 | -0.1772 |
| acoustic | elastic_net__deep | 206 | 8.1943 | 10.0193 | -0.2597 |
| acoustic | elastic_net__combined | 206 | 8.0476 | 9.8563 | -0.3618 |
| acoustic | ridge__baseline | 206 | 8.1105 | 9.9435 | 0.0054 |
| acoustic | ridge__traditional | 206 | 7.9871 | 9.7724 | -0.0525 |
| acoustic | ridge__deep | 206 | 8.1810 | 10.0166 | -0.0378 |
| acoustic | ridge__combined | 206 | 8.0082 | 9.8594 | -0.0690 |
| acoustic | dummy__baseline | 206 | 9.5585 | 11.6715 | -3.1715 |
| alt-rock | elastic_net__baseline | 398 | 5.8186 | 7.5406 | 0.1665 |
| alt-rock | elastic_net__traditional | 398 | 5.8542 | 7.5540 | 0.1623 |
| alt-rock | elastic_net__deep | 398 | 5.9022 | 7.6664 | 0.2634 |
| alt-rock | elastic_net__combined | 398 | 5.9473 | 7.7009 | 0.3086 |
| alt-rock | ridge__baseline | 398 | 5.8197 | 7.5336 | 0.0958 |
| alt-rock | ridge__traditional | 398 | 5.8507 | 7.5473 | 0.0946 |
| alt-rock | ridge__deep | 398 | 5.9050 | 7.6616 | 0.1429 |
| alt-rock | ridge__combined | 398 | 5.9672 | 7.7079 | 0.1567 |
| alt-rock | dummy__baseline | 398 | 10.2125 | 12.8659 | 9.8572 |
| ambient | elastic_net__baseline | 62 | 7.9642 | 9.8704 | 0.1168 |
| ambient | elastic_net__traditional | 62 | 7.5775 | 9.3672 | 0.3432 |
| ambient | elastic_net__deep | 62 | 7.6028 | 9.3579 | 0.6990 |
| ambient | elastic_net__combined | 62 | 7.2677 | 8.9554 | 0.4569 |
| ambient | ridge__baseline | 62 | 8.1093 | 10.0207 | 0.1596 |
| ambient | ridge__traditional | 62 | 7.8327 | 9.6409 | 0.2382 |
| ambient | ridge__deep | 62 | 7.8641 | 9.6472 | 0.5068 |
| ambient | ridge__combined | 62 | 7.5988 | 9.3488 | 0.4952 |
| ambient | dummy__baseline | 62 | 8.9042 | 11.0140 | -0.5089 |
| black-metal | elastic_net__baseline | 231 | 6.4317 | 7.9523 | -0.1382 |
| black-metal | elastic_net__traditional | 231 | 6.4507 | 7.9167 | -0.1443 |
| black-metal | elastic_net__deep | 231 | 6.4740 | 7.9922 | -0.1659 |
| black-metal | elastic_net__combined | 231 | 6.4894 | 8.0207 | -0.2735 |
| black-metal | ridge__baseline | 231 | 6.4216 | 7.9503 | -0.0543 |
| black-metal | ridge__traditional | 231 | 6.4383 | 7.9134 | -0.0582 |
| black-metal | ridge__deep | 231 | 6.4612 | 8.0045 | -0.0206 |
| black-metal | ridge__combined | 231 | 6.4894 | 8.0634 | -0.0296 |
| black-metal | dummy__baseline | 231 | 12.7134 | 14.1880 | -11.8616 |
| blues | elastic_net__baseline | 186 | 6.7134 | 8.6147 | 0.0610 |
| blues | elastic_net__traditional | 186 | 6.7178 | 8.7265 | -0.1462 |
| blues | elastic_net__deep | 186 | 6.7802 | 8.7976 | -0.0858 |
| blues | elastic_net__combined | 186 | 6.8293 | 8.8276 | -0.2444 |
| blues | ridge__baseline | 186 | 6.7670 | 8.6782 | -0.0277 |
| blues | ridge__traditional | 186 | 6.7779 | 8.8098 | -0.0887 |
| blues | ridge__deep | 186 | 6.8542 | 8.8987 | -0.1031 |
| blues | ridge__combined | 186 | 6.9259 | 8.9511 | -0.2176 |
| blues | dummy__baseline | 186 | 7.6495 | 9.3000 | -2.6030 |
| chill | elastic_net__baseline | 171 | 8.2911 | 10.3234 | 0.2644 |
| chill | elastic_net__traditional | 171 | 7.9912 | 9.9561 | 0.1754 |
| chill | elastic_net__deep | 171 | 8.2351 | 10.0973 | 0.1807 |
| chill | elastic_net__combined | 171 | 8.1285 | 9.8987 | 0.2941 |
| chill | ridge__baseline | 171 | 8.2946 | 10.3291 | 0.1268 |
| chill | ridge__traditional | 171 | 8.0217 | 9.9750 | 0.0520 |
| chill | ridge__deep | 171 | 8.2762 | 10.1164 | -0.0275 |
| chill | ridge__combined | 171 | 8.1986 | 9.9180 | -0.0247 |
| chill | dummy__baseline | 171 | 11.3933 | 13.8739 | 5.7601 |
| club | elastic_net__baseline | 38 | 12.0697 | 13.6067 | 1.0533 |
| club | elastic_net__traditional | 38 | 12.0130 | 13.4658 | 0.8940 |
| club | elastic_net__deep | 38 | 11.7456 | 13.4063 | 0.4852 |
| club | elastic_net__combined | 38 | 11.8278 | 13.5544 | 0.4685 |
| club | ridge__baseline | 38 | 12.2795 | 13.7946 | 1.8749 |
| club | ridge__traditional | 38 | 12.1101 | 13.5739 | 1.7598 |
| club | ridge__deep | 38 | 11.8053 | 13.4020 | 1.6594 |
| club | ridge__combined | 38 | 11.7560 | 13.5262 | 1.7730 |
| club | dummy__baseline | 38 | 9.6940 | 12.1634 | -3.2414 |
| country | elastic_net__baseline | 363 | 7.6786 | 10.1424 | 0.0502 |
| country | elastic_net__traditional | 363 | 7.5948 | 10.0387 | 0.1458 |
| country | elastic_net__deep | 363 | 7.7855 | 10.2474 | 0.1769 |
| country | elastic_net__combined | 363 | 7.6797 | 10.1579 | 0.2427 |
| country | ridge__baseline | 363 | 7.6766 | 10.1274 | -0.0130 |
| country | ridge__traditional | 363 | 7.6187 | 10.0464 | 0.0530 |
| country | ridge__deep | 363 | 7.8094 | 10.2389 | 0.0359 |
| country | ridge__combined | 363 | 7.7085 | 10.1487 | 0.0704 |
| country | dummy__baseline | 363 | 9.7710 | 13.1138 | 6.2703 |
| dance | elastic_net__baseline | 216 | 8.0252 | 10.2852 | 0.1007 |
| dance | elastic_net__traditional | 216 | 7.9242 | 10.2860 | 0.1524 |
| dance | elastic_net__deep | 216 | 8.1954 | 10.4254 | 0.1933 |
| dance | elastic_net__combined | 216 | 8.0132 | 10.3775 | 0.3613 |
| dance | ridge__baseline | 216 | 8.0127 | 10.2577 | 0.0266 |
| dance | ridge__traditional | 216 | 7.9140 | 10.2501 | 0.0491 |
| dance | ridge__deep | 216 | 8.1956 | 10.3910 | -0.0109 |
| dance | ridge__combined | 216 | 8.0344 | 10.3177 | 0.0835 |
| dance | dummy__baseline | 216 | 13.8965 | 18.0124 | 12.1098 |
| dancehall | elastic_net__baseline | 72 | 7.6603 | 9.2606 | -0.5178 |
| dancehall | elastic_net__traditional | 72 | 7.9280 | 9.5383 | -0.5588 |
| dancehall | elastic_net__deep | 72 | 7.4920 | 8.8590 | -0.6349 |
| dancehall | elastic_net__combined | 72 | 7.8845 | 9.3082 | -0.9125 |
| dancehall | ridge__baseline | 72 | 7.5580 | 9.1517 | -0.2041 |
| dancehall | ridge__traditional | 72 | 7.8537 | 9.5019 | -0.1680 |
| dancehall | ridge__deep | 72 | 7.3379 | 8.7841 | -0.0077 |
| dancehall | ridge__combined | 72 | 7.6860 | 9.2020 | -0.0524 |
| dancehall | dummy__baseline | 72 | 9.2359 | 10.9722 | -2.6148 |
| death-metal | elastic_net__baseline | 364 | 6.5380 | 8.0420 | -0.0055 |
| death-metal | elastic_net__traditional | 364 | 6.4637 | 7.9927 | 0.0277 |
| death-metal | elastic_net__deep | 364 | 6.7256 | 8.2210 | 0.0088 |
| death-metal | elastic_net__combined | 364 | 6.7468 | 8.2292 | -0.0074 |
| death-metal | ridge__baseline | 364 | 6.5338 | 8.0464 | 0.0251 |
| death-metal | ridge__traditional | 364 | 6.4738 | 8.0160 | -0.0126 |
| death-metal | ridge__deep | 364 | 6.7335 | 8.2422 | -0.0172 |
| death-metal | ridge__combined | 364 | 6.7800 | 8.2836 | -0.0827 |
| death-metal | dummy__baseline | 364 | 8.5679 | 10.2615 | -6.3023 |
| deep-house | elastic_net__baseline | 55 | 7.4533 | 9.8751 | 0.4698 |
| deep-house | elastic_net__traditional | 55 | 7.9598 | 10.1915 | 0.2238 |
| deep-house | elastic_net__deep | 55 | 8.2503 | 10.2303 | -0.0652 |
| deep-house | elastic_net__combined | 55 | 8.4595 | 10.4786 | 0.1337 |
| deep-house | ridge__baseline | 55 | 7.5077 | 9.8722 | 0.2160 |
| deep-house | ridge__traditional | 55 | 7.9891 | 10.2707 | 0.2817 |
| deep-house | ridge__deep | 55 | 8.2099 | 10.3614 | 0.3022 |
| deep-house | ridge__combined | 55 | 8.4591 | 10.6165 | 0.4178 |
| deep-house | dummy__baseline | 55 | 7.9505 | 10.6434 | 2.5299 |
| disco | elastic_net__baseline | 83 | 6.8480 | 9.0724 | -0.7315 |
| disco | elastic_net__traditional | 83 | 6.7896 | 9.0922 | -0.5624 |
| disco | elastic_net__deep | 83 | 6.8448 | 9.1738 | -0.9482 |
| disco | elastic_net__combined | 83 | 6.7952 | 9.0832 | -1.2001 |
| disco | ridge__baseline | 83 | 6.7955 | 9.0507 | -0.2842 |
| disco | ridge__traditional | 83 | 6.7531 | 9.0930 | -0.3278 |
| disco | ridge__deep | 83 | 6.7665 | 9.1922 | -0.3618 |
| disco | ridge__combined | 83 | 6.6682 | 9.0607 | -0.4575 |
| disco | dummy__baseline | 83 | 12.4605 | 14.5252 | -10.8208 |
| dub | elastic_net__baseline | 51 | 6.9718 | 8.5849 | -0.0851 |
| dub | elastic_net__traditional | 51 | 7.5059 | 9.1011 | -0.2453 |
| dub | elastic_net__deep | 51 | 6.8516 | 8.4526 | 0.1891 |
| dub | elastic_net__combined | 51 | 6.9727 | 8.5959 | -0.1348 |
| dub | ridge__baseline | 51 | 7.0468 | 8.7194 | -0.2105 |
| dub | ridge__traditional | 51 | 7.6574 | 9.2447 | -0.1035 |
| dub | ridge__deep | 51 | 6.9274 | 8.5727 | 0.0982 |
| dub | ridge__combined | 51 | 7.1704 | 8.8954 | -0.0378 |
| dub | dummy__baseline | 51 | 8.7043 | 10.6899 | -0.4544 |
| edm | elastic_net__baseline | 83 | 7.3708 | 10.6412 | 0.3353 |
| edm | elastic_net__traditional | 83 | 7.5957 | 10.7723 | 0.2491 |
| edm | elastic_net__deep | 83 | 7.9100 | 11.1572 | 0.6539 |
| edm | elastic_net__combined | 83 | 8.2237 | 11.4524 | 0.5719 |
| edm | ridge__baseline | 83 | 7.3106 | 10.6041 | 0.0934 |
| edm | ridge__traditional | 83 | 7.5316 | 10.7697 | -0.1213 |
| edm | ridge__deep | 83 | 7.8099 | 11.1003 | 0.1484 |
| edm | ridge__combined | 83 | 8.0109 | 11.3600 | -0.1710 |
| edm | dummy__baseline | 83 | 12.8571 | 15.3045 | 9.8270 |
| electro | elastic_net__baseline | 112 | 6.9542 | 9.4045 | 0.3527 |
| electro | elastic_net__traditional | 112 | 7.1225 | 9.7216 | 0.2487 |
| electro | elastic_net__deep | 112 | 6.7600 | 9.5134 | 0.4213 |
| electro | elastic_net__combined | 112 | 6.8442 | 9.6254 | 0.5151 |
| electro | ridge__baseline | 112 | 6.9778 | 9.4056 | 0.1714 |
| electro | ridge__traditional | 112 | 7.1768 | 9.7186 | 0.0109 |
| electro | ridge__deep | 112 | 6.8432 | 9.5396 | 0.0023 |
| electro | ridge__combined | 112 | 6.9729 | 9.7060 | -0.1004 |
| electro | dummy__baseline | 112 | 13.5094 | 15.9461 | 9.3903 |
| electronic | elastic_net__baseline | 69 | 5.0126 | 6.3054 | -0.2021 |
| electronic | elastic_net__traditional | 69 | 5.1513 | 6.4790 | -0.1500 |
| electronic | elastic_net__deep | 69 | 5.1196 | 6.3278 | 0.1613 |
| electronic | elastic_net__combined | 69 | 5.2927 | 6.5016 | -0.0670 |
| electronic | ridge__baseline | 69 | 5.0405 | 6.4117 | -0.0880 |
| electronic | ridge__traditional | 69 | 5.1709 | 6.5254 | -0.0323 |
| electronic | ridge__deep | 69 | 5.1759 | 6.4623 | 0.0496 |
| electronic | ridge__combined | 69 | 5.3143 | 6.5851 | 0.1334 |
| electronic | dummy__baseline | 69 | 7.8052 | 9.4884 | -1.7117 |
| emo | elastic_net__baseline | 515 | 7.1894 | 9.4787 | 0.0560 |
| emo | elastic_net__traditional | 515 | 6.9166 | 9.2242 | 0.1122 |
| emo | elastic_net__deep | 515 | 7.0735 | 9.4117 | 0.0919 |
| emo | elastic_net__combined | 515 | 6.9676 | 9.2844 | 0.1831 |
| emo | ridge__baseline | 515 | 7.1968 | 9.4792 | 0.0090 |
| emo | ridge__traditional | 515 | 6.9269 | 9.2291 | 0.0512 |
| emo | ridge__deep | 515 | 7.0992 | 9.4296 | 0.0230 |
| emo | ridge__combined | 515 | 7.0138 | 9.3199 | 0.0951 |
| emo | dummy__baseline | 515 | 8.9609 | 11.4303 | 0.0855 |
| folk | elastic_net__baseline | 281 | 6.8376 | 8.9212 | 0.1699 |
| folk | elastic_net__traditional | 281 | 6.8215 | 9.1629 | 0.2583 |
| folk | elastic_net__deep | 281 | 6.9517 | 8.9919 | 0.1850 |
| folk | elastic_net__combined | 281 | 6.9695 | 9.1473 | 0.2518 |
| folk | ridge__baseline | 281 | 6.8488 | 8.9265 | 0.0707 |
| folk | ridge__traditional | 281 | 6.8228 | 9.1736 | 0.1607 |
| folk | ridge__deep | 281 | 6.9556 | 8.9978 | 0.0104 |
| folk | ridge__combined | 281 | 7.0123 | 9.1881 | 0.0330 |
| folk | dummy__baseline | 281 | 10.1689 | 12.9198 | 7.5729 |
| french | elastic_net__baseline | 50 | 5.9722 | 7.2813 | 0.9606 |
| french | elastic_net__traditional | 50 | 6.2372 | 7.5819 | 0.9978 |
| french | elastic_net__deep | 50 | 6.4609 | 7.8096 | 1.1363 |
| french | elastic_net__combined | 50 | 6.7907 | 8.2070 | 1.5491 |
| french | ridge__baseline | 50 | 5.7271 | 7.0645 | 0.3133 |
| french | ridge__traditional | 50 | 6.1383 | 7.4402 | 0.4705 |
| french | ridge__deep | 50 | 6.2587 | 7.5467 | 0.3235 |
| french | ridge__combined | 50 | 6.6326 | 7.9438 | 0.4303 |
| french | dummy__baseline | 50 | 8.1702 | 9.8114 | 2.2105 |
| funk | elastic_net__baseline | 153 | 8.3211 | 10.6677 | 0.2577 |
| funk | elastic_net__traditional | 153 | 8.1403 | 10.5043 | 0.3423 |
| funk | elastic_net__deep | 153 | 8.0846 | 10.5394 | 0.2661 |
| funk | elastic_net__combined | 153 | 8.1051 | 10.5517 | 0.4344 |
| funk | ridge__baseline | 153 | 8.3838 | 10.6981 | 0.0948 |
| funk | ridge__traditional | 153 | 8.1860 | 10.5262 | 0.1697 |
| funk | ridge__deep | 153 | 8.1763 | 10.5929 | 0.0712 |
| funk | ridge__combined | 153 | 8.1831 | 10.6189 | 0.0741 |
| funk | dummy__baseline | 153 | 8.5504 | 10.5334 | -0.9166 |
| garage | elastic_net__baseline | 275 | 7.3127 | 9.1820 | 0.2108 |
| garage | elastic_net__traditional | 275 | 7.3631 | 9.1664 | 0.0841 |
| garage | elastic_net__deep | 275 | 7.1897 | 9.1729 | 0.1594 |
| garage | elastic_net__combined | 275 | 7.2212 | 9.1395 | 0.1136 |
| garage | ridge__baseline | 275 | 7.3190 | 9.1613 | 0.0659 |
| garage | ridge__traditional | 275 | 7.3822 | 9.1716 | -0.0150 |
| garage | ridge__deep | 275 | 7.2041 | 9.1857 | -0.0132 |
| garage | ridge__combined | 275 | 7.2592 | 9.1577 | -0.1167 |
| garage | dummy__baseline | 275 | 7.9941 | 10.1133 | -1.1683 |
| german | elastic_net__baseline | 69 | 6.4183 | 8.3683 | 0.5466 |
| german | elastic_net__traditional | 69 | 7.1256 | 9.6098 | 0.6388 |
| german | elastic_net__deep | 69 | 6.6263 | 8.6280 | 0.7965 |
| german | elastic_net__combined | 69 | 7.1374 | 9.6264 | 1.2116 |
| german | ridge__baseline | 69 | 6.5125 | 8.4306 | 0.1181 |
| german | ridge__traditional | 69 | 7.0553 | 9.5634 | 0.2773 |
| german | ridge__deep | 69 | 6.6119 | 8.5862 | 0.1886 |
| german | ridge__combined | 69 | 7.2331 | 9.6997 | 0.4321 |
| german | dummy__baseline | 69 | 8.5085 | 10.5240 | 0.4805 |
| gospel | elastic_net__baseline | 50 | 8.0957 | 10.1617 | 0.2729 |
| gospel | elastic_net__traditional | 50 | 8.0844 | 10.2587 | 0.0161 |
| gospel | elastic_net__deep | 50 | 7.4242 | 9.2978 | -0.1290 |
| gospel | elastic_net__combined | 50 | 7.5961 | 9.5880 | -0.0387 |
| gospel | ridge__baseline | 50 | 8.1278 | 10.1380 | -0.1138 |
| gospel | ridge__traditional | 50 | 8.1129 | 10.2539 | -0.1275 |
| gospel | ridge__deep | 50 | 7.4245 | 9.2048 | -0.1949 |
| gospel | ridge__combined | 50 | 7.5734 | 9.4943 | -0.1371 |
| gospel | dummy__baseline | 50 | 9.1923 | 11.1425 | -4.3420 |
| goth | elastic_net__baseline | 185 | 7.4085 | 9.2004 | -0.2211 |
| goth | elastic_net__traditional | 185 | 7.4119 | 9.1719 | -0.3459 |
| goth | elastic_net__deep | 185 | 7.5476 | 9.3882 | -0.3495 |
| goth | elastic_net__combined | 185 | 7.4477 | 9.3602 | -0.4970 |
| goth | ridge__baseline | 185 | 7.3728 | 9.1645 | -0.1196 |
| goth | ridge__traditional | 185 | 7.3633 | 9.1220 | -0.1934 |
| goth | ridge__deep | 185 | 7.4907 | 9.3705 | -0.0774 |
| goth | ridge__combined | 185 | 7.3959 | 9.3450 | -0.1559 |
| goth | dummy__baseline | 185 | 13.1467 | 14.6016 | -11.5343 |
| grindcore | elastic_net__baseline | 52 | 6.1688 | 7.7076 | -0.8735 |
| grindcore | elastic_net__traditional | 52 | 5.8217 | 7.2825 | -0.7027 |
| grindcore | elastic_net__deep | 52 | 6.1815 | 7.7381 | -0.9345 |
| grindcore | elastic_net__combined | 52 | 6.0193 | 7.5310 | -1.4202 |
| grindcore | ridge__baseline | 52 | 6.1256 | 7.7027 | -0.5912 |
| grindcore | ridge__traditional | 52 | 5.8875 | 7.3705 | -0.4122 |
| grindcore | ridge__deep | 52 | 6.2025 | 7.8125 | -0.2357 |
| grindcore | ridge__combined | 52 | 5.8284 | 7.4721 | -0.3477 |
| grindcore | dummy__baseline | 52 | 17.4251 | 18.8167 | -17.4239 |
| groove | elastic_net__baseline | 81 | 8.4014 | 10.4818 | -0.3154 |
| groove | elastic_net__traditional | 81 | 8.3150 | 10.2758 | -0.6238 |
| groove | elastic_net__deep | 81 | 8.2184 | 10.1961 | -0.4745 |
| groove | elastic_net__combined | 81 | 8.2237 | 10.0425 | -0.9040 |
| groove | ridge__baseline | 81 | 8.3557 | 10.4728 | -0.1158 |
| groove | ridge__traditional | 81 | 8.2120 | 10.2167 | -0.3249 |
| groove | ridge__deep | 81 | 8.0883 | 10.1039 | -0.0486 |
| groove | ridge__combined | 81 | 8.0670 | 9.9894 | -0.3006 |
| groove | dummy__baseline | 81 | 12.1678 | 13.5526 | -9.6980 |
| hard-rock | elastic_net__baseline | 233 | 6.6967 | 8.6166 | -0.1769 |
| hard-rock | elastic_net__traditional | 233 | 6.6801 | 8.6668 | -0.0882 |
| hard-rock | elastic_net__deep | 233 | 6.7607 | 8.7287 | -0.1400 |
| hard-rock | elastic_net__combined | 233 | 6.8489 | 8.7705 | -0.1857 |
| hard-rock | ridge__baseline | 233 | 6.6579 | 8.6003 | -0.0395 |
| hard-rock | ridge__traditional | 233 | 6.6481 | 8.6556 | 0.0142 |
| hard-rock | ridge__deep | 233 | 6.7105 | 8.6986 | 0.0448 |
| hard-rock | ridge__combined | 233 | 6.7921 | 8.7548 | 0.0383 |
| hard-rock | dummy__baseline | 233 | 9.0383 | 10.7250 | -5.7482 |
| hardcore | elastic_net__baseline | 341 | 6.0612 | 7.5535 | 0.1337 |
| hardcore | elastic_net__traditional | 341 | 6.1026 | 7.6372 | 0.2247 |
| hardcore | elastic_net__deep | 341 | 6.2217 | 7.7045 | 0.2182 |
| hardcore | elastic_net__combined | 341 | 6.2026 | 7.8152 | 0.3250 |
| hardcore | ridge__baseline | 341 | 6.0763 | 7.5618 | 0.0593 |
| hardcore | ridge__traditional | 341 | 6.1235 | 7.6490 | 0.1459 |
| hardcore | ridge__deep | 341 | 6.2343 | 7.7115 | 0.1134 |
| hardcore | ridge__combined | 341 | 6.2127 | 7.8093 | 0.1634 |
| hardcore | dummy__baseline | 341 | 6.4215 | 7.8625 | -1.5259 |
| heavy-metal | elastic_net__baseline | 30 | 8.9889 | 11.9066 | -0.3781 |
| heavy-metal | elastic_net__traditional | 30 | 8.4937 | 11.0176 | -1.6893 |
| heavy-metal | elastic_net__deep | 30 | 8.6763 | 11.1712 | -1.9552 |
| heavy-metal | elastic_net__combined | 30 | 8.6419 | 10.9222 | -2.5699 |
| heavy-metal | ridge__baseline | 30 | 9.1089 | 12.0429 | 0.0704 |
| heavy-metal | ridge__traditional | 30 | 8.4406 | 11.2721 | -0.3204 |
| heavy-metal | ridge__deep | 30 | 8.7455 | 11.4978 | 0.3774 |
| heavy-metal | ridge__combined | 30 | 8.3512 | 11.0478 | 0.2122 |
| heavy-metal | dummy__baseline | 30 | 17.7360 | 19.6583 | -15.1375 |
| hip-hop | elastic_net__baseline | 205 | 7.7274 | 10.1309 | 0.2934 |
| hip-hop | elastic_net__traditional | 205 | 7.7816 | 10.1697 | 0.3043 |
| hip-hop | elastic_net__deep | 205 | 7.8702 | 10.2090 | 0.4343 |
| hip-hop | elastic_net__combined | 205 | 7.8595 | 10.2117 | 0.5221 |
| hip-hop | ridge__baseline | 205 | 7.7244 | 10.1450 | 0.2246 |
| hip-hop | ridge__traditional | 205 | 7.7837 | 10.1818 | 0.2104 |
| hip-hop | ridge__deep | 205 | 7.9075 | 10.2409 | 0.2154 |
| hip-hop | ridge__combined | 205 | 7.8933 | 10.2396 | 0.2466 |
| hip-hop | dummy__baseline | 205 | 19.7531 | 22.9408 | 19.2370 |
| indie-pop | elastic_net__baseline | 231 | 9.2639 | 12.4240 | 0.1676 |
| indie-pop | elastic_net__traditional | 231 | 9.1531 | 12.2076 | 0.1679 |
| indie-pop | elastic_net__deep | 231 | 9.2899 | 12.4705 | 0.2820 |
| indie-pop | elastic_net__combined | 231 | 9.2997 | 12.4463 | 0.4101 |
| indie-pop | ridge__baseline | 231 | 9.2590 | 12.4046 | 0.0940 |
| indie-pop | ridge__traditional | 231 | 9.1667 | 12.2058 | 0.0746 |
| indie-pop | ridge__deep | 231 | 9.3112 | 12.4657 | 0.1098 |
| indie-pop | ridge__combined | 231 | 9.3321 | 12.4421 | 0.1344 |
| indie-pop | dummy__baseline | 231 | 15.3113 | 19.0611 | 10.6606 |
| industrial | elastic_net__baseline | 143 | 7.5337 | 9.2804 | -0.0571 |
| industrial | elastic_net__traditional | 143 | 7.1978 | 8.7739 | 0.0575 |
| industrial | elastic_net__deep | 143 | 7.5162 | 9.2342 | -0.1168 |
| industrial | elastic_net__combined | 143 | 7.2217 | 8.7943 | -0.2480 |
| industrial | ridge__baseline | 143 | 7.5164 | 9.2732 | 0.1042 |
| industrial | ridge__traditional | 143 | 7.1420 | 8.7362 | 0.1992 |
| industrial | ridge__deep | 143 | 7.4744 | 9.2332 | 0.1396 |
| industrial | ridge__combined | 143 | 7.1542 | 8.8042 | 0.1269 |
| industrial | dummy__baseline | 143 | 12.7132 | 14.0652 | -10.2200 |
| jazz | elastic_net__baseline | 66 | 7.6623 | 9.2963 | 0.8098 |
| jazz | elastic_net__traditional | 66 | 7.6852 | 9.4567 | 0.6384 |
| jazz | elastic_net__deep | 66 | 7.0995 | 8.7687 | 1.3013 |
| jazz | elastic_net__combined | 66 | 7.2923 | 9.1901 | 1.3542 |
| jazz | ridge__baseline | 66 | 7.6085 | 9.1773 | 0.3131 |
| jazz | ridge__traditional | 66 | 7.7847 | 9.4720 | 0.2187 |
| jazz | ridge__deep | 66 | 7.0319 | 8.6062 | 0.5642 |
| jazz | ridge__combined | 66 | 7.2143 | 9.0372 | 0.4862 |
| jazz | dummy__baseline | 66 | 8.3225 | 10.3135 | 4.3324 |
| k-pop | elastic_net__baseline | 60 | 7.8033 | 9.3969 | 0.2246 |
| k-pop | elastic_net__traditional | 60 | 7.7195 | 9.4758 | 0.2446 |
| k-pop | elastic_net__deep | 60 | 7.8126 | 9.2358 | -0.0351 |
| k-pop | elastic_net__combined | 60 | 7.9373 | 9.6620 | -0.0495 |
| k-pop | ridge__baseline | 60 | 7.8148 | 9.3949 | 0.0153 |
| k-pop | ridge__traditional | 60 | 7.8004 | 9.5452 | 0.1383 |
| k-pop | ridge__deep | 60 | 7.9281 | 9.3592 | -0.1050 |
| k-pop | ridge__combined | 60 | 8.0880 | 9.8209 | 0.0213 |
| k-pop | dummy__baseline | 60 | 9.7168 | 11.6413 | 0.8873 |
| metal | elastic_net__baseline | 111 | 6.9372 | 8.9337 | 0.4926 |
| metal | elastic_net__traditional | 111 | 6.6235 | 8.5933 | 0.6007 |
| metal | elastic_net__deep | 111 | 7.0250 | 9.0368 | 0.6144 |
| metal | elastic_net__combined | 111 | 6.7116 | 8.6372 | 0.7550 |
| metal | ridge__baseline | 111 | 6.9340 | 8.8784 | 0.3510 |
| metal | ridge__traditional | 111 | 6.6070 | 8.4879 | 0.3214 |
| metal | ridge__deep | 111 | 7.0200 | 8.9149 | 0.1832 |
| metal | ridge__combined | 111 | 6.7164 | 8.5679 | 0.1956 |
| metal | dummy__baseline | 111 | 12.0434 | 14.9576 | 11.9340 |
| metalcore | elastic_net__baseline | 129 | 3.7232 | 4.5177 | -0.1967 |
| metalcore | elastic_net__traditional | 129 | 3.6592 | 4.5069 | -0.1940 |
| metalcore | elastic_net__deep | 129 | 3.8435 | 4.7791 | -0.3121 |
| metalcore | elastic_net__combined | 129 | 3.8729 | 4.8159 | -0.4419 |
| metalcore | ridge__baseline | 129 | 3.7400 | 4.5277 | -0.0150 |
| metalcore | ridge__traditional | 129 | 3.6718 | 4.5122 | 0.0114 |
| metalcore | ridge__deep | 129 | 3.8863 | 4.7956 | -0.0188 |
| metalcore | ridge__combined | 129 | 3.8924 | 4.8280 | -0.0523 |
| metalcore | dummy__baseline | 129 | 5.9167 | 7.6490 | -4.6115 |
| piano | elastic_net__baseline | 71 | 6.9156 | 9.0801 | -0.2193 |
| piano | elastic_net__traditional | 71 | 7.1285 | 9.2092 | -0.3280 |
| piano | elastic_net__deep | 71 | 7.1794 | 9.5424 | -0.5411 |
| piano | elastic_net__combined | 71 | 7.3350 | 9.5315 | -0.8298 |
| piano | ridge__baseline | 71 | 6.9173 | 9.0981 | 0.0951 |
| piano | ridge__traditional | 71 | 7.0823 | 9.1510 | -0.0123 |
| piano | ridge__deep | 71 | 7.0352 | 9.4814 | -0.0904 |
| piano | ridge__combined | 71 | 7.1825 | 9.4572 | -0.2643 |
| piano | dummy__baseline | 71 | 10.4332 | 11.8492 | -8.1748 |
| pop | elastic_net__baseline | 65 | 6.4236 | 8.0497 | 1.0684 |
| pop | elastic_net__traditional | 65 | 6.4796 | 8.0109 | 1.3577 |
| pop | elastic_net__deep | 65 | 6.4300 | 7.9822 | 1.4849 |
| pop | elastic_net__combined | 65 | 6.3299 | 7.8597 | 1.9776 |
| pop | ridge__baseline | 65 | 6.2742 | 7.8322 | 0.9237 |
| pop | ridge__traditional | 65 | 6.3440 | 7.8643 | 1.1063 |
| pop | ridge__deep | 65 | 6.5807 | 7.9892 | 0.4987 |
| pop | ridge__combined | 65 | 6.5900 | 7.8852 | 0.6979 |
| pop | dummy__baseline | 65 | 28.9494 | 30.8192 | 28.9494 |
| power-pop | elastic_net__baseline | 149 | 6.3284 | 7.7172 | -0.6188 |
| power-pop | elastic_net__traditional | 149 | 5.8472 | 7.1657 | -0.7945 |
| power-pop | elastic_net__deep | 149 | 6.3296 | 7.7185 | -0.8963 |
| power-pop | elastic_net__combined | 149 | 6.1165 | 7.5381 | -1.1253 |
| power-pop | ridge__baseline | 149 | 6.3457 | 7.7460 | -0.5664 |
| power-pop | ridge__traditional | 149 | 5.8634 | 7.2304 | -0.5853 |
| power-pop | ridge__deep | 149 | 6.3397 | 7.7690 | -0.5054 |
| power-pop | ridge__combined | 149 | 6.0828 | 7.5904 | -0.5603 |
| power-pop | dummy__baseline | 149 | 17.6870 | 18.6190 | -17.5532 |
| progressive-house | elastic_net__baseline | 38 | 5.7435 | 7.0011 | -1.0639 |
| progressive-house | elastic_net__traditional | 38 | 6.0595 | 7.1536 | -1.1369 |
| progressive-house | elastic_net__deep | 38 | 6.4810 | 7.6052 | -1.4777 |
| progressive-house | elastic_net__combined | 38 | 6.6250 | 7.9958 | -2.1145 |
| progressive-house | ridge__baseline | 38 | 5.6488 | 6.8433 | -0.3904 |
| progressive-house | ridge__traditional | 38 | 6.1540 | 7.1929 | -0.5368 |
| progressive-house | ridge__deep | 38 | 6.4919 | 7.6188 | -0.5415 |
| progressive-house | ridge__combined | 38 | 6.5855 | 7.9398 | -0.8174 |
| progressive-house | dummy__baseline | 38 | 6.3126 | 8.2606 | -0.1477 |
| psych-rock | elastic_net__baseline | 141 | 5.9803 | 7.4452 | -0.3160 |
| psych-rock | elastic_net__traditional | 141 | 6.0443 | 7.5582 | -0.4353 |
| psych-rock | elastic_net__deep | 141 | 6.3481 | 7.8054 | -0.4547 |
| psych-rock | elastic_net__combined | 141 | 6.4796 | 7.9659 | -0.6429 |
| psych-rock | ridge__baseline | 141 | 5.9488 | 7.4155 | -0.1527 |
| psych-rock | ridge__traditional | 141 | 5.9845 | 7.5238 | -0.2345 |
| psych-rock | ridge__deep | 141 | 6.3509 | 7.8151 | -0.1478 |
| psych-rock | ridge__combined | 141 | 6.4075 | 7.9365 | -0.2391 |
| psych-rock | dummy__baseline | 141 | 10.5304 | 12.5127 | -9.2207 |
| punk | elastic_net__baseline | 115 | 5.1651 | 6.5359 | 0.3400 |
| punk | elastic_net__traditional | 115 | 5.1103 | 6.5046 | 0.4442 |
| punk | elastic_net__deep | 115 | 5.1127 | 6.6848 | 0.4813 |
| punk | elastic_net__combined | 115 | 5.1375 | 6.8154 | 0.7052 |
| punk | ridge__baseline | 115 | 5.1796 | 6.5172 | 0.1125 |
| punk | ridge__traditional | 115 | 5.1515 | 6.5379 | 0.2157 |
| punk | ridge__deep | 115 | 5.2009 | 6.6933 | 0.0971 |
| punk | ridge__combined | 115 | 5.2062 | 6.7877 | 0.1457 |
| punk | dummy__baseline | 115 | 5.1545 | 7.3415 | 2.5273 |
| punk-rock | elastic_net__baseline | 85 | 5.1029 | 6.0769 | -0.3466 |
| punk-rock | elastic_net__traditional | 85 | 5.2261 | 6.4259 | -0.4080 |
| punk-rock | elastic_net__deep | 85 | 5.5371 | 6.8540 | -0.5488 |
| punk-rock | elastic_net__combined | 85 | 5.6918 | 7.0509 | -0.8766 |
| punk-rock | ridge__baseline | 85 | 5.1592 | 6.1428 | -0.0796 |
| punk-rock | ridge__traditional | 85 | 5.2473 | 6.4341 | -0.1806 |
| punk-rock | ridge__deep | 85 | 5.5355 | 6.9247 | -0.1008 |
| punk-rock | ridge__combined | 85 | 5.6561 | 7.1202 | -0.2183 |
| punk-rock | dummy__baseline | 85 | 9.4339 | 10.4608 | -8.9844 |
| rock | elastic_net__baseline | 42 | 8.1983 | 13.9083 | 1.3841 |
| rock | elastic_net__traditional | 42 | 7.9278 | 13.6758 | 1.3407 |
| rock | elastic_net__deep | 42 | 8.4005 | 13.5667 | 1.6695 |
| rock | elastic_net__combined | 42 | 8.1055 | 13.4945 | 2.2336 |
| rock | ridge__baseline | 42 | 8.0145 | 14.0732 | 1.0210 |
| rock | ridge__traditional | 42 | 7.7518 | 13.7214 | 0.8974 |
| rock | ridge__deep | 42 | 8.1803 | 13.6717 | 0.5927 |
| rock | ridge__combined | 42 | 7.9066 | 13.4581 | 0.6963 |
| rock | dummy__baseline | 42 | 20.4564 | 21.9583 | 17.9828 |
| show-tunes | elastic_net__baseline | 33 | 12.7128 | 15.4184 | 0.3551 |
| show-tunes | elastic_net__traditional | 33 | 12.7559 | 15.3263 | 0.7157 |
| show-tunes | elastic_net__deep | 33 | 13.1463 | 15.7784 | 0.1088 |
| show-tunes | elastic_net__combined | 33 | 12.8225 | 15.3098 | 0.6309 |
| show-tunes | ridge__baseline | 33 | 12.6709 | 15.4610 | -0.0137 |
| show-tunes | ridge__traditional | 33 | 12.6589 | 15.2696 | 0.1353 |
| show-tunes | ridge__deep | 33 | 13.0891 | 15.8189 | -0.5059 |
| show-tunes | ridge__combined | 33 | 12.7523 | 15.4580 | -0.3847 |
| show-tunes | dummy__baseline | 33 | 13.8835 | 16.7003 | -0.7906 |
| singer-songwriter | elastic_net__baseline | 169 | 6.7894 | 9.3232 | -0.1009 |
| singer-songwriter | elastic_net__traditional | 169 | 6.6390 | 9.2168 | -0.2245 |
| singer-songwriter | elastic_net__deep | 169 | 6.9474 | 9.5335 | -0.1246 |
| singer-songwriter | elastic_net__combined | 169 | 7.0336 | 9.5919 | -0.2160 |
| singer-songwriter | ridge__baseline | 169 | 6.7611 | 9.3090 | 0.0594 |
| singer-songwriter | ridge__traditional | 169 | 6.6152 | 9.2445 | -0.0240 |
| singer-songwriter | ridge__deep | 169 | 6.9279 | 9.5402 | 0.1474 |
| singer-songwriter | ridge__combined | 169 | 7.0454 | 9.6377 | 0.1014 |
| singer-songwriter | dummy__baseline | 169 | 9.5124 | 11.4966 | -4.3422 |
| ska | elastic_net__baseline | 138 | 5.4103 | 6.7531 | -0.3906 |
| ska | elastic_net__traditional | 138 | 5.3690 | 6.7750 | -0.5467 |
| ska | elastic_net__deep | 138 | 5.5191 | 6.7896 | -0.4397 |
| ska | elastic_net__combined | 138 | 5.4474 | 6.7851 | -0.6633 |
| ska | ridge__baseline | 138 | 5.4192 | 6.7599 | -0.2813 |
| ska | ridge__traditional | 138 | 5.4025 | 6.8111 | -0.3665 |
| ska | ridge__deep | 138 | 5.5543 | 6.8649 | -0.1500 |
| ska | ridge__combined | 138 | 5.4726 | 6.8411 | -0.2849 |
| ska | dummy__baseline | 138 | 12.6121 | 13.7420 | -12.2196 |
| soul | elastic_net__baseline | 211 | 6.6810 | 8.8829 | 0.2695 |
| soul | elastic_net__traditional | 211 | 6.8321 | 9.0367 | 0.2058 |
| soul | elastic_net__deep | 211 | 6.9200 | 9.1913 | 0.3611 |
| soul | elastic_net__combined | 211 | 7.0219 | 9.3008 | 0.3228 |
| soul | ridge__baseline | 211 | 6.6728 | 8.8611 | 0.1160 |
| soul | ridge__traditional | 211 | 6.8214 | 9.0298 | 0.0712 |
| soul | ridge__deep | 211 | 6.9180 | 9.1723 | 0.1342 |
| soul | ridge__combined | 211 | 7.0385 | 9.2996 | 0.0297 |
| soul | dummy__baseline | 211 | 9.6794 | 12.0553 | 3.0978 |
| swedish | elastic_net__baseline | 106 | 7.0762 | 8.8173 | -0.4486 |
| swedish | elastic_net__traditional | 106 | 7.3404 | 9.2439 | -0.5094 |
| swedish | elastic_net__deep | 106 | 7.1344 | 8.9287 | -0.6254 |
| swedish | elastic_net__combined | 106 | 7.4257 | 9.3521 | -0.7065 |
| swedish | ridge__baseline | 106 | 7.1270 | 8.8490 | -0.2383 |
| swedish | ridge__traditional | 106 | 7.4061 | 9.2947 | -0.2516 |
| swedish | ridge__deep | 106 | 7.2432 | 9.0189 | -0.2343 |
| swedish | ridge__combined | 106 | 7.5440 | 9.4447 | -0.1980 |
| swedish | dummy__baseline | 106 | 9.4797 | 11.4476 | -5.3457 |

### Resíduos

| Modelo | Média | Desvio | Quantis 5/25/50/75/95% |
|---|---|---|---|
| elastic_net__baseline | -0.0081 | 9.2138 | {"q05": -12.593987062222054, "q25": -6.392265731646641, "q50": -0.9424027748445223, "q75": 5.010331774417957, "q95": 17.091918794993493} |
| elastic_net__traditional | -0.0202 | 9.1883 | {"q05": -12.638076803402237, "q25": -6.403951744319398, "q50": -0.9623751099620943, "q75": 5.02593072497803, "q95": 16.928118065904663} |
| elastic_net__deep | -0.0152 | 9.2801 | {"q05": -12.814925532478384, "q25": -6.334933079572949, "q50": -0.966496350468379, "q75": 5.180925543192794, "q95": 17.059402498445632} |
| elastic_net__combined | -0.0258 | 9.2954 | {"q05": -12.990186317360095, "q25": -6.3425831440850935, "q50": -0.9650782746419004, "q75": 5.1425050305823135, "q95": 17.00065361618032} |
| ridge__baseline | -0.0114 | 9.2115 | {"q05": -12.641858622279598, "q25": -6.379262619396599, "q50": -0.9786128433999215, "q75": 4.995097457518872, "q95": 17.069158769480858} |
| ridge__traditional | -0.0164 | 9.1866 | {"q05": -12.580655700141715, "q25": -6.3900900411459105, "q50": -0.9412017834120956, "q75": 5.040154722527205, "q95": 17.014849957691474} |
| ridge__deep | -0.0094 | 9.2860 | {"q05": -12.840804044226159, "q25": -6.418243268764463, "q50": -0.9459369446426642, "q75": 5.210546449093463, "q95": 17.157900752630532} |
| ridge__combined | -0.0210 | 9.3041 | {"q05": -13.02568647722214, "q25": -6.349806405186519, "q50": -0.9647802000279757, "q75": 5.120071263141695, "q95": 17.04634716974725} |
| dummy__baseline | 0.0000 | 13.4364 | {"q05": -19.959960777904886, "q25": -9.97318070318888, "q50": -1.0362804379800608, "q75": 8.02681929681112, "q95": 24.96371956201994} |

## Limitações

Coorte condicionada à disponibilidade de letras aceitas e matching anterior; descritores LFM2b podem referir-se a outra versão da letra em relação à LRCLIB. Os IDs operacionais não são universais. MiniLM é predominantemente validado para inglês e a coleta inclui outros idiomas. Não há interpretação causal. Escolhas dos pilotos e sobreposição da amostra com o piloto limitam a independência do desenvolvimento. Nenhum diagnóstico alterou os modelos.


## Verificações e reconciliação operacional

116 testes aprovados, 0 falhos, 0 ignorados; testes específicos 8 aprovados. Comandos e códigos de saída estão no run summary. Ruff, formatação e git diff --check: código 0. Nove modelos serializados recarregados com predições finitas em todas as 7648 linhas de desenvolvimento. Todos os hashes originais preservados. Alvo do holdout não carregado; métricas do holdout não calculadas.

Auditoria direta de PCA: 96 ajustes conferidos, cada um com n_samples_ igual ao tamanho exato do seu treino. Empates no menor score da seleção externa: 0. O desempate implementado é a primeira entrada de menor MAE na ordem fixa: Ridge alpha crescente; Elastic Net l1_ratio crescente e alpha decrescente. A referência do plano à ordem dos pilotos deve ser lida como trajetória de ajuste, não como o desempate mais regularizado da v0.3.1. Nenhum resultado ou modelo foi alterado por essa correção documental.

Limitações operacionais: o launcher do ambiente imprime um aviso de localização de Python, embora os comandos concluam com código 0. Os previews e mudanças pessoais preexistentes foram preservados e ficaram fora dos checkpoints. Para reproduzir, usar python -m tcc_music_popularity.final_development_v050 prepare/train/verify; os selos e checkpoints existentes impedem retuning acidental.
