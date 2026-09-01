# Plano de análise de PCA — Base v0.1.1

O orientador sugeriu PCA para estudar a estrutura dos componentes e a variabilidade. O PCA definitivo não é executado nesta etapa.

1. PCA maximiza a variabilidade das preditoras X, não da popularidade Y.
2. Para estudar popularidade, escores dos componentes poderão ser usados posteriormente como preditores em regressão.
3. O PCA será ajustado exclusivamente em `development_train` ou em folds internos desse conjunto.
4. Padronização e PCA serão aprendidos no treino e apenas aplicados ao holdout.
5. A análise apresentará scree plot, variância explicada individual e acumulada, loadings, interpretação, estabilidade e desempenho preditivo.
6. A prioridade é o bloco de descritores LFM2b; variáveis categóricas, IDs, grupos e alvo não serão misturados automaticamente.
7. PCA não substituirá automaticamente os descritores originais.
8. PCA será análise complementar ou representação alternativa.
9. A quantidade de componentes será escolhida somente no treinamento/validação cruzada.
10. Serão comparados: tradicional com descritores tratados; tradicional com componentes; e, se viável, combinado com componentes e embeddings.
