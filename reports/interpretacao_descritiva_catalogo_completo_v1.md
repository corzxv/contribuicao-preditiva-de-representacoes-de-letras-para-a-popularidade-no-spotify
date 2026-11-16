# Interpretação da descrição completa do catálogo — 06/11/2026

Execução integral do script 39 realizada pelo pesquisador e conferida. O resumo
registra 1.159.764 faixas, 20 campos, 82 gêneros e aproximadamente 32,71 segundos.
O agente analisou exclusivamente agregados e figuras já produzidos; não releu
o CSV inteiro nem executou nova PCA sobre as faixas.

## 1. A população acessível e a qualidade dos campos

Há 1.159.764 IDs distintos, sem ausência de ID. Foram registradas 64.157 strings
de crédito de artista e 882.360 strings de título; esses totais não identificam
pessoas ou composições universais. Faltam quinze créditos e um título.
A população permanece o catálogo acessível da fonte, não todo o Spotify.

O dicionário documenta os vinte campos, incluindo o índice exportado, nomes e ID,
popularidade, ano/gênero e medidas acústicas/musicais. Nos campos numéricos não
foram registradas ausências ou falhas de conversão. Isso não equivale a qualidade
perfeita: há 1.199 valores de tempo iguais a zero, sinalizados pela regra local
positiva. Correspondem a 0,1034% do catálogo e permanecem na descrição bruta.

Em sleep, há 650 desses tempos zero, diferença entre 17.851 faixas do gênero
e 17.201 com BPM válido. São 3,64% desse gênero e 54,21% dos tempos zero do
catálogo. A restrição multivariada está concentrada em alguns perfis; sua pequena
proporção global não significa distribuição uniforme entre gêneros.

PCA e correlações utilizam 1.158.565 casos completos válidos. As 1.199 exclusões
são exclusivas dessas análises; nenhuma faixa foi eliminada da população.
Instrumentalness é uma estimativa acústica, não confirmação de ausência de letra.
O significado exato de year como primeiro lançamento e a data de medição da
popularidade continuam não confirmados.

## 2. As distribuições apresentam comportamentos diferentes

As médias devem ser acompanhadas de quantis e gráficos. Dançabilidade é mais
concentrada em torno de valores intermediários; energia tem forte presença em
escores altos. Caráter acústico e instrumentalidade se concentram perto de zero,
mas também incluem perfis altos. Presença de fala e indício de execução ao vivo
apresentam caudas à direita. Não há uma normalidade comum dos metadados.

A duração mediana é 225,74 segundos, com P95 de 448 e P99 de 654,25 segundos,
enquanto o máximo é 6.000,50 segundos. Esse extremo comprime a região típica
no histograma de amplitude completa. Não é prova de erro e não foi removido.
Para o texto acadêmico, usar quantis/boxplots junto ao histograma, explicitando
as unidades. A intensidade sonora varia de -58,1 a 6,172 dB na fonte, sem impor
retroativamente um limite adicional para tornar o conjunto mais regular.

Resumo do escopo de valores finitos brutos; duração convertida para segundos:

| Variável | Média | DP populacional | P25 | Mediana | P75 |
|---|---:|---:|---:|---:|---:|
| Popularidade | 18,38 | 15,89 | 5,00 | 15,00 | 29,00 |
| Ano informado | 2.011,96 | 6,80 | 2.006,00 | 2.012,00 | 2.018,00 |
| Dançabilidade | 0,5374 | 0,1845 | 0,4130 | 0,5500 | 0,6770 |
| Energia | 0,6397 | 0,2705 | 0,4540 | 0,6940 | 0,8730 |
| Intensidade sonora (dB) | -8,98 | 5,68 | -10,83 | -7,45 | -5,28 |
| Presença de fala | 0,0928 | 0,1268 | 0,0371 | 0,0507 | 0,0890 |
| Caráter acústico | 0,3215 | 0,3550 | 0,0064 | 0,1470 | 0,6400 |
| Instrumentalidade | 0,2523 | 0,3651 | 0,0000 | 0,0018 | 0,6140 |
| Indício ao vivo | 0,2230 | 0,2011 | 0,0979 | 0,1340 | 0,2920 |
| Valência | 0,4556 | 0,2685 | 0,2260 | 0,4380 | 0,6740 |
| BPM — incluindo zeros | 121,38 | 29,78 | 98,80 | 121,93 | 139,90 |
| Duração (s) | 249,56 | 149,43 | 181,09 | 225,74 | 286,91 |

Para BPM sob a regra positiva, a média é 121,50 e a mediana 121,96; esse
denominador é 1.158.565, diferente do resumo bruto da tabela.

## 3. Gênero organiza diferenças importantes dos perfis

Os 82 rótulos não têm a mesma frequência. Black-metal reúne 21.852 faixas (1,88%);
songwriter reúne 589 (0,05%). Frequências do arquivo não são participações de
mercado ou uma taxonomia musical universal.

As diferenças entre médias de gênero representam as seguintes frações da
variação total, medidas por eta² descritivo:

| Atributo | Eta² entre gêneros |
|---|---:|
| Caráter acústico | 51,76% |
| Presença de fala | 49,96% |
| Intensidade sonora | 48,39% |
| Energia | 45,99% |
| Dançabilidade | 41,86% |
| Instrumentalidade | 40,10% |
| BPM válido | 8,50% |

Eta² é SS entre médias de categorias / SS total, ponderando cada média pelo
respectivo número de faixas válidas. Não é efeito causal ou teste preditivo.
A tabela confirma diferenças substantivas entre perfis neste catálogo.

Exemplos concretos: energia média de 0,2218 em classical e 0,9331 em death-metal;
instrumentalidade de 0,0025 em sertanejo e 0,7667 em ambient. BPM médio válido
de 99,99 em sleep e 156,54 em drum-and-bass. Os boxplots também mostram
heterogeneidade dentro dos gêneros; o rótulo não determina sozinho o perfil.

Implicação para a próxima amostra: gênero é um candidato fundamentado à
estratificação. Como ele responde por apenas 8,50% da variação de BPM entre
médias, preservar frequências de gênero não garante preservar BPM ou as relações
entre todas as variáveis. Essas propriedades exigem critérios próprios.

## 4. Ano, período e relações entre atributos

Os períodos reúnem 443.801 faixas em 2000–2009 (38,27%), 514.990 em 2010–2019
(44,40%) e 200.973 em 2020–2023 (17,33%). A popularidade média é,
respectivamente, 12,66, 19,99 e 26,89. Essa associação entre ano informado e
escore não descreve a trajetória temporal da mesma música.

Diferenças entre médias dos três períodos respondem por menos de 1% da variação
de cada atributo acústico contínuo/duração, chegando a 0,90% para valência.
São pequenas nessa medida frente às diferenças entre gêneros.
Para popularidade, a fração entre períodos é 10,39%. Isso não exclui diferenças
de caudas ou de combinações dentro dos períodos.

Correlações de Pearson nos mesmos casos completos:
energia–intensidade sonora +0,781; energia–caráter acústico -0,754;
caráter acústico–intensidade sonora -0,623; dançabilidade–valência +0,518.
Spearman mantém as direções principais, respectivamente +0,764, -0,726,
-0,566 e +0,510. Há redundância parcial e relações coerentes entre medidas,
sem equivalência completa. Nenhuma dessas correlações é uma afirmação causal.

## 5. PCA: eixos interpretáveis, com redução parcial

PCA descritiva das dez contínuas acústicas/duração, padronizadas por DP com
divisor n−1; popularidade, ano e gênero não constroem os eixos.

| Componentes acumulados | Variância dos preditores |
|---|---:|
| 1 | 29,12% |
| 2 | 44,35% |
| 3 | 57,85% |
| 6 | 84,39% |
| 8 | 95,66% |

O primeiro eixo combina energia (coeficiente +0,509) e intensidade sonora
(+0,518), em oposição ao caráter acústico (-0,445).
O segundo destaca valência (+0,486) e dançabilidade (+0,444), com coeficientes
negativos de instrumentalidade (-0,368) e duração (-0,335), entre outros.
O terceiro destaca indício de execução ao vivo (+0,673) e presença de fala
(+0,569). São coeficientes dos autovetores, diferentes das correlações com
componentes, fornecidas em coluna própria.

Os sinais são orientações convencionais; os eixos não são categorias naturais
de música, causas ou variância explicada da popularidade. Dois componentes
não oferecem um resumo quase completo: conservam somente 44,35% da variância.
O mapa em duas dimensões não demonstra clusters separados. PCA é útil para
descrever relações e redundâncias, sem justificar automaticamente amostrar
apenas por seus dois primeiros escores.

Fundamentação: [Jolliffe (2002), Principal Component Analysis, 2ª ed.](https://link.springer.com/book/10.1007/b98835).

## 6. O logaritmo da popularidade não produziu forte ganho de simetria

Na escala original, a assimetria por momentos é +0,8100. Em log(1+popularidade),
é -0,7947: a direção se inverteu e a magnitude permaneceu próxima.
As 158.391 faixas com zero (13,66%) continuam com zero após a transformação.
Portanto, a inspeção não sustenta apresentar o logaritmo como solução clara
para a assimetria da distribuição. Não foi testada nem assumida normalidade;
nenhuma resposta de modelo foi transformada.

A popularidade tem mediana 15, P75 de 29 e P95 de 49. A população contém 499
faixas de pelo menos 80 conforme a auditoria anterior, preservada. Caudas e
zeros merecem apresentação explícita, sem definir sucesso musical pela
aparência de uma transformação.

## 7. Como apresentar isso na parte inicial do TCC

Usar uma narrativa curta: fonte/unidade e dicionário; distribuição dos atributos;
composição por gênero/período; relações e uma síntese da PCA. A descrição prepara
a amostragem e a integração, conforme a prioridade do pesquisador.

Para o corpo, selecionar a tabela de metadados e poucas figuras complementares:
distribuições; boxplots por gênero; correlações; popularidade nas duas escalas;
variância/coeficientes da PCA quando necessários à interpretação. O mapa de 82
gêneros inteiro e tabelas extensas podem permanecer como material complementar.
Não é necessário inserir as treze figuras no corpo da monografia.

A matriz de gêneros é alta e o histograma de duração mostra amplitude extrema;
são escolhas explícitas de apresentação, não falhas de cálculo. Usar os quantis
e a figura por gêneros para ler a região típica, sem apagar os extremos.

## 8. Encaminhamento para dimensionar a nova amostra

A descrição oferece números populacionais e variações por gênero para fundamentar
um desenho estratificado e comparar alocações. O ponto de partida recomendado
é avaliar gênero como estrato e critérios simultâneos para os metadados,
mantendo também composição temporal e popularidade no planejamento.
Isso é uma recomendação de desenho a estudar, não tamanho/alocação já adotados.

O dimensionamento deve indicar quais médias/proporções terão qual precisão,
com que nível de confiança e em qual população. Uma alocação ótima para apenas
BPM não é necessariamente ótima para energia/duração; os tamanhos por gênero
não precisam ser iguais. Considerar limites de presença e de precisão de
categorias raras sem afirmar precisão por gênero a partir de precisão global.

O [manual Survey Methods and Practices, capítulo 8](https://www150.statcan.gc.ca/pub/12-587-x/12-587-x2003001-eng.pdf)
trata do dimensionamento, alocação proporcional/Neyman e compromissos entre
variáveis (seção 8.2.3, item iv). Essa é a etapa seguinte, sem novo sorteio agora.

Os metadados populacionais já são conhecidos. Seus critérios de precisão serão
metas de planejamento e controle da nova seleção, não justificativa retrospectiva
para dizer que foi necessário amostrar a fim de conhecer esses mesmos totais.
Eles também não garantem quantidade de letras recuperadas ou precisão do ganho
preditivo. A recuperação terá seus resultados e perdas documentados depois,
preservando a sequência estabelecida.

## Evidência e preservação

Resumos, 44 arquivos gerados, frequências e histogramas conferidos; 36 eta²
reconciliados com perfis por grupo e a variação global. PCA reconstruída pela
matriz de correlação agregada, sem escores individuais ou releitura das faixas.
Treze figuras reais inspecionadas visualmente; sem corte de rótulos ou
sobreposição material observada. A auditoria anterior e a nova descrição têm
as mesmas médias das dez contínuas, respeitando a conversão da duração.
Código, regras e material anterior preservados. Registro detalhado em
verificacao_descritiva_catalogo_20261106.json. Sem novo treinamento preditivo,
consulta LRCLIB, alteração de PDF ou publicação Git.
