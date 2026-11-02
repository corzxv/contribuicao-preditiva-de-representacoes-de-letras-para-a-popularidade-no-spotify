# Resultados finais para a monografia — v0.6

## Método

Foram avaliados nove estimadores congelados no desenvolvimento: quatro Elastic Net primários, quatro Ridge secundários e DummyRegressor pela média de desenvolvimento. As configurações correspondem a metadados/áudio (Baseline), Baseline e 196 descritores LFM2b (Tradicional), Baseline e 384 dimensões MiniLM (Profundo), e os dois blocos textuais (Combinado). PCAs de 90% foram ajustadas separadamente dentro do desenvolvimento; nenhum pré-processamento foi ajustado no teste. O candidato predefinido elastic_net__traditional permanece inalterado.

As previsões brutas foram persistidas e seladas antes do acesso ao alvo. A popularidade foi projetada exclusivamente para os representantes congelados e unida por track_id e spotify_row_id, com join 1:1. MAE é primária; RMSE, R² e Spearman são secundárias/descritivas. Resíduo = observado − previsto; valor positivo indica subestimação. Spearman é não definida quando o vetor previsto é constante (Dummy). Previsões fora de 0–100 foram mantidas.

O bootstrap pareado por artista utiliza 2.000 reamostragens com seed 20261013. Sorteiam-se 1.308 grupos com reposição em cada reamostragem, incluindo todas as composições de cada grupo e preservando sua multiplicidade. Os mesmos sorteios são usados em todas as comparações; métricas permanecem ponderadas por composição. IC95% são descritivos. Nas três comparações primárias de MAE, usa-se Bonferroni: intervalos bilaterais de 98,333333% nos quantis 0,008333333 e 0,991666667. Ganho confirmado exige limite superior ajustado menor que zero. Os intervalos avaliam a incerteza do teste para modelos congelados e não toda a variabilidade de repetir o treinamento. Intervalo contendo zero não demonstra equivalência, ausência universal de efeito ou inutilidade das letras.


A avaliação final compreendeu 2592 composições e 1308 grupos de artista, sem interseção desses grupos com desenvolvimento. O alvo corresponde à popularidade Spotify observada no snapshot, na escala de 0 a 100.

## Resultados

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

## Contribuição incremental

| Modelo − Baseline | Primária | ΔMAE | ΔMAE % | IC95% ΔMAE | IC98,333333% ΔMAE | ΔRMSE | IC95% ΔRMSE |
|---|---|---|---|---|---|---|---|
| elastic_net__traditional | True | -0.0198 | -0.2749 | [-0.0947; 0.0537] | [-0.1147; 0.0725] | -0.0478 | [-0.1254; 0.0315] |
| elastic_net__deep | True | 0.0961 | 1.3337 | [0.0171; 0.1717] | [0.0005; 0.1872] | 0.0856 | [0.0063; 0.1634] |
| elastic_net__combined | True | 0.0650 | 0.9026 | [-0.0426; 0.1654] | [-0.0646; 0.1900] | 0.0728 | [-0.0396; 0.1833] |
| ridge__traditional | False | -0.0280 | -0.3889 | [-0.1030; 0.0433] | secundária; sem ajuste | -0.0558 | [-0.1344; 0.0200] |
| ridge__deep | False | 0.0775 | 1.0762 | [0.0102; 0.1465] | secundária; sem ajuste | 0.0513 | [-0.0207; 0.1230] |
| ridge__combined | False | 0.0475 | 0.6596 | [-0.0493; 0.1420] | secundária; sem ajuste | 0.0440 | [-0.0593; 0.1446] |

- traditional: ΔMAE=-0.0198 (-0.2749%); Ganho incremental não confirmado; o intervalo ajustado inclui zero. Isso não demonstra equivalência nem ausência universal de contribuição das letras.
- deep: ΔMAE=0.0961 (1.3337%); O intervalo ajustado indica erro maior que o Baseline nesta amostra; ganho incremental não confirmado.
- combined: ΔMAE=0.0650 (0.9026%); Ganho incremental não confirmado; o intervalo ajustado inclui zero. Isso não demonstra equivalência nem ausência universal de contribuição das letras.

## Relação com desenvolvimento

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

As diferenças entre desenvolvimento e teste refletem amostras e tamanhos de ajuste diferentes, não estabelecendo por si só overfitting. Os descritores LFM2b e as representações profundas MiniLM devem ser discutidos separadamente. As magnitudes absolutas e percentuais apresentadas precisam ser consideradas conjuntamente com os intervalos, para distinguir evidência estatística de relevância prática.

## Limites de generalização

A inferência se restringe à amostra com letras aceitas, condicionada à disponibilidade, às regras de matching e à coleta. Falhas HTTP e ambiguidades podem gerar seleção. Há predominância do inglês; MiniLM pode representar outros idiomas com qualidade diferente. Os descritores LFM2b e os embeddings LRCLIB podem derivar de versões distintas da letra. Uma faixa Spotify representa cada composição, com chave operacional que não é identificador universal. As escolhas metodológicas foram orientadas pelos pilotos. O teste agrupado por artista avalia popularidade observada no snapshot da fonte; não é validação prospectiva de sucesso comercial nem demonstra previsão de sucesso futuro de lançamentos. As conclusões são preditivas e associativas, sem interpretação causal.

Nenhuma referência bibliográfica foi acrescentada nesta síntese. Todas as quantidades derivam dos artefatos reais desta execução.


## Discussão da magnitude e diagnósticos

O bloco traditional apresentou ΔMAE de -0.019798 ponto (-0.274859%) e ΔRMSE de -0.047781. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O bloco deep apresentou ΔMAE de 0.096067 ponto (1.333734%) e ΔRMSE de 0.085620. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O bloco combined apresentou ΔMAE de 0.065013 ponto (0.902595%) e ΔRMSE de 0.072835. Essa magnitude deve ser contextualizada na escala 0–100 e no MAE do Baseline de aproximadamente 7,20 pontos; não foi estabelecido limiar externo de relevância prática.

O intervalo ajustado do bloco profundo tem limite inferior de aproximadamente +0,000506 ponto, muito próximo de zero. Pelo critério congelado, o intervalo está acima de zero, mas a interpretação deve considerar a margem pequena e a precisão Monte Carlo de apenas 2.000 reamostragens. Não foram sorteadas reamostragens adicionais para alterar essa conclusão. Tradicional e Combinado incluem zero, sem demonstração de equivalência. O candidato elastic_net__traditional permanece o escolhido no desenvolvimento; Ridge mantém o papel secundário.

Os gráficos agregados revelam tendência à sobreestimação nos bins de baixa popularidade e subestimação nos de alta popularidade, condicionada ao bin observado. Essa inspeção é exploratória e não resultou em calibração ou clipping. No candidato Tradicional, resultados por período: 2000–2009: MAE 7.0209, n=713; 2010–2019: MAE 7.1849, n=1802; 2020 ou posterior: MAE 8.6411, n=77. A comparação do último período envolve poucos casos e não é validação prospectiva. Tabelas completas por gênero/período estão no relatório; somente células com n≥30 são publicadas.
