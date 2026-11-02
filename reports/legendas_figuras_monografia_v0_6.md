# Legendas sugeridas — gráficos existentes da V0.6

Fonte de todos os gráficos: elaboração própria, avaliação final V0.6. As imagens
são cópias byte a byte dos quatro gráficos públicos já gerados. Não houve nova
avaliação, recálculo de métricas, ajuste, seleção ou modificação das figuras.
Baseline, Tradicional, Profundo e Combinado referem-se aos quatro Elastic Net
primários congelados. O Tradicional continua sendo o candidato predefinido no
desenvolvimento, independentemente dos resultados do teste.

## elastic_net_metrics.png

**Legenda sugerida:** MAE e RMSE dos quatro modelos Elastic Net congelados no
holdout de 2.592 composições. Os erros estão expressos em pontos da popularidade
Spotify registrada no snapshot; valores menores indicam menor erro agregado.

## primary_mae_adjusted_intervals.png

**Legenda sugerida:** Diferença de MAE entre cada bloco textual e o Baseline
(modelo menos Baseline), com intervalos ajustados por Bonferroni de 98,333333%
nas três comparações primárias. O bootstrap pareado por grupo de artista usou
2.000 reamostragens e seed 20261013. Valores negativos favorecem o modelo com
letras; a linha zero indica ausência de diferença pontual. Intervalo contendo
zero não demonstra equivalência nem ausência universal de contribuição das letras.
Os intervalos se referem à diferença agregada no teste, não a uma música individual.

## residual_distributions.png

**Legenda sugerida:** Distribuição dos resíduos dos quatro Elastic Net congelados
no holdout, definidos como popularidade observada menos prevista. Resíduo positivo
indica subestimação; negativo, sobreestimação. As previsões foram mantidas brutas,
sem clipping ou calibração após a avaliação.

## observed_predicted_aggregated.png

**Legenda sugerida:** Médias da popularidade observada e prevista por faixas fixas
de dez pontos de popularidade observada, incluindo somente faixas com pelo menos
30 composições. A diagonal indica igualdade entre observado e previsto. O gráfico
é um diagnóstico agregado condicionado ao valor observado, não uma avaliação
prospectiva ou um intervalo de previsão individual.

## Limites de interpretação

Os gráficos reutilizam o mesmo experimento encerrado. A avaliação é preditiva e
associativa, não causal. A amostra é condicionada à disponibilidade e aceitação
das letras e às regras de matching. Popularidade no snapshot não equivale a
sucesso comercial futuro. Nenhuma legenda implica novo teste independente.
