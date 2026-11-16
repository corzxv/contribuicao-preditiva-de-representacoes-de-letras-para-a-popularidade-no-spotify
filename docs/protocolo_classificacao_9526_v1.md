# Classificação da popularidade das 9.526 faixas com letra

A unidade de análise é a faixa da candidata v2. O objetivo é medir a
contribuição preditiva da letra, em conjunto com metadados e atributos
acústicos, para a popularidade no snapshot observado. O desempenho se
refere ao conjunto de faixas com letra vinculada. A amostra tem 5.548
faixas de popularidade baixa (0–19), 2.919 de média (20–39) e 1.059 de
alta (40–100). Os cortes são operacionais. A seleção inclui 9.033 faixas
da coorte histórica do projeto.

| Modelo | Preditores |
|---|---|
| Baseline | 15 variáveis de metadados e áudio |
| Tradicional | Baseline e 21 descritores lexicais e estruturais |
| Profundo | Baseline e 384 dimensões do embedding multilíngue E5 |
| Combinado | Baseline, descritores e embedding |

Os quatro modelos usam logística ordinal com chances proporcionais e
penalização L2. As variáveis numéricas recebem imputação pela mediana e
padronização. As categorias recebem codificação indicadora e tratamento
de níveis inéditos. Essas operações são ajustadas em cada treino. A versão
inicial usa os metadados diretamente. O valor da penalização é escolhido
entre 0,001, 0,01, 0,1 e 1 nas três divisões internas de cada treino externo.
O critério é a acurácia balanceada das previsões internas reunidas. Empates
favorecem a penalização mais forte. A classe prevista é a de maior probabilidade.

As cinco divisões externas e as três internas são comuns aos quatro modelos.
Os componentes reúnem faixas relacionadas por artista, participação explícita,
composição operacional ou hash textual estrito. O algoritmo equilibra os
tamanhos sem usar a popularidade para atribuir os componentes. A preparação
conferiu a presença das três classes em todas as partes de treino e avaliação.

A métrica principal é a acurácia balanceada, média das sensibilidades das
três classes nas previsões externas reunidas. As saídas incluem acurácia,
macro-F1, precisão e sensibilidade por classe, matriz de confusão, taxa de
erros entre classes extremas, log-loss, Brier multiclasse e calibração
descritiva. Uma referência usa as frequências do treino de cada divisão.
O ganho de cada bloco com letras é comparado ao Baseline nas mesmas faixas.
O ajuste e a avaliação principal dão peso igual por faixa. A avaliação de
sensibilidade usa o peso de desenho da candidata nas mesmas previsões.

## Execução

A preparação conferiu 9.500 textos únicos. O encoder tem 9.018 vetores
compatíveis pelo hash do texto normalizado e pela configuração selada.
482 vetores precisam ser gerados. Os 21 descritores são calculados dos
textos vinculados à amostra atual. O ajuste compara quatro penalizações em
três partes internas, cinco partes externas e quatro conjuntos de preditores.

Execute no PowerShell.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\57_classificar_amostra_9526.py"
```

Em caso de interrupção, o mesmo comando retoma os vetores e ajustes
concluídos. `reports/classificacao_9526_v1/resumo_classificacao.json` informa
a conclusão. `metricas_externas.csv` reúne as métricas. Os ajustes, as
divisões e as probabilidades individuais ficam em
`data/derived/private_classificacao_9526_v1`.
