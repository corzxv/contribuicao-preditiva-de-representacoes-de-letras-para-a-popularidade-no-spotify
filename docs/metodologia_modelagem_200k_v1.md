# Texto metodológico — domínio observado e avaliação preditiva

Preparação para a monografia; decisão de ponderação aprovada pelo pesquisador
em 01/11/2026, D-017. Resultados Ridge concluídos e conferidos em 02/11/2026. Não substituir
silenciosamente os resultados da integração Spotify–LFM2b antiga por estes números.

## Domínio, estimando e unidade

A análise principal compreende as 77.535 faixas com letras aceitas na versão v2
da recuperação local, provenientes da amostra original de 200.000 faixas. Trata-se
do domínio analítico observado. Sua disponibilidade textual não constitui, por
si, mecanismo probabilístico de seleção representativo de todas as músicas com
letras ou do catálogo da fonte. A resposta é a popularidade Spotify observada
no snapshot; o objetivo é avaliar associação e contribuição preditiva incremental,
sem interpretação causal ou promessa de popularidade futura.

O estimando principal é o desempenho preditivo médio na distribuição empírica
desse domínio, sob o procedimento de validação por grupos definido abaixo. Cada
faixa recebe peso igual no ajuste e na avaliação principal. Isso não equivale a
dar o mesmo peso a cada artista ou componente: componentes maiores contribuem
com mais faixas. Não extrapolar o risco estimado a artistas, épocas, músicas ou
populações fora das condições observadas sem hipóteses adicionais explícitas.

## Comparação pareada e prevenção de vazamento

Baseline reúne 15 campos de metadados/acústicas; Tradicional acrescenta 21
descritores lexicais/estruturais do próprio texto; Profundo acrescenta embeddings
multilingues de 384 dimensões; Combinado acrescenta ambos. As quatro configurações
utilizam as mesmas observações e partições. Campos de controle, pesos, IDs,
nomes, hashes e informações de matching não entram como preditores.

A validação cruzada é aninhada e agrupada, com cinco folds externos e três
internos. Componentes conexos preservam artistas conservadores, participações
explícitas, composições operacionais e textos iguais, segundo as regras congeladas
da etapa 19. A atribuição equilibra contagens por componente sem utilizar o alvo.
Testes externos ficam fora da escolha de hiperparâmetros e do ajuste interno.
Imputação, codificação de categorias, escala, remoção de constantes e eventual
redução de dimensão devem ser aprendidas apenas no respectivo treino. Embeddings
foram obtidos com encoder pré-treinado congelado, sem ajuste pela popularidade.

Cada faixa deverá ter uma previsão externa, produzida pelo modelo que não usou
seu componente no ajuste. Esses resultados serão avaliados de forma pareada
entre blocos. Os grupos são operacionais, sujeitos a pseudônimos/colaborações/
versões não detectados. O teste histórico v0.6 já havia sido aberto em 14/10/2026;
esta avaliação deve declarar a exposição e não ser apresentada como nova confirmação
independente. A integridade dos arquivos não certifica precisão semântica do matching.

## Métricas principais e seleção

Seleção de hiperparâmetros e comparação principal por MAE não ponderado. Se
e_i = y_i - previsão_externa_i e n = 77.535, então:

- MAE = soma(|e_i|) / n;
- RMSE = raiz(soma(e_i²) / n);
- R² = 1 - soma(e_i²) / soma((y_i - média(y))²).

RMSE e R² são complementares, não critérios para escolher retrospectivamente
o resultado mais favorável. As métricas globais são calculadas sobre as previsões
externas reunidas, não pela média simples de R² dos folds. Resultados por fold
auxiliam o diagnóstico; métricas futuras devem verificar cobertura 1:1 das previsões.
Qualquer quantificação de incerteza deve respeitar dependência por componentes
e o desenho da CV; não tratar erros das faixas ou dos folds como réplicas
independentes por conveniência. O método específico será declarado antes de
usar intervalos/testes para concluir sobre ganho incremental.

## Sensibilidade à ponderação

Preservam-se os estratos, probabilidades de inclusão e pesos amostrais originais
para descrição, cobertura e diagnóstico de seleção. Na sensibilidade preditiva,
usar exatamente as mesmas observações, folds, modelos ajustados com pesos iguais
e previsões externas da análise principal. Calcular:

MAE_ponderado = soma(w_i |e_i|) / soma(w_i), com w_i = sampling_weight original.

Comparar a diferença de MAE entre cada bloco e sua referência tanto com pesos
iguais quanto com os pesos originais, verificando se direção, magnitude e
interpretação do incremento mudam. Isso é ponderação na avaliação; não implica
retreinamento ponderado ou seleção de hiperparâmetros pela métrica de sensibilidade.
Um treino ponderado seria outro procedimento, a ser planejado separadamente.

Os pesos originais refletem o sorteio inicial, não a probabilidade de obter letra
aceita. Sua aplicação ao subconjunto observado não corrige automaticamente o viés
de disponibilidade das letras nem identifica desempenho no catálogo inteiro.
O MAE ponderado é tratado como diagnóstico de sensibilidade à reponderação dos
casos observados. Qualquer ampliação inferencial posterior exigirá estimando,
hipóteses de seleção/positividade, avaliação de cobertura e limitações explícitas.

## Situação de execução

Etapas 17, 19, 20 e 21 concluídas pelo pesquisador. A base comum e os folds 5×3
foram auditados em 21: 77.535 casos, cinco avaliações externas de 15.507 faixas,
zero metadados ausentes/inválidos e 21.893 componentes, maior 186. O script 22
foi preparado e testado em fixtures pelo agente para a primeira comparação Ridge nos
quatro blocos, com referências média/mediana e grade interna de seis alphas.
Procedimento completo no protocolo_regressao_200k_v1.md, congelado antes de
qualquer métrica externa recente. Smoke real de 22 agora concluído em 318 faixas,
com reprodução exata das previsões: é teste técnico sem conclusão de desempenho
no domínio. Produção integral agora concluída: 20 partes Ridge, dez referências,
77.535 previsões por variante. MAEs 8,3525/8,2957/8,1285/8,1151, Combinado com
redução 2,842% frente ao Baseline (ponderada 2,781%); mesma ordenação.
Interpretação em reports/interpretacao_modelagem_200k_v1.md, descritiva e sem IC.
Diagnósticos 23 executados: métricas reproduzidas, ganhos nos cinco folds e na
retirada condicional de componentes, com exceções de subgrupos e alto erro na
cauda de popularidade. Exploratórios, sem novos modelos/IC/p-valores. Material
24 para escrita gerado somente dos agregados: trecho parcial e figuras, sem
equivaler à monografia completa. A conclusão técnica
dos dados não substitui revisão dirigida do matching ou avaliação empírica dos modelos.
