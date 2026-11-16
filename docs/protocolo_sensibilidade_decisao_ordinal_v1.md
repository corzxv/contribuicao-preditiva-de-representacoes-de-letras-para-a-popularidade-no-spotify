# Sensibilidade da regra de decisão — 05/11/2026 (D-027)

Análise exploratória definida depois dos resultados externos da classificação.
Motivação concreta: Combinado reconhece 40,75% das faixas elevadas operacionais,
com precisão de 72,38%; a regra principal argmax favorece a classe mais provável
por faixa e não é necessariamente ótima para a média das sensibilidades.
Não substituir o resultado principal ou alegar confirmação independente.

Duas regras fixas, sem grade, seleção ou ajuste a rótulos externos:

1. Principal original: argmax_k p(k|x).
2. Sensibilidade: argmax_k p(k|x)/pi_k, onde pi_k é a proporção da classe no
   treino externo correspondente, armazenada pela referência class_prior.

Derivação: acurácia balanceada é a média das sensibilidades; seu risco equivale
ao erro de classificação ponderado por inverso da prevalência de cada classe.
Para probabilidades condicionais verdadeiras e prevalências adequadas, a ação
de Bayes para esse risco maximiza p(k|x)/pi_k. Aqui são probabilidades estimadas
e calibração imperfeita; não há garantia de melhora nem validação da hipótese.
Não usar pesos originais de desenho como pi_k. Não usar a classe observada do
teste para estimar o prior aplicado àquela observação.

O comando verifica que a referência coincide com as proporções dos demais quatro
folds (treino externo), sem usar o fold avaliado. Isso é verificação de linhagem,
não ajuste novo. Desempates pela menor classe, como no resultado principal.
Escores p/pi servem apenas para decisão; não são publicadas novas probabilidades
normalizadas. Log-loss, Brier e calibração do modelo original permanecem iguais.

Reproduzir métricas principais antes de aplicar sensibilidade. Mesmas faixas,
componentes, folds, probabilidades e observações; acurácia, acurácia balanceada,
macro-F1, precisão/sensibilidade e erros extremos por regra. Pesos iguais na
análise principal; pesos originais apenas na avaliação separada, sem corrigir
seleção das letras. Não selecionar a regra por sensibilidade ponderada.

Modelos/hiperparâmetros foram escolhidos anteriormente para a regra original.
A nova regra é diagnóstico condicional das probabilidades existentes, não
avaliação de uma pipeline inteira ajustada para esse custo. Eventual adoção como
procedimento principal exigiria outro protocolo, participação do pesquisador
e validação adequada. Nenhum treino, recalibração, alteração do alvo, índice,
novo embedding, matching ou filtro de idioma é executado.

Script 36 lê o Parquet individual completo, portanto é executado manualmente
pelo pesquisador. Agente testa fixtures; saídas reais pendentes. Apenas agregados
em reports/sensibilidade_decisao_ordinal_200k_v1. Se interrupted, repetir o comando
com as mesmas fontes/código; o relatório só é concluído após conferir preservação.

Fundamento consultado em 05/11/2026: documentação oficial de
[acurácia balanceada](https://scikit-learn.org/stable/modules/model_evaluation.html#balanced-accuracy-score)
e [separação entre probabilidade e decisão](https://scikit-learn.org/stable/modules/classification_threshold.html).
A extensão multiclasse p/pi acima é derivação do risco especificado neste estudo,
não uma rotina binária de otimização de threshold aplicada ao teste.
