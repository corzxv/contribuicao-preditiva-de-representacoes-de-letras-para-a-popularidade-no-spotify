# Regressão no domínio observado — Ridge v1

## Evidência de entrada e objetivo

Script 21 executado pelo pesquisador em 8,323 s: 77.535 faixas preservadas, 77.051
vetores Float32 de 384 dimensões, finitude/hash/L2 conferidos integralmente, maior
erro de norma 5,96e-8; 21.893 componentes, maior 186. Zero células inválidas ou
ausentes nos 15 campos de Baseline. Cinco testes externos com 15.507 faixas cada;
treinos externos com 62.028; validações internas com 20.676, treinos internos com
41.352. Controles de separação aprovados, sem uso de alvo para construir folds.

Esta etapa usa exatamente esses casos/folds e compara quatro blocos com a mesma
família Ridge: Baseline, Tradicional, Profundo, Combinado. Acrescenta referências
média e mediana do treino externo. Não são quatro algoritmos distintos: estima-se
o incremento das representações dentro da família regularizada. Justificativa:
referência transparente, custo controlado e regularização comum; não se presume
ganho dos embeddings. Não treina rede neural ou ajusta o encoder. Não é escolha
guiada por resultados externos desta coorte, ainda não calculados na preparação.

Fontes seladas: resumo 21, seus quatro derivados privados e armazenamento vetorial
referenciado. Confere hashes/código/protocolo anteriores e alinha todas as dimensões
por text_input_sha256, nunca pela posição do vetor. Saídas em workspace novo;
não modifica 19/20/21 ou os experimentos antigos. Agente testa somente fixtures.

## Pré-processamento em cada treino

Listas explícitas de blocos da etapa 21; IDs, nomes, controles, idioma, pesos e
grupos não entram como preditores. Todas as dimensões profundas são usadas:
não ajusta PCA, seleção por correlação ou transformação escolhida pelos resultados.

Numéricas de Baseline, 21 descritores e dimensões profundas: imputação de mediana
seguida de StandardScaler, aprendidos somente no respectivo treino interno/externo.
Coluna completamente vazia recebe zero pelo imputer com keep_empty_features=True;
coluna constante é centrada para zero pelo scaler, sem usar informação da avaliação.
Isso trata text_no_lexical_segments constante, preservando o contrato da base.

Categorias: preencher nulo com __MISSING__ e OneHotEncoder sem drop, com categorias
aprendidas apenas no treino e handle_unknown=ignore. Categoria nova na avaliação
vira zeros nesse grupo. Dummies não recebem escala adicional. Nunca aprender
vocabulário, mediana ou média/DP globalmente antes da CV. Intercepto Ridge ajustado
e não penalizado. Não truncar previsões ao intervalo 0..100; registrar quantas
saem desse intervalo. Isso mantém o estimador fixo e torna a limitação visível.

## Ajuste e escolha interna

Ridge minimiza soma dos quadrados dos resíduos mais alpha vezes a norma quadrada
dos coeficientes. Ajuste com pesos iguais, sem sample_weight. Grade pré-fixada:
alpha = 0,1; 1; 10; 100; 1.000; 10.000. Mesmo conjunto nos quatro blocos.
Solver LSQR, tol=1e-5, max_iter=10.000, duas threads de bibliotecas numéricas.
Recurso operacional não autoriza alterar a família/grade pelo desempenho.

Dentro de cada treino externo, avaliar todos os seis alphas nos três folds
internos já fixados. Critério: soma dos erros absolutos internos dividida pelo
total de observações internas previstas, não média simples dos MAEs dos folds.
Em empate numérico exato, escolher maior alpha. Não arredondar para decidir empate.
Cada configuração precisa de todos os folds. Falha/convergência no limite
interrompe para diagnóstico; não comparar grade incompleta ou retunar no teste.
Selecionar alpha por MAE não altera a perda quadrática usada para ajustar Ridge.

Refazer pré-processamento e Ridge sobre todo o treino externo com alpha escolhido
internamente, prever o teste externo uma vez. Alvos externos não participam de
transformações/seleção. Referências média/mediana usam só a resposta do treino
externo, sem tuning. Não ajustar modelo final em toda a coorte automaticamente.

Escala completa: 360 ajustes internos (4 blocos × 5 externos × 3 internos × 6
alphas), 20 refits externos Ridge e dez referências. São 390 ajustes no total;
transforms são reutilizados entre alphas dentro de um mesmo treino interno, nunca
entre folds. A seleção continua independente para cada bloco/treino externo.

## Métricas e sensibilidade aprovadas em D-017

Após todas as 20 partes Ridge e dez referências, reunir uma previsão externa
por faixa e por variante nas mesmas 77.535 observações. MAE não ponderado é
primário; RMSE e R² não ponderados complementares, calculados sobre previsões
externas reunidas. R² com denominador zero é indefinido/null; não substituí-lo
por evidência de bom ajuste. Não fazer média dos R² por fold.

MAE ponderado = soma(sampling_weight × erro absoluto) / soma(sampling_weight),
usando exatamente as mesmas previsões externas. Não retreina com pesos nem escolhe
alpha/modelo pela sensibilidade. Guardar estratos/pesos originais no arquivo 21
para descrição/cobertura; o peso do sorteio não corrige seleção por letras aceitas.

Comparações pareadas pré-fixadas: Tradicional−Baseline, Profundo−Baseline,
Combinado−Baseline, Combinado−Tradicional e Combinado−Profundo, tanto em MAE
principal quanto ponderado. Delta negativo indica menor erro na primeira opção.
Esses contrastes respondem a incrementos específicos; não escolher depois apenas
o contraste favorável. Nenhuma inferência de catálogo ou causalidade.

Nesta primeira execução as diferenças são descritivas. Não produzir p-valores
ou intervalos ingênuos tratando faixas/folds como réplicas independentes. Método
de incerteza que respeite grupos e dependência da CV será declarado antes de
usá-lo para conclusões inferenciais. Teste v0.6 já exposto em 14/10/2026; nova CV
não restaura confirmação independente. Revisão semântica dirigida permanece
distinta da integridade técnica e do desempenho preditivo.

## Smoke, escala e retomada

Smoke manual: seleciona até 20 componentes completos e 240 faixas por fold externo
(máximo 1.200 observações), por ordem SHA-256 de seed/componente, sem usar alvo.
Preserva os folds originais. Executa somente fold externo 0, mas os três internos
e a grade completa nos quatro blocos, além das duas referências: 78 ajustes.
Recarrega modelos próprios com hashes conferidos e repete cinco previsões por
bloco, diferença máxima tolerada 1e-8. É teste técnico; não publicar ranking/MAE
como avaliação científica nem usar seu custo para prometer duração da escala.

All exige smoke completo sob mesmo selo. Primeiro lote de produção recomendado:
all --limit-outer-blocks 1. A ordem operacional é Combinado, Profundo, Tradicional,
Baseline em cada fold; o primeiro lote mede o Combinado no externo 0, com 18
ajustes internos + refit e duas referências. Usa o bloco com mais entradas para
informar custo sem tomar Baseline como medida dos embeddings. Não é garantia
de tempo dos demais blocos/folds. Preserva referências/ajustes e não conta
referências no limite. Estimar custo sem mudar protocolo por erros externos. Depois all sem
limite retoma as 20 partes; não executá-lo automaticamente após smoke.

Checkpoint SQLite por ajuste interno concluído, com assinatura do payload;
modelos/previsões por parte externa privados com hashes e manifesto publicado
por último. Interrupção pode repetir apenas o ajuste em curso e preparação de
matriz do treino interno, não os ajustes já confirmados. Partes com hashes
divergentes bloqueiam, sem descarte/reconstrução silenciosos. Um processo por vez.

Saídas públicas separadas smoke/integral; métricas globais somente quando todas
as partes estiverem prontas. Parcial completed=false e saída 2 são esperados no
lote limitado. Smoke mantém gate falso até reprodução aprovada. Código, protocolo,
grade, bibliotecas e entradas entram no selo: preservar depois da execução real.
Agente não executa smoke/treino real; pesquisador usa PowerShell conforme guia.

## Fontes técnicas

Documentação oficial consultada em 01/11/2026: [Ridge, penalização e solver LSQR](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html)
e [prevenção de vazamento no pré-processamento](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
Bibliotecas locais/testes registram compatibilidade efetiva; os documentos não
certificam adequação da família ao corpus ou ganho incremental.
