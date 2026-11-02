# Base comum e folds do domínio observado — v1

## Escopo e fontes

Preparação posterior às etapas 17/19/20, sem encoder, recuperação de letras ou
ajuste de modelos. Mantém as 77.535 faixas aceitas, pesos e campos originais.
Fontes: coorte_descritores.parquet, índice/vetores integrais e resumos completos
de 19/20. Confere selos anteriores, hashes, vínculos 1:1 por track_id e m:1 por
input textual; audita os vetores existentes por lotes contra hashes do checkpoint,
dimensão 384, finitude e norma L2 com tolerância 1e-5. Não lê letras nem pesos do
encoder. Saídas em diretório privado novo, sem modificar dados anteriores.

## Resposta e quatro blocos

spotify_popularity é coluna nova Float64 derivada de popularity: inteiro finito
entre 0 e 100. Popularidade inválida interrompe, sem excluir casos. Não usa views
do Genius, playcount LFM, IDs, nomes de artistas/faixas, controles de matching,
idioma, pesos, grupos ou exposição histórica como preditores. Nenhum alvo histórico
é carregado. A resposta permanece a popularidade observada no snapshot, sem causa.

Manifesto privado define, sobre as mesmas linhas e folds:

- Baseline: 15 metadados/acústicas em colunas novas model_*.
- Tradicional: Baseline + 21 descritores textuais congelados na etapa 19.
- Profundo: Baseline + 384 dimensões do encoder congelado na etapa 20.
- Combinado: Baseline + os dois blocos de letras.

Não duplica quatro matrizes volumosas nem copia os vetores: o manifesto referencia
o armazenamento único selado por text_input_sha256. Sua ordem deve ser alinhada
por chave antes de qualquer modelo futuro; posição de linha não é identificador.

Numéricas de Baseline: year, danceability, energy, loudness, speechiness,
acousticness, instrumentalness, liveness, valence, tempo, duration_ms.
Categorias: genre, key, mode, time_signature. Inteiros categóricos são representados
por strings; key=-1 preservado como categoria operacional de chave não detectada.
Não interpretar distâncias ordinais entre essas categorias. Ano é informação
retrospectiva do snapshot; não alegar validação temporal ou previsão de lançamentos.

## Conversões sem aprender com a coorte

Originais imutáveis; todos os preditores derivados ganham prefixo model_. Trimming
de espaços externos para parsing, sem aprender vocabulário, estatísticas ou faixas.
Branco/nulo torna-se nulo. Texto numérico não interpretável ou não finito torna-se
nulo apenas na coluna nova. Regras operacionais pré-fixadas:

- danceability/energy/speechiness/acousticness/instrumentalness/liveness/valence: [0,1].
- year: inteiro de quatro dígitos [1000,9999], sem limite escolhido pelos dados.
- key: inteiro [-1,11]; mode: inteiro [0,1]; time_signature: inteiro [0,7].
- tempo: >=0; duration_ms: >0; loudness: qualquer valor finito.
- genre: string com espaços externos removidos, sem agrupamento de categorias.

São regras de parsing/domínio operacional, não garantia de qualidade musical.
Os valores não brancos rejeitados pelas regras são contados por campo e registrados
privadamente por track_id/campo em metadados_invalidos.parquet. Valores originais
permanecem na coorte e nenhuma faixa é descartada. Não imputar, escalar, codificar
categorias, remover constantes, ajustar PCA ou escolher variáveis nesta etapa;
essas operações futuras pertencem a cada treino interno/externo. A constante
text_no_lexical_segments permanece no contrato até tratamento dentro do treino.

## Componentes e CV aninhada 5x3 já aprovada

Reutiliza e confere componentes da etapa 19: artista conservador, participações
feat./ft. explícitas, composição operacional e textos estritos iguais. Não são
identificadores universais; pseudônimos/versões não detectados permanecem limitação.
Audita ainda que inputs normalizados iguais pertençam ao mesmo componente. Falha
de identidade/alinhamento interrompe, sem corrigir ou excluir silenciosamente.

Atribui componentes inteiros aos cinco folds externos, sem usar alvo, idioma,
pesos ou métricas. Ordena componentes por tamanho decrescente e desempata por
SHA-256(seed + separador nulo + identificador); aloca ao fold com menos faixas,
depois menos componentes, depois desempate SHA-256. Seed externa 20261101.
Reaplica o algoritmo em cada treino externo para três folds internos, seeds
20261101+1000+fold_externo. Reprodutível e invariável à ordem das linhas.
Equilibra contagens, não é estratificação pelo alvo ou amostra probabilística.

folds_5x3.parquet privado: track_id, text_component_id, outer_fold (0..4) e
inner_outer_0..4 (0..2 no respectivo treino; -1 no teste externo). Os testes
externos não entram nos respectivos folds internos. Audita separação dos grupos,
cobertura e contagens; quatro blocos usam o mesmo arquivo, sem novo sorteio.
Folds pequenos/impossíveis interrompem; nenhum rearranjo guiado pelo desempenho.

As flags de exposição v0.6 são preservadas e agregadas por partição. Abertura
histórica em 14/10/2026 continua declarada: nova CV não cria confirmação independente.

## Limites, pesos e execução

Domínio analítico observado com letras aceitas, sem representatividade presumida
do catálogo ou de todas as músicas com letras. Amostra original de 200 mil e pesos
continuam para descrição/cobertura/seleção. Confere probabilidades e reciprocidade
dos pesos, preserva-os; não os aplica na preparação. Política aprovada em D-017:
ajuste com pesos iguais por faixa; seleção por MAE não ponderado; MAE primário
nas previsões externas, com RMSE e R² não ponderados complementares. Sensibilidade:
MAE ponderado pelos pesos amostrais originais, nas mesmas observações/previsões
externas/folds, sem retreinar ou selecionar pelo resultado ponderado. Estimando
principal é desempenho preditivo médio na distribuição empírica do domínio
observado, sob a validação agrupada aprovada. Ponderação só na avaliação de
sensibilidade é distinta de ponderar o treinamento. Não alegar correção automática
da disponibilidade de letras. Detalhes para a monografia em
metodologia_modelagem_200k_v1.md; nenhum modelo é ajustado aqui.
Integridade técnica não mede precisão semântica do matching nem ganho preditivo.

Execução integral manual pelo pesquisador. Agente testa somente fixtures pequenas.
Reexecutar o mesmo comando refaz apenas auditoria/montagem/folds determinísticos,
sem inferência de encoder; saídas com selo diferente são preservadas e bloqueadas.
Resumo completed=true é publicado por último, com hashes dos derivados privados.
Nenhum treino automático ao finalizar. Protocolo e código entram no selo; depois
da execução real não os editar para atualizar status, usar o guia/estado externo.
