# Coorte ampliada com letras aceitas: protocolo estatístico exploratório

Preparado em 28/10/2026, antes de executar a descrição ou o treinamento desta rodada.
Esta etapa não foi executada pelo assistente. A execução real é manual. O protocolo e
o código serão selados por SHA-256 no comando 09; alterações posteriores invalidam a retomada.

## O que os resultados anteriores realmente mostraram

Na V0.6, n=2.592 no teste: referência constante MAE 11,116393; Elastic Net Baseline
MAE 7,202885, RMSE 9,257271, R² 0,556792; Tradicional MAE 7,183087, RMSE 9,209490,
R² 0,561355. O desempenho deve ser julgado frente à referência e à finalidade, não
como simplesmente bom ou ruim. O incremento dos descritores foi pequeno; isso é
diferente de afirmar que o modelo não aprendeu nada. Fonte local:
`reports/final_holdout_metrics_v0_6.csv`.

V0.8 já comparou regressão com spline no ano e histogram gradient boosting em 7.648
composições de desenvolvimento. O boosting Baseline diminuiu MAE de 7,0940 para
6,9013, mas aumentou P95 de 18,1946 para 18,7516 e erros >20 de 284 para 319.
Nenhuma alternativa satisfez integralmente o critério operacional de avanço.
Fontes: `reports/revisao_estatistica_v0_8.md` e seu CSV de métricas.

V0.9 ampliou somente os treinos, mantendo aquelas 7.648 observações OOF. No máximo,
Baseline teve MAE 7,165120, RMSE 9,184520, R² 0,53274; Tradicional MAE 7,047780,
RMSE 9,048948, R² 0,54643. A diferença de MAE foi −0,117340 ponto, com melhora
nos cinco folds. Houve extrapolações graves em alguns treinos pequenos, inclusive
um valor padronizado extremo de `lfm_affective_liwc_filler`; isso não autoriza excluir
a variável ou o registro. Fonte: `reports/experimento_ampliacao_v0_9.md`.
Não foi localizado artefato de resultado CatBoost V0.10 nesta revisão; não presumir
que o pedido histórico foi executado.

## Pergunta e população

Estimar a popularidade Spotify observada no snapshot e avaliar contribuição preditiva
incremental dos descritores de letra. Sem causalidade ou previsão de sucesso futuro.
A auditoria 08 confirmou 78.323 consultas/faixas aceitas, 58.705 no desenvolvimento e
19.618 no holdout; são 78.280 hashes de texto distintos. Isso não é a contagem final de
composições. Não houve sobreposição exata de textos/artistas/composições entre splits.
A auditoria não é revisão humana de matching, semântica, idioma ou duplicatas aproximadas.

Usar somente faixas aceitas e auditadas. Escolher um representante por composition_key
operacional DENTRO do subconjunto aceito, pela função V0.4 existente: versão original
preferida, confiança e método de matching, score, completude e IDs como desempate.
A restrição a aceitas é nova e explícita; um representante pode diferir do escolhido
no universo completo. Não emprestar letras a versões sem compatibilidade. Conservar
todos os vínculos e informar quantas versões foram colapsadas. A unidade é a composição
operacional representada por uma gravação; a chave não é identidade musical universal.

Não redividir o split original nem mover faixas do holdout para treino. Os 19.618
registros do holdout terão apenas metadados verificados. Alvos serão projetados somente
após filtro development_train. A nova amostra aceita é condicionada à cobertura LRCLIB;
descrever cobertura por gênero, ano e resposta somente no desenvolvimento. Não afirmar
representatividade do universo musical. Descritores LFM2b não são recalculados e podem
se referir a versão textual diferente da letra LRCLIB: registrar essa limitação.

## Distribuição e interpretação estatística

Começar com distribuição empírica, quantis, assimetria, curtose, extremos, massa em 0
e 100, ausências e relações bivariadas. O histograma marginal de Y não determina
P(Y|X). MQO estima uma média condicional linear; normalidade marginal da resposta ou
das preditoras não é requisito para ajustar MQO. Hipóteses dos erros e dependência
importam para a inferência clássica. Verificar resíduos OOF, heterogeneidade de erros,
curvatura e calibração descritiva. Não aplicar testes de normalidade a milhares de
observações para escolher automaticamente um algoritmo. Fundamentação:
[Penn State, Regression Methods, Lesson 4](https://online.stat.psu.edu/stat501/Lesson04).

Popularidade 0–100 é um índice, não contagem de eventos; Poisson/negativa binomial
não são justificadas apenas por valores inteiros. Dividir por 100 não a transforma
em uma proporção binomial com denominador conhecido. Regressão beta usual tem suporte
aberto (0,1), exigindo tratar fronteiras e justificar a hipótese; não deslocar zeros
e uns artificialmente nesta rodada. Modelos de duas partes ou distribucionais podem
ser considerados em protocolo posterior se houver mecanismo substantivo plausível.
Referência: [BetaModel, statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.othermod.betareg.BetaModel.html).

Elastic Net JÁ É regressão linear regularizada. Ridge estabiliza coeficientes correlacionados;
Elastic Net combina penalidades L1/L2. Não confundir regressão com uma alternativa
a todo aprendizado de máquina. Comparar formas funcionais com validação adequada é
mais informativo que procurar a distribuição que mais se parece com o histograma.
[Scikit-learn, modelos lineares](https://scikit-learn.org/stable/modules/linear_model.html).

## Descrição a produzir pelo script 09

- Inventário dos 23 atributos Baseline e 196 LFM2b autorizados pelo manifesto V0.5,
  com dicionário existente, sem inventar descrições.
- Tamanho da coorte por faixa, composição, artista e componente de dependência;
  perdas por colapso de versões e cobertura de aceitação na população de desenvolvimento.
- Ausências/não finitos, cardinalidade, quantis, média, desvio, assimetria, curtose;
  frequências de categorias e de faixas de popularidade, com denominadores.
- Spearman com Y e pares de preditoras com |rho|≥0,8 e pelo menos 30 pares completos.
  São descrições exploratórias, não filtros de variáveis nem testes de significância.
- Histograma, ECDF e QQ marginal (explicitamente distinto de QQ dos resíduos).

Não fazer seleção pelo alvo, remover outliers por erro, imputar na descrição ou
atribuir significados não documentados. Sem alterar dados de entrada.

## Preparação, famílias e grade fechada

Baseline: 23 atributos. Tradicional: os mesmos 23 + 196. Identificadores, artista,
título, matching, indicadores de coleta, Genius views e LFM playcount nunca entram em X.
Ambos usam as mesmas linhas. `key`, `time_signature` e `genre`: categorias nominais,
one-hot aprendido dentro de cada treino, referência omitida; desconhecidos codificados
com zeros e ausência por marcador. `mode` e flags: binários. Ausências numéricas e
não finitos: mediana do respectivo treino; colunas inteiramente ausentes preservadas
como zero após imputação. Numéricas padronizadas somente no treino. Sem PCA nesta rodada.

| Família | Hipótese/pergunta | Configurações por bloco |
|---|---|---|
| Referências média e mediana | Quanto melhora sobre previsão constante? | Ajustadas somente no treino externo |
| MQO/OLS | Relações aditivas lineares sem regularização | Uma configuração, descritores originais |
| Ridge | Redundância/instabilidade dos coeficientes lineares | alpha 1, 100, 1000 |
| Elastic Net | Regularização com possível esparsidade | alpha 0,03/0,3 × l1_ratio 0,1/0,8 |
| Aditiva Ridge | Curvatura aditiva além do ano | Splines cúbicas, 5 nós uniformes por variável contínua; alpha 1, 100, 1000 |

Splines em year, danceability, energy, loudness, speechiness, acousticness,
instrumentalness, liveness, valence, tempo e duration_ms. Demais variáveis entram
linearmente/categoricamente. Nós são aprendidos no treino; extrapolação linear;
constantes detectadas somente no treino. É regressão em bases spline com Ridge,
não um GAM com parâmetros de suavização separados estimados por REML. Não alegar
inferência automática de efeitos. Fundamentação das bases aditivas:
[ISLP, Non-Linear Modeling](https://intro-stat-learning.github.io/ISLP/labs/Ch07-nonlin-lab.html).

No Tradicional, Ridge/Elastic Net/Aditiva comparam adicionalmente descritores LFM
originais versus asinh(x), antes da padronização. A asinh é monotônica, definida
em zero/negativos e comprime caudas; mantém todas as variáveis, inclusive filler.
Essa é uma mudança explícita de representação, motivada pela instabilidade anterior.
A escolha fica nos folds internos, não nos erros externos. OLS é referência original.
Não são estimados coeficientes causais nem valores-p após seleção regularizada.

Elastic Net: max_iter=20.000, tol=1e-4, seleção cíclica. Configuração com warning de
convergência não participa da escolha; se nenhuma for válida, interromper e registrar.
Não ampliar grade automaticamente em resposta às métricas. Previsões brutas sem clipping.

## Validação, seleção e incerteza

Construir componentes conexos considerando qualquer artista, composição, split_group
ou hash estrito/normalizado compartilhado, sobre todas as versões aceitas antes do
colapso. Cinco folds externos GroupKFold, shuffle=True, seed 20261028. Três internos
por treino externo, seeds 20261029+índice externo (0–4). Não usar Y para criar partições.
Estes são folds novos para a coorte nova; os folds V0.5/V0.9 originais não são alterados.
Validar ausência de sobreposição em todas as dimensões e persistir os índices.

Seleção pela média dos MAEs internos, folds com peso igual. RMSE/R² e cauda são
diagnósticos externos, sem tuning retrospectivo. MAE enfatiza a mediana condicional;
as famílias por mínimos quadrados modelam a média, portanto podem existir compromissos.
Referências média e mediana permitem observar isso. Não otimizar várias métricas
retrospectivamente para declarar um vencedor.

Avaliar cada família nos mesmos folds e também o procedimento `selected_inner`, que
escolhe a família exclusivamente dentro de cada treinamento externo. Esta última
comparação pode escolher famílias distintas nos dois blocos; a contribuição dos
descritores deve ser examinada principalmente dentro da mesma família.
A escolha pelo menor OOF entre diversas famílias é exploratória e não é avaliação
independente. [Cawley e Talbot (2010)](https://www.jmlr.org/papers/v11/cawley10a.html)
explicam o viés de seleção; [exemplo de CV aninhada](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)
separa ajuste interno e avaliação externa.

Entrega: MAE/RMSE/R², mediana/P90/P95 do erro absoluto, erros >20, extremos e previsões
fora de 0–100, global/fold/faixa do alvo com denominadores (sem R² nas faixas).
Diagnósticos OOF de resíduos, QQ, escala-localização, erros por ano/gênero e calibração
descritiva; nenhuma calibração aplicada. Faixas com n<30 marcadas.
Diferenças pareadas T−B e IC percentil 95% com 1.000 bootstraps de componentes completos
para ΔMAE, ΔRMSE e Δproporção de erros >20. IC condicionado às previsões OOF fixas;
não refaz o treino e não representa toda a incerteza de seleção. Folds não são cinco
experimentos independentes. Sem teste t ingênuo de cinco métricas nem p-values em massa.

## O que muda e o que permanece exploratório

Aqui a validação também se amplia, ao contrário da V0.9. Logo, não atribuir diferença
de métricas em relação à V0.9 somente ao algoritmo. Dentro da rodada nova as comparações
são pareadas. O holdout V0.6 já foi examinado; não chamá-lo de confirmação inédita.
Nenhum novo modelo final de produção será escolhido/refeito automaticamente, e o
demonstrador permanece congelado. Nesta rodada são persistidos somente os modelos de folds.

Embeddings serão etapa separada, com encoder/configuração congelados. A matriz e os
representantes desta rodada servirão de referência para comparar os quatro blocos nas
mesmas observações. Se houver falha de embeddings, não excluir silenciosamente linhas:
reparar ou declarar uma nova amostra comum e reavaliar TODOS os blocos.
O estudo [Prevedello et al., Lyrics for Success (2024)](https://aclanthology.org/2024.nlp4musa-1.13/)
investigou embeddings e descritores para popularidade 15 dias após lançamento em
12.428 faixas. É motivação para contribuição incremental; seu alvo, população e
atributos disponíveis diferem deste snapshot. Não importar métricas ou proxies proibidos.

## Execução e preservação

530 ajustes planejados: 480 internos e 50 externos, além de oito ajustes técnicos
de benchmark. Benchmark em até aproximadamente 3.000 linhas do treino externo 0,
com grupos inteiros (o último grupo pode ultrapassar o limite). Sem escolher parâmetros
pelo desempenho do benchmark. Uma tarefa por vez, quatro threads numéricas por padrão.
Tempo real deve ser medido; extrapolação linear de um lote pequeno não é garantia.

Checkpoints por família/bloco/fold externo; retomar refaz somente o componente
incompleto. Modelos e previsões privados; reprodução com atol=1e-8 e rtol=1e-10.
Arquivos de entrada, código, versões de bibliotecas, matriz e folds são selados.
Sem coleta, leitura de letras completas, embeddings, acesso à rede nos scripts,
alteração de pipeline anterior, commit ou push.
