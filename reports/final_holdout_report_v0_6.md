# Avaliação final do holdout — v0.6

## Método e integridade

Foram avaliados nove estimadores congelados no desenvolvimento: quatro Elastic Net primários, quatro Ridge secundários e DummyRegressor pela média de desenvolvimento. As configurações correspondem a metadados/áudio (Baseline), Baseline e 196 descritores LFM2b (Tradicional), Baseline e 384 dimensões MiniLM (Profundo), e os dois blocos textuais (Combinado). PCAs de 90% foram ajustadas separadamente dentro do desenvolvimento; nenhum pré-processamento foi ajustado no teste. O candidato predefinido elastic_net__traditional permanece inalterado.

As previsões brutas foram persistidas e seladas antes do acesso ao alvo. A popularidade foi projetada exclusivamente para os representantes congelados e unida por track_id e spotify_row_id, com join 1:1. MAE é primária; RMSE, R² e Spearman são secundárias/descritivas. Resíduo = observado − previsto; valor positivo indica subestimação. Spearman é não definida quando o vetor previsto é constante (Dummy). Previsões fora de 0–100 foram mantidas.

O bootstrap pareado por artista utiliza 2.000 reamostragens com seed 20261013. Sorteiam-se 1.308 grupos com reposição em cada reamostragem, incluindo todas as composições de cada grupo e preservando sua multiplicidade. Os mesmos sorteios são usados em todas as comparações; métricas permanecem ponderadas por composição. IC95% são descritivos. Nas três comparações primárias de MAE, usa-se Bonferroni: intervalos bilaterais de 98,333333% nos quantis 0,008333333 e 0,991666667. Ganho confirmado exige limite superior ajustado menor que zero. Os intervalos avaliam a incerteza do teste para modelos congelados e não toda a variabilidade de repetir o treinamento. Intervalo contendo zero não demonstra equivalência, ausência universal de efeito ou inutilidade das letras.


Amostra: 2592 composições, 1308 artistas. Zero sobreposição de composição/artista/hash normalizado de letra com desenvolvimento. Zero perda/multiplicação de linhas ou alvo ausente. Os nove pipelines e todos os artefatos congelados preservam seus hashes. Checkpoint: 9c6d16e1eb5c7c8d6b86559f5ac40ac7f7fda4db; tag final-models-pre-holdout-v0.5.

Previsões seladas em 2026-10-14T16:12:09.447436+00:00; SHA-256 completo `a5f3abd70e9d8045437dd75e5749a8b14a583dfc1ce0b2ea1d8478ffe3f33f29`. Abertura do alvo iniciada em 2026-10-14T16:12:27.567600+00:00. Hash do avaliador `966c8896b2a267fa76cd7240c26ea53a2957c2c99074e0ce6f296d80507c506b`; plano `c8674923a0fc64628ec5e7275378bd7ddb0ff3d7995ecaeef8ec735c90036744`; manifesto `cf749eb097f29bd3665b5dff27fc61d81787a0bb0fe8eab71966013d7dae55bb`. Registro privado de abertura preservado.

## Nove modelos no teste

| Modelo | MAE | RMSE | R² | Spearman | Resíduo médio | <0 | >100 |
|---|---|---|---|---|---|---|---|
| elastic_net__baseline | 7.2029 | 9.2573 | 0.5568 | 0.7391 | -0.0501 | 3 | 0 |
| ridge__baseline | 7.2036 | 9.2510 | 0.5574 | 0.7395 | -0.0520 | 3 | 0 |
| elastic_net__traditional | 7.1831 | 9.2095 | 0.5614 | 0.7384 | -0.0360 | 3 | 0 |
| ridge__traditional | 7.1756 | 9.1951 | 0.5627 | 0.7395 | -0.0438 | 3 | 0 |
| elastic_net__deep | 7.2990 | 9.3429 | 0.5486 | 0.7308 | 0.0006 | 3 | 0 |
| ridge__deep | 7.2811 | 9.3023 | 0.5525 | 0.7331 | -0.0129 | 4 | 0 |
| elastic_net__combined | 7.2679 | 9.3301 | 0.5498 | 0.7282 | 0.0299 | 3 | 0 |
| ridge__combined | 7.2511 | 9.2949 | 0.5532 | 0.7309 | 0.0180 | 6 | 0 |
| dummy__baseline | 11.1164 | 13.9058 | -0.0001 | não definida | 0.1179 | 0 | 0 |

## Comparações incrementais

| Modelo − Baseline | Primária | ΔMAE | ΔMAE % | IC95% ΔMAE | IC98,333333% ΔMAE | ΔRMSE | IC95% ΔRMSE |
|---|---|---|---|---|---|---|---|
| elastic_net__traditional | True | -0.0198 | -0.2749 | [-0.0947; 0.0537] | [-0.1147; 0.0725] | -0.0478 | [-0.1254; 0.0315] |
| elastic_net__deep | True | 0.0961 | 1.3337 | [0.0171; 0.1717] | [0.0005; 0.1872] | 0.0856 | [0.0063; 0.1634] |
| elastic_net__combined | True | 0.0650 | 0.9026 | [-0.0426; 0.1654] | [-0.0646; 0.1900] | 0.0728 | [-0.0396; 0.1833] |
| ridge__traditional | False | -0.0280 | -0.3889 | [-0.1030; 0.0433] | secundária; sem ajuste | -0.0558 | [-0.1344; 0.0200] |
| ridge__deep | False | 0.0775 | 1.0762 | [0.0102; 0.1465] | secundária; sem ajuste | 0.0513 | [-0.0207; 0.1230] |
| ridge__combined | False | 0.0475 | 0.6596 | [-0.0493; 0.1420] | secundária; sem ajuste | 0.0440 | [-0.0593; 0.1446] |

## Conclusões primárias

- traditional: ΔMAE=-0.0198 (-0.2749%); Ganho incremental não confirmado; o intervalo ajustado inclui zero. Isso não demonstra equivalência nem ausência universal de contribuição das letras.
- deep: ΔMAE=0.0961 (1.3337%); O intervalo ajustado indica erro maior que o Baseline nesta amostra; ganho incremental não confirmado.
- combined: ΔMAE=0.0650 (0.9026%); Ganho incremental não confirmado; o intervalo ajustado inclui zero. Isso não demonstra equivalência nem ausência universal de contribuição das letras.

## Desenvolvimento versus teste

| Modelo | MAE OOF desenvolvimento | MAE teste | Diferença teste−OOF | RMSE OOF | RMSE teste |
|---|---|---|---|---|---|
| elastic_net__baseline | 7.0940 | 7.2029 | 0.1089 | 9.2138 | 9.2573 |
| ridge__baseline | 7.0925 | 7.2036 | 0.1110 | 9.2115 | 9.2510 |
| elastic_net__traditional | 7.0612 | 7.1831 | 0.1219 | 9.1883 | 9.2095 |
| ridge__traditional | 7.0563 | 7.1756 | 0.1193 | 9.1866 | 9.1951 |
| elastic_net__deep | 7.1625 | 7.2990 | 0.1365 | 9.2801 | 9.3429 |
| ridge__deep | 7.1696 | 7.2811 | 0.1115 | 9.2860 | 9.3023 |
| elastic_net__combined | 7.1631 | 7.2679 | 0.1048 | 9.2955 | 9.3301 |
| ridge__combined | 7.1688 | 7.2511 | 0.0823 | 9.3041 | 9.2949 |
| dummy__baseline | 10.7222 | 11.1164 | 0.3942 | 13.4364 | 13.9058 |

OOF de desenvolvimento e holdout são amostras diferentes, com estimadores também ajustados em tamanhos de treino diferentes; diferenças entre essas métricas não constituem isoladamente prova de overfitting. O teste não selecionou novamente o candidato.

## Diagnósticos exploratórios

As tabelas por período/gênero abaixo incluem apenas grupos com n≥30. Não implicam modelos de subgrupo, exclusões ou alterações do protocolo. Histogramas usam resíduo observado−previsto; observado versus previsto usa bins fixos de 10 pontos com n≥30.

### period

| Categoria | Modelo | n | MAE | RMSE | R² | Spearman | Resíduo médio |
|---|---|---|---|---|---|---|---|
| 2000–2009 | elastic_net__baseline | 713 | 7.0179 | 9.0050 | 0.3022 | 0.6259 | -0.1375 |
| 2000–2009 | ridge__baseline | 713 | 7.0182 | 9.0057 | 0.3021 | 0.6259 | -0.1379 |
| 2000–2009 | elastic_net__traditional | 713 | 7.0209 | 8.9787 | 0.3062 | 0.6205 | -0.1041 |
| 2000–2009 | ridge__traditional | 713 | 7.0501 | 9.0137 | 0.3008 | 0.6209 | -0.0938 |
| 2000–2009 | elastic_net__deep | 713 | 7.0491 | 8.9750 | 0.3068 | 0.6176 | -0.1443 |
| 2000–2009 | ridge__deep | 713 | 7.1508 | 9.0814 | 0.2903 | 0.6171 | -0.1140 |
| 2000–2009 | elastic_net__combined | 713 | 7.0316 | 8.9850 | 0.3053 | 0.6139 | -0.1307 |
| 2000–2009 | ridge__combined | 713 | 7.1263 | 9.0801 | 0.2905 | 0.6141 | -0.0912 |
| 2000–2009 | dummy__baseline | 713 | 10.3160 | 12.5301 | -0.3511 | não definida | -6.3875 |
| 2010–2019 | elastic_net__baseline | 1802 | 7.2151 | 9.2393 | 0.5632 | 0.7533 | -0.0534 |
| 2010–2019 | ridge__baseline | 1802 | 7.2164 | 9.2306 | 0.5640 | 0.7535 | -0.0559 |
| 2010–2019 | elastic_net__traditional | 1802 | 7.1849 | 9.1952 | 0.5674 | 0.7534 | -0.0289 |
| 2010–2019 | ridge__traditional | 1802 | 7.1636 | 9.1635 | 0.5704 | 0.7544 | -0.0426 |
| 2010–2019 | elastic_net__deep | 1802 | 7.3291 | 9.3669 | 0.5511 | 0.7453 | 0.0295 |
| 2010–2019 | ridge__deep | 1802 | 7.2672 | 9.2759 | 0.5598 | 0.7475 | 0.0059 |
| 2010–2019 | elastic_net__combined | 1802 | 7.2876 | 9.3484 | 0.5528 | 0.7434 | 0.0773 |
| 2010–2019 | ridge__combined | 1802 | 7.2267 | 9.2674 | 0.5606 | 0.7462 | 0.0534 |
| 2010–2019 | dummy__baseline | 1802 | 11.2831 | 14.1739 | -0.0279 | não definida | 2.3359 |
| 2020 ou posterior | elastic_net__baseline | 77 | 8.6295 | 11.6678 | 0.5181 | 0.7815 | 0.8370 |
| 2020 ou posterior | ridge__baseline | 77 | 8.6205 | 11.6553 | 0.5191 | 0.7861 | 0.8349 |
| 2020 ou posterior | elastic_net__traditional | 77 | 8.6411 | 11.3939 | 0.5405 | 0.7834 | 0.4272 |
| 2020 ou posterior | ridge__traditional | 77 | 8.6184 | 11.3458 | 0.5443 | 0.7860 | 0.3893 |
| 2020 ou posterior | elastic_net__deep | 77 | 8.9068 | 11.7977 | 0.5073 | 0.7670 | 0.6666 |
| 2020 ou posterior | ridge__deep | 77 | 8.8131 | 11.6452 | 0.5200 | 0.7757 | 0.4814 |
| 2020 ou posterior | elastic_net__combined | 77 | 8.9961 | 11.7294 | 0.5130 | 0.7501 | 0.4058 |
| 2020 ou posterior | ridge__combined | 77 | 8.9786 | 11.6162 | 0.5224 | 0.7604 | 0.2013 |
| 2020 ou posterior | dummy__baseline | 77 | 14.6266 | 18.8123 | -0.2527 | não definida | 8.4495 |

### genre

| Categoria | Modelo | n | MAE | RMSE | R² | Spearman | Resíduo médio |
|---|---|---|---|---|---|---|---|
| acoustic | elastic_net__baseline | 107 | 8.8423 | 10.3029 | 0.0589 | 0.2118 | -0.4625 |
| acoustic | ridge__baseline | 107 | 8.8373 | 10.3060 | 0.0584 | 0.2095 | -0.3881 |
| acoustic | elastic_net__traditional | 107 | 8.6886 | 10.2600 | 0.0668 | 0.2089 | -0.1819 |
| acoustic | ridge__traditional | 107 | 8.7050 | 10.2823 | 0.0627 | 0.2026 | -0.0976 |
| acoustic | elastic_net__deep | 107 | 8.9832 | 10.4660 | 0.0289 | 0.1794 | -0.5176 |
| acoustic | ridge__deep | 107 | 8.9900 | 10.5188 | 0.0191 | 0.1657 | -0.2010 |
| acoustic | elastic_net__combined | 107 | 8.8505 | 10.5246 | 0.0180 | 0.1719 | -0.3193 |
| acoustic | ridge__combined | 107 | 8.8828 | 10.6032 | 0.0033 | 0.1600 | -0.0194 |
| acoustic | dummy__baseline | 107 | 9.5868 | 11.3726 | -0.1466 | não definida | -4.0668 |
| alt-rock | elastic_net__baseline | 129 | 5.5746 | 7.1895 | 0.2926 | 0.5524 | 0.4964 |
| alt-rock | ridge__baseline | 129 | 5.5771 | 7.1929 | 0.2919 | 0.5518 | 0.4977 |
| alt-rock | elastic_net__traditional | 129 | 5.5965 | 7.2131 | 0.2879 | 0.5615 | 0.4759 |
| alt-rock | ridge__traditional | 129 | 5.6188 | 7.2237 | 0.2859 | 0.5598 | 0.4151 |
| alt-rock | elastic_net__deep | 129 | 5.7514 | 7.2685 | 0.2770 | 0.5515 | 0.8534 |
| alt-rock | ridge__deep | 129 | 5.7981 | 7.2481 | 0.2810 | 0.5545 | 0.6676 |
| alt-rock | elastic_net__combined | 129 | 5.7586 | 7.3356 | 0.2636 | 0.5509 | 0.8147 |
| alt-rock | ridge__combined | 129 | 5.8142 | 7.3256 | 0.2656 | 0.5533 | 0.6142 |
| alt-rock | dummy__baseline | 129 | 10.9445 | 13.5127 | -1.4989 | não definida | 10.4653 |
| black-metal | elastic_net__baseline | 88 | 6.3011 | 7.7186 | -0.3581 | 0.1026 | -0.1363 |
| black-metal | ridge__baseline | 88 | 6.3015 | 7.7184 | -0.3580 | 0.1019 | -0.1090 |
| black-metal | elastic_net__traditional | 88 | 6.1470 | 7.5739 | -0.3076 | 0.1652 | -0.6751 |
| black-metal | ridge__traditional | 88 | 6.1624 | 7.5861 | -0.3119 | 0.1719 | -0.5912 |
| black-metal | elastic_net__deep | 88 | 6.2773 | 7.7630 | -0.3738 | 0.1203 | -0.6107 |
| black-metal | ridge__deep | 88 | 6.2804 | 7.7930 | -0.3844 | 0.1223 | -0.3354 |
| black-metal | elastic_net__combined | 88 | 6.1586 | 7.6567 | -0.3364 | 0.1843 | -1.0627 |
| black-metal | ridge__combined | 88 | 6.1692 | 7.7033 | -0.3527 | 0.1778 | -0.7555 |
| black-metal | dummy__baseline | 88 | 13.4475 | 14.7045 | -3.9290 | não definida | -13.1284 |
| blues | elastic_net__baseline | 79 | 8.0092 | 11.2464 | 0.0720 | 0.3922 | 1.3013 |
| blues | ridge__baseline | 79 | 8.0076 | 11.2341 | 0.0740 | 0.3925 | 1.2614 |
| blues | elastic_net__traditional | 79 | 8.0462 | 11.1308 | 0.0910 | 0.4292 | 1.7519 |
| blues | ridge__traditional | 79 | 8.0455 | 11.1427 | 0.0890 | 0.4290 | 1.7851 |
| blues | elastic_net__deep | 79 | 8.1142 | 11.1767 | 0.0834 | 0.4171 | 1.3852 |
| blues | ridge__deep | 79 | 8.0832 | 11.1868 | 0.0818 | 0.4150 | 1.6098 |
| blues | elastic_net__combined | 79 | 8.0339 | 11.1363 | 0.0901 | 0.4343 | 1.8873 |
| blues | ridge__combined | 79 | 8.0289 | 11.2204 | 0.0763 | 0.4344 | 2.2038 |
| blues | dummy__baseline | 79 | 9.1618 | 11.7818 | -0.0185 | não definida | -1.5870 |
| chill | elastic_net__baseline | 68 | 9.5122 | 12.1977 | 0.3660 | 0.7866 | 0.0476 |
| chill | ridge__baseline | 68 | 9.5249 | 12.2118 | 0.3645 | 0.7803 | -0.0263 |
| chill | elastic_net__traditional | 68 | 9.6290 | 12.0915 | 0.3769 | 0.7506 | -0.0891 |
| chill | ridge__traditional | 68 | 9.6498 | 12.1210 | 0.3739 | 0.7471 | -0.2295 |
| chill | elastic_net__deep | 68 | 9.3124 | 11.9070 | 0.3958 | 0.7640 | 0.1219 |
| chill | ridge__deep | 68 | 9.4141 | 12.0375 | 0.3825 | 0.7485 | -0.3285 |
| chill | elastic_net__combined | 68 | 9.5934 | 11.9973 | 0.3866 | 0.7146 | 0.0790 |
| chill | ridge__combined | 68 | 9.6607 | 12.0855 | 0.3776 | 0.7121 | -0.3747 |
| chill | dummy__baseline | 68 | 13.2521 | 16.1028 | -0.1050 | não definida | 4.9639 |
| country | elastic_net__baseline | 138 | 6.9183 | 8.7357 | 0.2734 | 0.5677 | -0.0881 |
| country | ridge__baseline | 138 | 6.9222 | 8.7354 | 0.2734 | 0.5689 | -0.1115 |
| country | elastic_net__traditional | 138 | 6.9714 | 8.8216 | 0.2590 | 0.5573 | -0.2537 |
| country | ridge__traditional | 138 | 6.9786 | 8.8186 | 0.2595 | 0.5578 | -0.3272 |
| country | elastic_net__deep | 138 | 7.0426 | 9.0194 | 0.2254 | 0.5177 | 0.2248 |
| country | ridge__deep | 138 | 7.0504 | 9.0053 | 0.2278 | 0.5200 | -0.0252 |
| country | elastic_net__combined | 138 | 7.0518 | 9.0565 | 0.2190 | 0.5201 | -0.0013 |
| country | ridge__combined | 138 | 7.0742 | 9.0634 | 0.2178 | 0.5194 | -0.2302 |
| country | dummy__baseline | 138 | 8.7421 | 11.5632 | -0.2731 | não definida | 5.3558 |
| dance | elastic_net__baseline | 78 | 8.4528 | 10.4945 | 0.4783 | 0.8157 | -0.0708 |
| dance | ridge__baseline | 78 | 8.4440 | 10.4843 | 0.4794 | 0.8186 | -0.0568 |
| dance | elastic_net__traditional | 78 | 8.5269 | 10.3467 | 0.4929 | 0.8167 | -0.3048 |
| dance | ridge__traditional | 78 | 8.5287 | 10.3366 | 0.4939 | 0.8148 | -0.4373 |
| dance | elastic_net__deep | 78 | 8.6871 | 10.7046 | 0.4573 | 0.7935 | 0.9224 |
| dance | ridge__deep | 78 | 8.6268 | 10.5604 | 0.4718 | 0.8023 | 0.4965 |
| dance | elastic_net__combined | 78 | 8.6589 | 10.4320 | 0.4845 | 0.7963 | 0.6169 |
| dance | ridge__combined | 78 | 8.5621 | 10.2834 | 0.4991 | 0.7990 | 0.1977 |
| dance | dummy__baseline | 78 | 14.6191 | 18.8336 | -0.6800 | não definida | 11.9823 |
| death-metal | elastic_net__baseline | 117 | 6.1398 | 7.8901 | -0.1081 | 0.2004 | 0.2199 |
| death-metal | ridge__baseline | 117 | 6.1376 | 7.8851 | -0.1067 | 0.2054 | 0.2711 |
| death-metal | elastic_net__traditional | 117 | 5.8938 | 7.5639 | -0.0184 | 0.2983 | 0.2313 |
| death-metal | ridge__traditional | 117 | 5.8935 | 7.5537 | -0.0156 | 0.3010 | 0.1618 |
| death-metal | elastic_net__deep | 117 | 6.2097 | 7.9036 | -0.1119 | 0.2161 | 0.2021 |
| death-metal | ridge__deep | 117 | 6.2556 | 7.9762 | -0.1324 | 0.2115 | 0.2081 |
| death-metal | elastic_net__combined | 117 | 6.0023 | 7.8199 | -0.0885 | 0.2700 | 0.3722 |
| death-metal | ridge__combined | 117 | 6.0225 | 7.8347 | -0.0926 | 0.2716 | 0.0972 |
| death-metal | dummy__baseline | 117 | 7.7653 | 9.0533 | -0.4589 | não definida | -5.0775 |
| edm | elastic_net__baseline | 34 | 8.1168 | 10.0653 | 0.3458 | 0.7793 | 0.3869 |
| edm | ridge__baseline | 34 | 8.1348 | 10.0632 | 0.3460 | 0.7790 | 0.2956 |
| edm | elastic_net__traditional | 34 | 8.4402 | 10.7435 | 0.2546 | 0.6100 | 0.3842 |
| edm | ridge__traditional | 34 | 8.4416 | 10.7430 | 0.2547 | 0.5944 | 0.1137 |
| edm | elastic_net__deep | 34 | 8.5080 | 10.6531 | 0.2671 | 0.6583 | 1.0766 |
| edm | ridge__deep | 34 | 8.5460 | 10.5990 | 0.2745 | 0.6477 | 0.0816 |
| edm | elastic_net__combined | 34 | 8.6496 | 11.1722 | 0.1940 | 0.5008 | 0.9526 |
| edm | ridge__combined | 34 | 8.6738 | 11.1644 | 0.1951 | 0.4880 | -0.1251 |
| edm | dummy__baseline | 34 | 12.8861 | 15.4663 | -0.5447 | não definida | 9.1844 |
| electro | elastic_net__baseline | 36 | 10.3125 | 12.3576 | 0.4266 | 0.8217 | -0.4067 |
| electro | ridge__baseline | 36 | 10.3104 | 12.3551 | 0.4269 | 0.8238 | -0.4332 |
| electro | elastic_net__traditional | 36 | 10.8474 | 12.5797 | 0.4058 | 0.7486 | -0.3551 |
| electro | ridge__traditional | 36 | 10.8483 | 12.5600 | 0.4077 | 0.7565 | -0.5781 |
| electro | elastic_net__deep | 36 | 10.4047 | 12.2165 | 0.4397 | 0.7883 | 0.8179 |
| electro | ridge__deep | 36 | 10.3259 | 12.0942 | 0.4508 | 0.7930 | -0.0030 |
| electro | elastic_net__combined | 36 | 10.7343 | 12.4900 | 0.4143 | 0.7365 | 0.6415 |
| electro | ridge__combined | 36 | 10.6400 | 12.3477 | 0.4276 | 0.7559 | -0.1618 |
| electro | dummy__baseline | 36 | 14.7244 | 17.6744 | -0.1729 | não definida | 6.7858 |
| emo | elastic_net__baseline | 148 | 7.6431 | 9.7001 | 0.2900 | 0.6065 | -0.0857 |
| emo | ridge__baseline | 148 | 7.6564 | 9.7126 | 0.2882 | 0.6049 | -0.1169 |
| emo | elastic_net__traditional | 148 | 7.4248 | 9.4023 | 0.3329 | 0.6066 | -0.1495 |
| emo | ridge__traditional | 148 | 7.4330 | 9.4143 | 0.3312 | 0.6076 | -0.1898 |
| emo | elastic_net__deep | 148 | 7.7113 | 9.7919 | 0.2765 | 0.5495 | -0.1060 |
| emo | ridge__deep | 148 | 7.7601 | 9.8540 | 0.2673 | 0.5436 | -0.2793 |
| emo | elastic_net__combined | 148 | 7.4441 | 9.4516 | 0.3259 | 0.5825 | -0.1455 |
| emo | ridge__combined | 148 | 7.4912 | 9.5082 | 0.3178 | 0.5781 | -0.2926 |
| emo | dummy__baseline | 148 | 9.4734 | 11.5419 | -0.0052 | não definida | 0.8323 |
| folk | elastic_net__baseline | 106 | 5.4243 | 6.8091 | 0.4572 | 0.7275 | -0.8196 |
| folk | ridge__baseline | 106 | 5.4382 | 6.8162 | 0.4561 | 0.7253 | -0.8318 |
| folk | elastic_net__traditional | 106 | 5.1715 | 6.5222 | 0.5020 | 0.7702 | -0.4224 |
| folk | ridge__traditional | 106 | 5.1997 | 6.5341 | 0.5002 | 0.7674 | -0.4955 |
| folk | elastic_net__deep | 106 | 5.2293 | 6.7373 | 0.4686 | 0.7413 | -0.4076 |
| folk | ridge__deep | 106 | 5.3362 | 6.7976 | 0.4591 | 0.7382 | -0.6764 |
| folk | elastic_net__combined | 106 | 5.1010 | 6.5581 | 0.4965 | 0.7653 | -0.1922 |
| folk | ridge__combined | 106 | 5.1978 | 6.6167 | 0.4875 | 0.7543 | -0.4634 |
| folk | dummy__baseline | 106 | 8.5595 | 10.7591 | -0.3552 | não definida | 5.5080 |
| funk | elastic_net__baseline | 35 | 7.1905 | 9.2038 | 0.2986 | 0.5900 | 1.0008 |
| funk | ridge__baseline | 35 | 7.2265 | 9.2061 | 0.2982 | 0.5869 | 0.8590 |
| funk | elastic_net__traditional | 35 | 7.1945 | 9.1375 | 0.3087 | 0.5617 | 0.5600 |
| funk | ridge__traditional | 35 | 7.1969 | 9.1199 | 0.3113 | 0.5600 | 0.3811 |
| funk | elastic_net__deep | 35 | 7.3982 | 9.5618 | 0.2430 | 0.5573 | 1.1803 |
| funk | ridge__deep | 35 | 7.4455 | 9.5408 | 0.2463 | 0.5461 | 0.5429 |
| funk | elastic_net__combined | 35 | 7.3050 | 9.2583 | 0.2903 | 0.5635 | 0.9749 |
| funk | ridge__combined | 35 | 7.2900 | 9.1940 | 0.3001 | 0.5728 | 0.3619 |
| funk | dummy__baseline | 35 | 8.3145 | 10.9896 | -0.0000 | não definida | -0.0206 |
| garage | elastic_net__baseline | 83 | 8.4809 | 11.4155 | 0.0247 | 0.1855 | 1.3573 |
| garage | ridge__baseline | 83 | 8.4823 | 11.4081 | 0.0260 | 0.1821 | 1.2754 |
| garage | elastic_net__traditional | 83 | 8.8328 | 11.6473 | -0.0153 | 0.1003 | 1.4350 |
| garage | ridge__traditional | 83 | 8.8321 | 11.6448 | -0.0148 | 0.0971 | 1.3665 |
| garage | elastic_net__deep | 83 | 8.5363 | 11.2353 | 0.0553 | 0.2013 | 1.7493 |
| garage | ridge__deep | 83 | 8.5432 | 11.2130 | 0.0590 | 0.1864 | 1.5118 |
| garage | elastic_net__combined | 83 | 8.6976 | 11.3557 | 0.0349 | 0.1478 | 1.8576 |
| garage | ridge__combined | 83 | 8.6834 | 11.3054 | 0.0435 | 0.1358 | 1.6016 |
| garage | dummy__baseline | 83 | 8.4830 | 11.6661 | -0.0185 | não definida | 1.5742 |
| goth | elastic_net__baseline | 69 | 7.7589 | 9.6555 | -0.0372 | 0.1594 | -0.3008 |
| goth | ridge__baseline | 69 | 7.7625 | 9.6563 | -0.0374 | 0.1553 | -0.2866 |
| goth | elastic_net__traditional | 69 | 7.7522 | 9.6992 | -0.0466 | 0.1822 | 0.5587 |
| goth | ridge__traditional | 69 | 7.7584 | 9.7147 | -0.0500 | 0.1913 | 0.6740 |
| goth | elastic_net__deep | 69 | 7.9906 | 9.9181 | -0.0944 | 0.1229 | -0.4483 |
| goth | ridge__deep | 69 | 8.0493 | 9.9609 | -0.1039 | 0.1158 | -0.0114 |
| goth | elastic_net__combined | 69 | 7.9781 | 9.9039 | -0.0913 | 0.1668 | 0.2093 |
| goth | ridge__combined | 69 | 8.0651 | 9.9883 | -0.1100 | 0.1620 | 0.5945 |
| goth | dummy__baseline | 69 | 15.4139 | 16.8775 | -2.1691 | não definida | -13.9630 |
| grindcore | elastic_net__baseline | 30 | 5.9206 | 7.8258 | 0.0467 | 0.4204 | 0.1918 |
| grindcore | ridge__baseline | 30 | 5.9465 | 7.8286 | 0.0460 | 0.4238 | 0.1438 |
| grindcore | elastic_net__traditional | 30 | 5.7170 | 7.4408 | 0.1382 | 0.4558 | -0.2822 |
| grindcore | ridge__traditional | 30 | 5.6594 | 7.4426 | 0.1377 | 0.4401 | 0.0725 |
| grindcore | elastic_net__deep | 30 | 6.7406 | 8.0679 | -0.0132 | 0.3077 | -1.5292 |
| grindcore | ridge__deep | 30 | 6.2567 | 7.8912 | 0.0306 | 0.3111 | -0.2001 |
| grindcore | elastic_net__combined | 30 | 6.3762 | 7.6422 | 0.0909 | 0.4722 | -1.7724 |
| grindcore | ridge__combined | 30 | 6.0222 | 7.4907 | 0.1265 | 0.4615 | -0.3331 |
| grindcore | dummy__baseline | 30 | 17.4592 | 19.1500 | -4.7086 | não definida | -17.3920 |
| groove | elastic_net__baseline | 32 | 6.4893 | 7.8231 | -0.6162 | 0.0667 | -1.7193 |
| groove | ridge__baseline | 32 | 6.4541 | 7.7948 | -0.6045 | 0.0700 | -1.5857 |
| groove | elastic_net__traditional | 32 | 5.9385 | 7.6236 | -0.5348 | 0.0564 | -1.1305 |
| groove | ridge__traditional | 32 | 5.9188 | 7.5728 | -0.5145 | 0.0393 | -0.8265 |
| groove | elastic_net__deep | 32 | 6.3567 | 7.9908 | -0.6863 | 0.0776 | -2.1916 |
| groove | ridge__deep | 32 | 6.3023 | 7.8098 | -0.6108 | 0.0792 | -1.1338 |
| groove | elastic_net__combined | 32 | 6.2030 | 8.1012 | -0.7332 | 0.0610 | -1.9096 |
| groove | ridge__combined | 32 | 6.1309 | 7.9272 | -0.6595 | 0.0778 | -0.8947 |
| groove | dummy__baseline | 32 | 11.7738 | 12.9533 | -3.4310 | não definida | -11.3983 |
| hard-rock | elastic_net__baseline | 57 | 6.9443 | 8.7627 | 0.0621 | 0.2945 | 1.3837 |
| hard-rock | ridge__baseline | 57 | 6.9535 | 8.7817 | 0.0580 | 0.2856 | 1.4607 |
| hard-rock | elastic_net__traditional | 57 | 7.1628 | 8.8282 | 0.0480 | 0.2758 | 0.9967 |
| hard-rock | ridge__traditional | 57 | 7.1865 | 8.8770 | 0.0375 | 0.2684 | 1.0999 |
| hard-rock | elastic_net__deep | 57 | 7.0561 | 8.7641 | 0.0618 | 0.2549 | 1.2110 |
| hard-rock | ridge__deep | 57 | 7.1086 | 8.9011 | 0.0322 | 0.2457 | 1.5789 |
| hard-rock | elastic_net__combined | 57 | 7.1662 | 8.7931 | 0.0556 | 0.2920 | 1.0328 |
| hard-rock | ridge__combined | 57 | 7.2414 | 8.9532 | 0.0209 | 0.2751 | 1.4083 |
| hard-rock | dummy__baseline | 57 | 8.8041 | 9.9914 | -0.2193 | não definida | -4.2376 |
| hardcore | elastic_net__baseline | 105 | 6.4997 | 7.9068 | 0.0500 | 0.3054 | 1.4990 |
| hardcore | ridge__baseline | 105 | 6.5042 | 7.9013 | 0.0513 | 0.3035 | 1.4391 |
| hardcore | elastic_net__traditional | 105 | 6.5388 | 8.0179 | 0.0231 | 0.2316 | 1.2761 |
| hardcore | ridge__traditional | 105 | 6.5475 | 8.0047 | 0.0263 | 0.2333 | 1.1886 |
| hardcore | elastic_net__deep | 105 | 6.4440 | 7.9126 | 0.0486 | 0.2836 | 1.5656 |
| hardcore | ridge__deep | 105 | 6.4721 | 7.8646 | 0.0601 | 0.2810 | 1.2677 |
| hardcore | elastic_net__combined | 105 | 6.3601 | 7.9143 | 0.0482 | 0.2636 | 1.3716 |
| hardcore | ridge__combined | 105 | 6.3935 | 7.8803 | 0.0563 | 0.2736 | 1.0608 |
| hardcore | dummy__baseline | 105 | 6.2751 | 8.1393 | -0.0067 | não definida | 0.6651 |
| hip-hop | elastic_net__baseline | 80 | 7.3738 | 8.9269 | 0.4421 | 0.6654 | 0.0441 |
| hip-hop | ridge__baseline | 80 | 7.3750 | 8.9260 | 0.4422 | 0.6649 | 0.1087 |
| hip-hop | elastic_net__traditional | 80 | 7.3900 | 8.8924 | 0.4464 | 0.6381 | 0.0673 |
| hip-hop | ridge__traditional | 80 | 7.3824 | 8.8654 | 0.4497 | 0.6416 | -0.0485 |
| hip-hop | elastic_net__deep | 80 | 7.4105 | 8.9483 | 0.4394 | 0.6304 | 0.2368 |
| hip-hop | ridge__deep | 80 | 7.4134 | 8.9309 | 0.4416 | 0.6355 | -0.2004 |
| hip-hop | elastic_net__combined | 80 | 7.4294 | 8.8808 | 0.4478 | 0.6273 | 0.3894 |
| hip-hop | ridge__combined | 80 | 7.4109 | 8.8409 | 0.4528 | 0.6287 | -0.0349 |
| hip-hop | dummy__baseline | 80 | 19.7568 | 22.7499 | -2.6237 | não definida | 19.3580 |
| indie-pop | elastic_net__baseline | 69 | 10.7950 | 13.2331 | 0.4251 | 0.7881 | -1.1501 |
| indie-pop | ridge__baseline | 69 | 10.7985 | 13.2393 | 0.4246 | 0.7875 | -1.1450 |
| indie-pop | elastic_net__traditional | 69 | 10.4277 | 12.8492 | 0.4580 | 0.8026 | -1.2707 |
| indie-pop | ridge__traditional | 69 | 10.4758 | 12.8885 | 0.4546 | 0.7999 | -1.4003 |
| indie-pop | elastic_net__deep | 69 | 10.6735 | 13.1061 | 0.4361 | 0.7857 | -1.2296 |
| indie-pop | ridge__deep | 69 | 10.7718 | 13.1730 | 0.4303 | 0.7858 | -1.6274 |
| indie-pop | elastic_net__combined | 69 | 10.4481 | 12.8591 | 0.4571 | 0.7975 | -1.2974 |
| indie-pop | ridge__combined | 69 | 10.5769 | 13.0026 | 0.4449 | 0.7978 | -1.7184 |
| indie-pop | dummy__baseline | 69 | 15.6684 | 19.5873 | -0.2596 | não definida | 8.8920 |
| industrial | elastic_net__baseline | 51 | 7.0910 | 8.7120 | 0.1453 | 0.4468 | -1.8321 |
| industrial | ridge__baseline | 51 | 7.0631 | 8.6996 | 0.1477 | 0.4482 | -1.7681 |
| industrial | elastic_net__traditional | 51 | 6.0161 | 7.8117 | 0.3128 | 0.6483 | -1.2239 |
| industrial | ridge__traditional | 51 | 5.9571 | 7.7993 | 0.3150 | 0.6412 | -1.0676 |
| industrial | elastic_net__deep | 51 | 6.7363 | 8.2709 | 0.2296 | 0.5515 | -1.7093 |
| industrial | ridge__deep | 51 | 6.5337 | 8.2080 | 0.2413 | 0.5465 | -1.0298 |
| industrial | elastic_net__combined | 51 | 6.1428 | 7.8506 | 0.3059 | 0.6043 | -1.1294 |
| industrial | ridge__combined | 51 | 6.0426 | 7.8569 | 0.3048 | 0.5954 | -0.4481 |
| industrial | dummy__baseline | 51 | 13.2491 | 14.8843 | -1.4949 | não definida | -11.5214 |
| metal | elastic_net__baseline | 39 | 6.6475 | 8.7224 | 0.0163 | 0.3314 | 1.2699 |
| metal | ridge__baseline | 39 | 6.6431 | 8.7194 | 0.0170 | 0.3335 | 1.2835 |
| metal | elastic_net__traditional | 39 | 6.9377 | 8.7383 | 0.0127 | 0.2892 | 1.1772 |
| metal | ridge__traditional | 39 | 6.9713 | 8.7113 | 0.0188 | 0.2884 | 0.9745 |
| metal | elastic_net__deep | 39 | 7.0217 | 8.9155 | -0.0277 | 0.2877 | 1.7306 |
| metal | ridge__deep | 39 | 7.0853 | 8.7695 | 0.0056 | 0.2931 | 0.9664 |
| metal | elastic_net__combined | 39 | 7.1481 | 8.8817 | -0.0199 | 0.2527 | 1.6530 |
| metal | ridge__combined | 39 | 7.2143 | 8.7372 | 0.0130 | 0.2703 | 0.8929 |
| metal | dummy__baseline | 39 | 12.7003 | 15.4479 | -2.0855 | não definida | 12.7003 |
| metalcore | elastic_net__baseline | 40 | 3.5831 | 4.3993 | 0.4631 | 0.7934 | -2.3743 |
| metalcore | ridge__baseline | 40 | 3.5477 | 4.3372 | 0.4781 | 0.7955 | -2.2613 |
| metalcore | elastic_net__traditional | 40 | 3.3939 | 4.2401 | 0.5012 | 0.7842 | -2.0842 |
| metalcore | ridge__traditional | 40 | 3.3521 | 4.1752 | 0.5164 | 0.7897 | -1.9549 |
| metalcore | elastic_net__deep | 40 | 4.0083 | 5.0849 | 0.2826 | 0.7704 | -3.3230 |
| metalcore | ridge__deep | 40 | 3.8559 | 4.8349 | 0.3515 | 0.7760 | -2.9048 |
| metalcore | elastic_net__combined | 40 | 3.7663 | 4.6587 | 0.3979 | 0.7847 | -2.7852 |
| metalcore | ridge__combined | 40 | 3.6274 | 4.5007 | 0.4380 | 0.7838 | -2.4113 |
| metalcore | dummy__baseline | 40 | 8.4702 | 9.8565 | -1.6953 | não definida | -7.8170 |
| power-pop | elastic_net__baseline | 63 | 4.8089 | 6.3085 | -0.0566 | 0.3566 | -1.1170 |
| power-pop | ridge__baseline | 63 | 4.8060 | 6.3085 | -0.0566 | 0.3640 | -1.1468 |
| power-pop | elastic_net__traditional | 63 | 5.0157 | 6.5016 | -0.1223 | 0.3007 | -0.9695 |
| power-pop | ridge__traditional | 63 | 4.9988 | 6.4670 | -0.1104 | 0.3008 | -0.8068 |
| power-pop | elastic_net__deep | 63 | 5.1341 | 6.6475 | -0.1732 | 0.2811 | -1.7798 |
| power-pop | ridge__deep | 63 | 4.9944 | 6.5294 | -0.1319 | 0.2782 | -1.2482 |
| power-pop | elastic_net__combined | 63 | 5.1577 | 6.8839 | -0.2582 | 0.2304 | -1.6962 |
| power-pop | ridge__combined | 63 | 5.1105 | 6.7726 | -0.2178 | 0.2318 | -1.1093 |
| power-pop | dummy__baseline | 63 | 19.1354 | 19.9137 | -9.5286 | não definida | -18.9444 |
| punk | elastic_net__baseline | 48 | 5.7571 | 7.4755 | 0.2808 | 0.6537 | 2.4174 |
| punk | ridge__baseline | 48 | 5.7287 | 7.4447 | 0.2868 | 0.6549 | 2.3195 |
| punk | elastic_net__traditional | 48 | 6.0267 | 7.8776 | 0.2014 | 0.6215 | 2.6215 |
| punk | ridge__traditional | 48 | 5.9886 | 7.7960 | 0.2179 | 0.6283 | 2.4248 |
| punk | elastic_net__deep | 48 | 6.5195 | 8.3242 | 0.1083 | 0.5905 | 3.1550 |
| punk | ridge__deep | 48 | 6.3457 | 8.0582 | 0.1644 | 0.5917 | 2.4523 |
| punk | elastic_net__combined | 48 | 6.6282 | 8.7825 | 0.0074 | 0.5697 | 3.5137 |
| punk | ridge__combined | 48 | 6.5247 | 8.5552 | 0.0581 | 0.5656 | 2.8362 |
| punk | dummy__baseline | 48 | 7.1257 | 9.3836 | -0.1331 | não definida | 3.2163 |
| punk-rock | elastic_net__baseline | 42 | 4.2348 | 5.7289 | 0.0842 | 0.3842 | -0.5732 |
| punk-rock | ridge__baseline | 42 | 4.2206 | 5.7242 | 0.0857 | 0.3850 | -0.4513 |
| punk-rock | elastic_net__traditional | 42 | 3.9531 | 5.2096 | 0.2427 | 0.4643 | -0.4965 |
| punk-rock | ridge__traditional | 42 | 3.9612 | 5.2207 | 0.2395 | 0.4662 | -0.2301 |
| punk-rock | elastic_net__deep | 42 | 4.1858 | 5.4925 | 0.1582 | 0.4552 | -1.0418 |
| punk-rock | ridge__deep | 42 | 4.0554 | 5.4905 | 0.1588 | 0.4525 | -0.0845 |
| punk-rock | elastic_net__combined | 42 | 4.0123 | 5.0721 | 0.2821 | 0.4728 | -0.8914 |
| punk-rock | ridge__combined | 42 | 3.9552 | 5.1043 | 0.2730 | 0.4635 | 0.0136 |
| punk-rock | dummy__baseline | 42 | 8.5170 | 9.8715 | -1.7192 | não definida | -7.8492 |
| singer-songwriter | elastic_net__baseline | 56 | 6.9038 | 8.8567 | 0.3472 | 0.6734 | -0.8516 |
| singer-songwriter | ridge__baseline | 56 | 6.8829 | 8.8492 | 0.3483 | 0.6710 | -0.7412 |
| singer-songwriter | elastic_net__traditional | 56 | 6.8712 | 8.6844 | 0.3724 | 0.6294 | -1.2283 |
| singer-songwriter | ridge__traditional | 56 | 6.8551 | 8.6789 | 0.3731 | 0.6244 | -1.0874 |
| singer-songwriter | elastic_net__deep | 56 | 6.9346 | 8.6543 | 0.3767 | 0.6580 | -0.8141 |
| singer-songwriter | ridge__deep | 56 | 6.9345 | 8.6453 | 0.3780 | 0.6597 | -0.3498 |
| singer-songwriter | elastic_net__combined | 56 | 6.9241 | 8.5571 | 0.3906 | 0.6380 | -1.3057 |
| singer-songwriter | ridge__combined | 56 | 6.8564 | 8.5172 | 0.3963 | 0.6256 | -0.7908 |
| singer-songwriter | dummy__baseline | 56 | 9.6939 | 11.6599 | -0.1314 | não definida | -3.9742 |
| ska | elastic_net__baseline | 33 | 4.1583 | 5.2519 | -0.0981 | 0.3822 | 1.6144 |
| ska | ridge__baseline | 33 | 4.1636 | 5.2633 | -0.1029 | 0.3785 | 1.6529 |
| ska | elastic_net__traditional | 33 | 4.2537 | 5.3894 | -0.1563 | 0.2797 | 1.9309 |
| ska | ridge__traditional | 33 | 4.2890 | 5.4551 | -0.1847 | 0.2927 | 2.1159 |
| ska | elastic_net__deep | 33 | 4.4588 | 5.5436 | -0.2235 | 0.2417 | 0.8368 |
| ska | ridge__deep | 33 | 4.6080 | 5.6700 | -0.2799 | 0.2683 | 1.5420 |
| ska | elastic_net__combined | 33 | 4.4329 | 5.4413 | -0.1787 | 0.2404 | 1.0834 |
| ska | ridge__combined | 33 | 4.6103 | 5.6367 | -0.2649 | 0.2463 | 1.7668 |
| ska | dummy__baseline | 33 | 10.5380 | 11.3413 | -4.1208 | não definida | -10.1738 |
| soul | elastic_net__baseline | 55 | 7.6313 | 9.3982 | 0.3524 | 0.6494 | -0.0627 |
| soul | ridge__baseline | 55 | 7.6471 | 9.4034 | 0.3517 | 0.6502 | -0.1310 |
| soul | elastic_net__traditional | 55 | 7.4952 | 9.2684 | 0.3702 | 0.6672 | -0.2909 |
| soul | ridge__traditional | 55 | 7.4808 | 9.2532 | 0.3722 | 0.6685 | -0.4039 |
| soul | elastic_net__deep | 55 | 7.6761 | 9.2876 | 0.3675 | 0.6445 | 0.0406 |
| soul | ridge__deep | 55 | 7.7231 | 9.3042 | 0.3653 | 0.6367 | -0.3419 |
| soul | elastic_net__combined | 55 | 7.6507 | 9.2854 | 0.3678 | 0.6322 | -0.0742 |
| soul | ridge__combined | 55 | 7.6959 | 9.3152 | 0.3638 | 0.6202 | -0.4783 |
| soul | dummy__baseline | 55 | 10.1101 | 12.3122 | -0.1115 | não definida | 3.8989 |
| swedish | elastic_net__baseline | 38 | 8.2813 | 9.8610 | 0.2723 | 0.5915 | 3.1747 |
| swedish | ridge__baseline | 38 | 8.3281 | 9.9137 | 0.2645 | 0.5772 | 3.3144 |
| swedish | elastic_net__traditional | 38 | 7.5949 | 9.2062 | 0.3657 | 0.7528 | 2.8786 |
| swedish | ridge__traditional | 38 | 7.6704 | 9.2868 | 0.3546 | 0.7570 | 3.0878 |
| swedish | elastic_net__deep | 38 | 7.9499 | 9.4694 | 0.3289 | 0.6253 | 2.7458 |
| swedish | ridge__deep | 38 | 8.2311 | 9.7950 | 0.2820 | 0.6055 | 3.4819 |
| swedish | elastic_net__combined | 38 | 7.5025 | 9.0842 | 0.3824 | 0.7419 | 2.7283 |
| swedish | ridge__combined | 38 | 7.7904 | 9.3951 | 0.3394 | 0.7349 | 3.5089 |
| swedish | dummy__baseline | 38 | 9.6057 | 11.5612 | -0.0003 | não definida | 0.1922 |

### Quantis do erro absoluto

| Modelo | Q25 | Mediana | Q75 | Q90 | Q95 |
|---|---|---|---|---|---|
| elastic_net__baseline | 2.8307 | 6.1039 | 10.1052 | 14.4882 | 18.0415 |
| ridge__baseline | 2.8453 | 6.1348 | 10.0865 | 14.5189 | 17.9574 |
| elastic_net__traditional | 2.7877 | 5.9180 | 10.1346 | 14.3920 | 18.1978 |
| ridge__traditional | 2.7985 | 6.0058 | 10.2008 | 14.3215 | 18.0545 |
| elastic_net__deep | 2.9670 | 6.1788 | 10.2169 | 14.4294 | 17.7591 |
| ridge__deep | 2.9064 | 6.0903 | 10.1384 | 14.4441 | 17.8128 |
| elastic_net__combined | 2.9023 | 6.0951 | 10.2613 | 14.5741 | 17.9836 |
| ridge__combined | 2.8936 | 6.0182 | 10.2339 | 14.3981 | 18.1865 |
| dummy__baseline | 4.9920 | 9.0080 | 15.9920 | 22.0080 | 26.0080 |

## Limitações

A inferência se restringe à amostra com letras aceitas, condicionada à disponibilidade, às regras de matching e à coleta. Falhas HTTP e ambiguidades podem gerar seleção. Há predominância do inglês; MiniLM pode representar outros idiomas com qualidade diferente. Os descritores LFM2b e os embeddings LRCLIB podem derivar de versões distintas da letra. Uma faixa Spotify representa cada composição, com chave operacional que não é identificador universal. As escolhas metodológicas foram orientadas pelos pilotos. O teste agrupado por artista avalia popularidade observada no snapshot da fonte; não é validação prospectiva de sucesso comercial nem demonstra previsão de sucesso futuro de lançamentos. As conclusões são preditivas e associativas, sem interpretação causal.

Não houve treinamento, retuning, clipping, calibração, exclusão ou substituição de registros. Alvo, previsões, resíduos e sorteios individuais permanecem privados. Códigos de saída, testes e auditorias são registrados no run summary.


## Discussão da magnitude e diagnósticos

O bloco traditional apresentou ΔMAE de -0.019798 ponto (-0.274859%) e ΔRMSE de -0.047781. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O bloco deep apresentou ΔMAE de 0.096067 ponto (1.333734%) e ΔRMSE de 0.085620. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O bloco combined apresentou ΔMAE de 0.065013 ponto (0.902595%) e ΔRMSE de 0.072835. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O intervalo ajustado do bloco profundo tem limite inferior de aproximadamente +0,000506 ponto, muito próximo de zero. Pelo critério congelado, o intervalo está acima de zero, mas a interpretação deve considerar a margem pequena e a precisão Monte Carlo de apenas 2.000 reamostragens. Não foram sorteadas reamostragens adicionais para alterar essa conclusão. Tradicional e Combinado incluem zero, sem demonstração de equivalência. O candidato elastic_net__traditional permanece o escolhido no desenvolvimento; Ridge mantém o papel secundário.

Os gráficos agregados revelam tendência à sobreestimação nos bins de baixa popularidade e subestimação nos de alta popularidade, condicionada ao bin observado. Essa inspeção é exploratória e não resultou em calibração ou clipping. No candidato Tradicional, resultados por período: 2000–2009: MAE 7.0209, n=713; 2010–2019: MAE 7.1849, n=1802; 2020 ou posterior: MAE 8.6411, n=77. A comparação do último período envolve poucos casos e não é validação prospectiva. Tabelas completas por gênero/período estão no relatório; somente células com n≥30 são publicadas.


## Verificação final

127 testes aprovados, 0 falhos, 0 ignorados; 11 testes sintéticos do avaliador aprovados antes da abertura do alvo. Ruff, formatação, git diff --check e verificações reais retornaram código 0. Alinhamento por chaves, métricas, multiplicidade dos sorteios, seed e quantis Bonferroni foram recalculados e conferidos exatamente. Os nove modelos e todos os artefatos congelados mantiveram seus hashes. A análise está concluída; chamadas posteriores reutilizam resultados e verificam sua integridade. Comandos e códigos completos constam no run summary.
