# Parecer de fechamento metodológico — 02/11/2026

## Conclusão e destino dos achados

Preservar integralmente resultados, modelos, coorte, folds, PDF e pacote TeX atuais.
Há um **desvio técnico real na tokenização do prefixo E5**, descrito abaixo; não
foi encontrada evidência de perda de cauda textual, pooling incorreto, vetores
corrompidos ou erro nos 21 descritores auditados. O desvio deve constar da
metodologia e ser corrigido em uma futura implementação versionada. Não foi
demonstrado seu impacto no MAE: similaridade alta de vetores artificiais não
garante equivalência preditiva. Não chamar a execução atual de reprodução exata
da receita oficial do E5. Também não há evidência suficiente para concluir que
a ordenação dos quatro modelos se deve ao desvio ou para disparar a regeneração
massiva. Eventual exigência de conformidade estrita antes da versão final requer
decisão explícita sobre nova versão; nunca sobrescrever esta execução.

O ganho Combinado/Baseline permanece favorável na análise auxiliar condicional.
O incremento Combinado/Profundo é pequeno e seu intervalo auxiliar inclui zero.
Não há IC validado da incerteza integral de treinamento/CV nem nova confirmação
independente. A avaliação atual pode ser encerrada como comparação exploratória
do procedimento operacional documentado, com essas qualificações.

| Classe | Achado | Encaminhamento |
| --- | --- | --- |
| Problema real | Prefixo tokenizado separadamente acrescenta token de espaço | Corrigir descrição agora; receita de entrada corrigida em futura versão isolada. Preservar corpus/modelos atuais e não afirmar impacto preditivo inexistente |
| Problema de interpretação a evitar | Tratar cinco folds como cinco réplicas ou um bootstrap de perdas como IC integral | Usar estimandos/hipóteses explícitos e separar intervalos auxiliares da inferência da pipeline |
| Complemento realizado | Resíduos da cauda, clipping e limites por componente/fold | Incorporar como análises exploratórias, sem substituir resultado principal |
| Limitação documentável | Seleção de letras, grupos operacionais, exposição v0.6 e fonte temporal incerta | Restringir alcance; não tentar corrigir retrospectivamente com pesos ou novo split |
| Pendência de escrita | Fontes, fluxo de integração, referências, matching humano e arquivo principal | Integrar evidências existentes; não exige nova recuperação de letras ou treino |

## 1. Incerteza dos contrastes pareados

### O que está sendo quantificado

Nos 77.535 casos e previsões OOF já observados, os contrastes são conhecidos:
Combinado−Baseline = −0,23736258 e Combinado−Profundo = −0,01340169 ponto de MAE.
Não há erro de Monte Carlo desses números. Um intervalo só tem sentido para um
alvo hipotético adicional, sob hipóteses declaradas; não representa incerteza
intrínseca da distribuição empírica finita nem transforma as aceitas em amostra
probabilística de todas as músicas com letras.

[Bengio e Grandvalet (2004)](https://www.jmlr.org/papers/v5/grandvalet04a.html)
mostram por que a variância da CV não tem estimador universalmente não viesado e
por que ignorar suas correlações pode subestimar a incerteza. Não aplicar teste t,
Wilcoxon ou DP/sqrt(5) aos cinco MAEs externos como réplicas independentes.

### Estratégia leve adotada: razão de totais por componente, fold a fold

Hipóteses **auxiliares**, não comprovadas: componentes independentes em uma
superpopulação compatível com o domínio observado, muitos grupos, momentos
finitos, ausência de influência dominante e composição/tamanhos de grupos
compatíveis com a divisão existente. O desenho original sorteou faixas, não
componentes aceitos; essas hipóteses não decorrem dos pesos amostrais. Dentro de
cada componente admite-se dependência arbitrária. Há 4.377 a 4.380 componentes
nos cinco testes externos; o maior representa até 1,20% das faixas de um teste.
Isso não demonstra independência nem estabilidade relativa dos algoritmos.

Para cada fold k, condicionar no seu próprio treino, pré-processamento, seleção
interna e par de modelos. O contraste usa D_g = soma, no componente, das
diferenças pareadas de erros absolutos, e N_g = quantidade de faixas. Calcular
delta_k = soma(D_g)/soma(N_g), com erro padrão por linearização da razão:

`SE_k² = [G_k/(G_k−1)] × soma_g[(D_g−delta_k N_g)²] / soma_g(N_g)²`.

Essa é uma aplicação da inferência por clusters à média de perdas pareadas,
com princípios discutidos por [Cameron e Miller (2015)](https://www.econ.ucdavis.edu/faculty/cameron/research/Cameron_Miller_JHR_2015_February.pdf).
Não é média simples de MAEs por componente: isso daria o mesmo peso a um grupo
com uma faixa e a outro com 186, mudando o estimando. Para sensibilidade ponderada,
D_g incorpora os pesos originais e N_g é a soma desses pesos, sem mudar treino.

Calcular aproximações normais por fold e limites Bonferroni para dez quantidades
(dois contrastes × cinco folds), com família separada para cada ponderação.
Combinar extremos com pesos N_fold/N_total. A desigualdade da união não exige
independência entre folds: se todos os intervalos marginais cobrem seus alvos,
a média ponderada também está entre os extremos ponderados. Sua cobertura nominal
continua **aproximada e condicionada às hipóteses marginais**, e não validada por
simulação para este corpus. Não supor condicionamento conjunto em todos os modelos:
os outros treinos contêm os casos usados como teste deste fold.

| Avaliação | Contraste | Diferença observada | Limites auxiliares, 95% nominais |
| --- | --- | ---: | ---: |
| Pesos iguais | Combinado − Baseline | −0,23736 | [−0,31400; −0,16073] |
| Pesos iguais | Combinado − Profundo | −0,01340 | [−0,03027; +0,00347] |
| Pesos originais, sensibilidade | Combinado − Baseline | −0,22861 | [−0,30454; −0,15268] |
| Pesos originais, sensibilidade | Combinado − Profundo | −0,01234 | [−0,02919; +0,00450] |

O alvo auxiliar combinado é uma média de riscos condicionais dos cinco pares
ajustados, em outras avaliações hipotéticas de componentes compatíveis, mantendo
os ajustes fixos em cada análise marginal. **Não é IC do procedimento completo,
do modelo treinado em todas as faixas ou do catálogo**. A direção favorável frente
ao Baseline é mais convincente nesse cenário; a superioridade sobre o Profundo
permanece inconclusiva mesmo nele. Não reportar p-valores ou significância geral.
Bonferroni não desfaz escolhas históricas de hipóteses/modelos depois de resultados.

### Bootstrap e incerteza integral: alternativas investigadas

Bootstrap pareado de componentes dentro de cada fold é alternativa à linearização:
sortear grupos inteiros, usar a mesma multiplicidade para ambos os modelos e
recalcular razão de totais. Não sortear faixas isoladas nem separar versões.
Reamostrar diretamente as perdas OOF conjuntas só avalia composição com previsões
fixas; não recupera a dependência produzida pelos treinos sobrepostos. A faixa de
remoção de um componente da etapa 23 continua sendo diagnóstico de influência,
não IC, bootstrap ou leave-one-group-out com reajuste. Nenhum bootstrap extenso
foi executado nesta rodada.

Há métodos assintóticos de CV sob estabilidade dos algoritmos, como
[Bayle et al. (2020)](https://papers.neurips.cc/paper_files/paper/2020/hash/bce9abf229ffd7e570818476ee5d7dde-Abstract.html).
O resultado posterior de [Bayle, Janson e Mackey (2026)](https://proceedings.mlr.press/v306/bayle26a.html)
adverte que estabilidade individual não basta para uma comparação: a diferença
de perdas pode ser relativamente instável. O exemplo negativo do artigo não
prova que nosso Ridge falha, mas impede presumir validade só por ser Ridge ou
por haver muitos grupos. Grupos de tamanho desigual, seleção de alpha e
pré-processamento exigiriam adaptação/justificação próprias.

[Bates, Hastie e Tibshirani (2024)](https://arxiv.org/abs/2104.00673) distinguem
alvos de erro e estudam um desenho aninhado para estimar a variabilidade da CV.
Esse desenho de estimação de incerteza não se obtém automaticamente da nossa
CV aninhada 5×3 para escolher alpha; os ajustes internos salvos não são réplicas
independentes do contraste externo.

Se fosse indispensável uma conclusão sobre o algoritmo em novas amostras, seria
necessário justificar um desenho adicional que refaça seleção, escalas e modelos
em cada réplica, pareando os quatro blocos e mantendo cópias de um componente
sempre na mesma partição. Repetir seeds apenas estima sensibilidade à partição
do mesmo corpus. Nem refit-bootstrap corrigiria automaticamente disponibilidade
de letras, erros de matching ou seleção da fonte. Um teste realmente novo com
grupos elegíveis definidos antes da análise seria outra possibilidade futura,
sem chamar o teste já exposto de independente. **Não é necessário iniciar esses
trabalhos para encerrar a comparação exploratória atual; nenhum treino pesado
ou novo comando de treinamento foi preparado como próxima tarefa.**

## 2. Auditoria técnica das representações

### E5: o que foi confirmado e o problema encontrado

Revisão congelada: `intfloat/multilingual-e5-small` em
`614241f622f53c4eeff9890bdc4f31cfecc418b3`. Código/protocolo e snapshot coincidem
com o selo da execução. Foram conferidos hashes de configuração/tokenizer e,
no diagnóstico sintético motivado pelo achado, de todos os arquivos, inclusive
pesos. Nenhum arquivo de modelo foi baixado. A fonte única continua sendo o texto
normalizado aceito; nomes, popularidade, gêneros, idioma e pesos não entram no E5.

| Aspecto | Implementação observada | Parecer |
| --- | --- | --- |
| Prefixo | `query: ` em todas as janelas/idiomas, tokenizado à parte do conteúdo | Família de prefixo adequada para features, mas há token de espaço extra frente à concatenação oficial |
| Tokenizer | Fast local, mesmo snapshot, sem tradução/filtragem de idiomas | Compatível; igualdade entre idioma estimado e capacidade real do modelo não é pressuposta |
| Comprimento | Conteúdo completo; reserva de quatro tokens do prefixo e dois especiais; 506 de conteúdo por janela; overlap 32 | Nenhum input efetivo acima de 512; não houve truncamento silencioso |
| Pooling | Média de hidden states com máscara de atenção, incluindo prefixo/especiais válidos | Padding excluído; teste com hidden states artificiais confirmou o cálculo |
| Normalização | L2 por janela; média ponderada por tokens novos e L2 final | Integridade adequada; agregação de janelas é adaptação do estudo, sem validação universal para letras |
| Execução | CPU float32, eval/inference_mode, determinismo, safetensors locais | Não há ajuste do encoder ao alvo ou vocabulário aprendido na coorte |

O [model card oficial](https://huggingface.co/intfloat/multilingual-e5-small)
recomenda `query: ` para embeddings usados como features, inclusive em outros
idiomas; seu exemplo concatena prefixo e texto antes de tokenizar e usa média
mascarada/L2. Declara 384 dimensões, contexto de 512 tokens e limitações de cobertura
linguística. Essas instruções não validam desempenho sobre letras.

**Desvio reproduzível:** o prefixo isolado produz IDs `[41, 1294, 12, 6]`; o último
é o marcador de espaço `▁`. Para `Uma manhã tranquila.`, o conteúdo também começa
por um token com espaço inicial. A sequência construída corresponde a
`query:  Uma manhã tranquila.`, enquanto a concatenação oficial produz um espaço.
O token adicional é válido, recebe máscara 1, participa da atenção/média e ocupa
uma posição. Não é simples diferença de impressão. A diferença apareceu em 11/11
frases artificiais e 8/8 textos inspecionados; a pequena amostra não é estimativa
probabilística de prevalência no corpus. A construção por janelas ainda pode
começar em subpalavras: uma correção futura precisa testar fronteiras, não apenas
apagar um token de todos os inputs já salvos.

Para medir exclusivamente se os vetores mudam, quatro frases artificiais curtas
(inglês, português, árabe e chinês) foram codificadas com as duas receitas, sem
cache/exportação de vetores: oito forwards unitários, entradas de no máximo 64
tokens. Cossenos entre 0,996643 e 0,999434; distâncias L2 entre 0,03365 e 0,08194.
Vetores próximos **não são idênticos**; o experimento não mede impacto em MAE,
não valida todos os idiomas/comprimentos e não autoriza transportar uma garantia
numérica para as 77.051 letras. Nenhum embedding do corpus foi gerado nesta rodada.

Encaminhamento: reconhecer a variante operacional atual e a divergência da receita
oficial. A entrada concatenada usada no script 27 é referência canônica para o
caso curto; antes de qualquer futura versão completa, testar também janelas,
fronteiras de subpalavras, prefixos e cobertura. Corrigir o código 20 no lugar
invalidaria selos/retomada e a rastreabilidade dos modelos existentes. Não fazê-lo.
Caso se opte por refazer representações, isso será outra versão, execução manual,
sem substituir retroativamente o estudo atual. Não estimar efeito preditivo
plugando vetores corrigidos em Ridge treinado em outra representação.

O aviso sobre mais de 512 tokens refere-se à tokenização integral anterior à
divisão, não aos inputs enviados ao modelo. O aviso sobre tokenizer fast indica
eficiência potencial, não evidência de erro numérico. Overlap influencia contextos
duas vezes: ponderar tokens novos reduz seu peso, mas não desfaz essa influência.

### Descritores: critérios e proveniência

São 21 descritores próprios do estudo, definidos em Python/contrato antes do
resultado atual; **não são os 196 descritores LFM2b nem medidas validadas de
sentimento, legibilidade ou rima**. Fonte: `accepted_text` v2, NFC/BOM/quebras de
linha/espaços finais conforme função selada, sem apagar repetições ou marcadores.
Hashes normalizados ligam o mesmo conteúdo ao encoder; 77.535 faixas representam
77.051 inputs únicos. Todas as observações originais foram mantidas.

Na tabela, C=caracteres não brancos, L=letras Unicode, T=segmentos após casefold,
U=tipos de segmento, B=linhas não vazias. Denominador zero recebe zero; a flag
de ausência de segmentos acompanha a extração. DP populacional usa divisor n.

| Coluna | Definição operacional |
| --- | --- |
| text_characters | Pontos de código do texto normalizado, incluindo espaços/quebras internos |
| text_nonspace_characters | Quantidade C |
| text_nonempty_lines | Quantidade B |
| text_stanzas | Blocos não vazios separados por uma ou mais linhas vazias |
| text_lexical_segments | Quantidade T, sequências Unicode de letras com apóstrofo/hífen interno |
| text_unique_segments | Quantidade U após casefold |
| text_segment_length_mean | Média dos comprimentos dos segmentos após casefold |
| text_segment_length_std | DP populacional desses comprimentos |
| text_segment_type_ratio | U/T |
| text_hapax_type_ratio | Tipos que ocorrem uma vez / U |
| text_segment_entropy | −soma p_t log2(p_t), em bits |
| text_line_length_mean | Média de caracteres não brancos por linha não vazia |
| text_line_length_std | DP populacional desses comprimentos |
| text_repeated_line_fraction | (B − número de linhas distintas)/B, após casefold e uniformização de espaços |
| text_letters_fraction | L/C, categoria Unicode L |
| text_digits_fraction | Dígitos decimais Unicode / C |
| text_punctuation_fraction | Categoria Unicode P / C |
| text_uppercase_letter_fraction | Letras maiúsculas / L |
| text_question_line_fraction | Linhas com ? ou ？ / B |
| text_exclamation_line_fraction | Linhas com ! ou ！ / B |
| text_no_lexical_segments | Indicador T=0; constante zero na coorte atual |

Selos de código/contrato/normalização coincidem com a execução 19. Foram
recalculados todos os 21 valores em oito textos originais e comparados a todas
as suas referências armazenadas: diferença máxima 0,0. Projeção lida de 10.154.023
bytes comprimidos; sem varrer todas as letras. O hash integral do arquivo de
descritores é evidência anterior da etapa 21; não foi recalculado aqui. A etapa
19 verificou finitude de todos os descritores e a 21 auditou todos os 77.051
vetores, dimensão/hash/L2, com erro máximo de norma 5,96×10⁻⁸. Distinguir essa
evidência integral anterior da conferência amostral atual.

Não foi identificado erro de implementação desses critérios. Suas limitações
precisam constar: segmentos não são palavras universais; escritas sem espaços,
marcas combinantes que não pertencem à categoria L e expansões de casefold
afetam comparabilidade. Marcadores de seção e outras anotações preservadas
também contam. Essas são características operacionais, não descobertas de
semântica universal. A flag constante não acrescenta informação; StandardScaler
ajustado em cada treino a transforma em zero, sem excluir casos ou provocar
vazamento. Não mudar definições retrospectivamente por desempenho.

## 3. Cauda superior: o que significa MAE 29,37

Os 128 casos pertencem a 96 componentes; o maior contém sete casos da cauda e
os cinco maiores somam 24. As popularidades observadas vão de 80 a 96: 116 estão
em 80–84, oito em 85–89 e quatro em 90–100. A banda não equivale a 128 hits
extremos próximos de 100. Não divulgar métricas separadas para esses subgrupos
pequenos; as contagens apenas caracterizam suporte. Contagens por fold também
estão disponíveis, sem tratar folds como novas amostras independentes.

| Modelo | Previsão média | MAE da cauda | RMSE da cauda | Subestimadas |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 50,8831 | 30,9294 | 32,7434 | 128/128 |
| Tradicional | 51,3634 | 30,4491 | 32,2431 | 128/128 |
| Profundo | 52,1361 | 29,6764 | 31,6598 | 128/128 |
| Combinado | 52,4414 | 29,3711 | 31,3288 | 128/128 |

Popularidade observada média 81,8125. No Combinado, as previsões da cauda vão de
24,9681 a 77,9977: **todas as 128 são subestimadas**. Resíduo definido como
previsão−observado tem média −29,3711 e DP populacional 10,9011; mínimo −58,0319,
P10 −42,3052, P25 −37,2444, mediana −28,7755, P75 −22,4381, P90 −15,7352 e
máximo −2,0023. São 101 subestimações de pelo menos 20 pontos e 22 de pelo menos
40. Não se trata apenas de poucos erros extremos isolados. No conjunto inteiro,
o Combinado não emitiu previsão ≥80; seu máximo também é 77,9977.

Esses números demonstram dificuldade do procedimento em reproduzir a cauda
observada. São compatíveis com compressão/regressão ao centro de uma regressão
regularizada e com pouco suporte/ informação para separar valores altos, mas o
diagnóstico não identifica causalmente essas explicações. Ridge minimiza perda
quadrática penalizada no ajuste, embora alpha/modelos sejam avaliados por MAE.
Condicionar no próprio alvo y≥80 pode produzir resíduos sistematicamente negativos
mesmo sem erro de código; não confundir esse diagnóstico com calibração definida
condicionalmente à previsão, E[Y|previsão]. Não mudar objetivo ou ponderação para
favorecer hits retrospectivamente.

### Contribuição ao erro agregado

- 128/77.535 = **0,1651% das faixas**.
- Soma de erros absolutos do Combinado na cauda: **3.759,4960** pontos.
- Participação no erro absoluto total: **0,5975%**; no erro quadrático: **1,4591%**.
- Contribuição aditiva ao MAE global: **0,04849 ponto**, com denominador global
  mantido. O MAE dos demais casos, apenas como descrição, é 8,07997; não excluir
  os 128 do resultado principal.
- A melhora Baseline→Combinado na cauda contribui **0,002573 ponto** ao ganho
  global de 0,237363: **1,0838% do ganho total**. A melhora global não foi produzida
  principalmente por esses casos.

Portanto, MAE global bom em relação às referências simples convive com desempenho
fraco em faixas muito populares. Um objetivo específico de prever hits exigiria
outro estimando/desenho; não é uma alegação sustentada por esta comparação média.

### Previsões negativas e clipping separado

| Modelo | <0 | >100 | MAE original | MAE com clip[0,100] |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 537 | 0 | 8,352484 | 8,337807 |
| Tradicional | 584 | 1 | 8,295691 | 8,280130 |
| Profundo | 610 | 0 | 8,128523 | 8,110555 |
| Combinado | 615 | 0 | 8,115122 | 8,097009 |

No Combinado, 615 previsões negativas (0,7932%) pertencem a 317 componentes;
mínimo −32,7066 e mediana −1,7873. Popularidade observada nesses casos: média
5,3122, mediana 3, máximo 44; 133 são zero e apenas um caso tem y≥40. Isso é
principalmente extrapolação na borda inferior, não a mesma dificuldade da cauda
superior. Ridge não impõe restrição de suporte à resposta; valores negativos
não são evidência, por si só, de vetores inválidos.

Com y∈[0,100], projetar a previsão nesse intervalo não pode aumentar erro
absoluto/quadrático ponto a ponto. Na sensibilidade, a ordenação dos quatro
blocos é mantida. O Combinado melhora 0,018113 ponto de MAE global; com pesos
originais, de 7,990828 a 7,972609. Essa melhora determinística de suporte não é
nova informação textual. Nos 128 casos da cauda, clipping **não altera nenhuma
previsão ou métrica**, pois já estavam no intervalo. Preservar como análise
pós-resultado separada; não substituir as métricas da comparação principal.

## 4. O que falta para a monografia completa

PDF e ZIP atuais preservados por SHA-256. Não foram regenerados nem editados
para acrescentar esses achados. Este parecer é adendo para revisão posterior.
No repositório só foram localizados dois projetos TeX parciais, sem arquivo
principal completo; o caminho permanece solicitado, sem concluir que não exista
fora do projeto.

| Frente | Evidência existente | Integração ou ressalva necessária |
| --- | --- | --- |
| Pergunta e estimando | D-014/D-015/D-017; metodologia atual | Formular contribuição incremental média sob Ridge, pesos iguais e domínio observado; separar descrição da amostra de inferência preditiva |
| Fonte Spotify | Kaggle configurado, CSV/hash, auditoria 11 | Descrever catálogo acessível de 1.159.764 IDs, mecanismo de origem conhecido e suas lacunas; não chamar de todo o Spotify |
| Tempo da resposta | Registro de reuso/verificação em 18/08/2026; atualização upstream documentada em 2023 | Data de coleta de popularity e versão Kaggle não confirmadas. Não atribuir popularity a 2026 nem year a ano original de lançamento sem evidência |
| Fonte textual | Dump LRCLIB 12/10/2026 e checkpoints locais | Descrever banco colaborativo/snapshot, plain/synced, instrumentais e registros ausentes/ambíguos; referência e licença/condições conforme evidência específica, sem confundir acesso aberto com direito sobre letras |
| Integração Spotify–LRCLIB | Normalização preservadora, recuperação v2 e rejeições | Fluxograma com chaves operacionais, variantes, equivalência, versões/duração/conflitos e critérios de aceite/rejeição; distinguir registro/gravação/composição/texto |
| Amostragem e seleção | Sorteio estratificado de 200 mil; pesos e parecer v2 | Mostrar 77.535 aceitas, 86.610 não encontradas, 27.085 ambíguas, 8.759 instrumentais, nove sem texto e duas insuficientes; zero pendência/erro. Não somar 31 sugestões v3 não aplicadas |
| Qualidade de matching | Auditorias de integridade concluídas | Separar integridade criptográfica de correção semântica; revisão humana dirigida pendente. Sem amostra/rotulação apropriada, não inventar taxa de precisão do corpus |
| Representações | Contrato 19, encoder 20, auditorias 26/27 | Incluir as 21 definições, input comum, janelas/agregação e **token de espaço extra encontrado**, com a distinção entre receita oficial e variante efetiva |
| Validação e exposição | 21.893 componentes, folds comuns 5×3, teste v0.6 exposto em 14/10/2026 | Especificar arestas de grupos, limites das identidades, pré-processamento no treino e tuning; não dizer teste intocado ou prevenção universal de leakage |
| Métodos estatísticos | Métricas OOF, pesos iguais, sensibilidade original | Separar efeito observado, limites condicionais e incerteza integral não estimada; incluir caráter pós-resultado de clipping/subgrupos e limites de seleção histórica |
| Resultados/discussão | Trecho 24 e este adendo | Integrar cauda, negativos, pequeno ganho sobre Profundo e heterogeneidade linguística; sem significância/causalidade/generalização automática |
| História LFM2b | Pacote antigo separado, descritores/experimentos anteriores | Contextualizar trajetória sem impor interseção como elegibilidade atual ou misturar métricas/targets; spotify_popularity ≠ genius_lyrics_views ≠ lfm_playcount |
| Referências e forma | Links primários abaixo, TeX parcial existente | Completar introdução/revisão de literatura, referências bibliográficas consistentes, template institucional, figuras/tabelas numeradas e apêndice de proveniência/reprodução |

O índice popularity é descrito como escore de 0–100 baseado em execuções e
recência, com versões duplicadas avaliadas separadamente, na
[documentação Spotify](https://developer.spotify.com/documentation/web-api/reference/get-track).
Essa definição não fornece a data da medição no CSV e não é resposta causal nem
popularidade no lançamento. As datas não confirmadas devem permanecer assim.

### Redação proposta para incorporar na revisão

> Na distribuição empírica das faixas com letras aceitas, o Combinado apresentou
> redução média de 0,2374 ponto de MAE frente ao Baseline e de 0,0134 ponto frente
> ao Profundo. Uma análise exploratória da variação de avaliação, sob hipóteses
> auxiliares de independência entre componentes operacionais e condicionamento
> nos ajustes de cada fold, manteve direção favorável frente ao Baseline, mas
> foi inconclusiva para o pequeno incremento sobre o Profundo. Esses limites não
> estimam a variabilidade integral da seleção e do treinamento e não autorizam
> extrapolação ao catálogo. A representação E5 empregada é uma variante operacional
> com agregação de janelas e um token adicional de espaço no prefixo, identificado
> na auditoria posterior; seu impacto preditivo específico não foi quantificado.
> Todas as faixas com popularidade observada ≥80 foram subestimadas, evidenciando
> que melhoria média não implica capacidade adequada de estimar a cauda superior.

## 5. Verificação e reprodução

Novos diagnósticos em `reports/fechamento_metodologico_200k_v1/`, somente agregados:
resíduos/histograma, métricas originais/clipping, negativos, contagens de cauda,
limites condicionais por fold/combinados, auditoria de representações e teste
sintético do prefixo. `resumo_fechamento.json` liga previsões/perdas aos hashes
validados em 23. Código/protocolos 19–23 preservados; nenhum modelo preditivo
carregado ou treinado, nenhuma busca LRCLIB, nenhum vetor do corpus recalculado.

- Script 25: diagnóstico concluído em 0,264 s, sem encoder/letras/refit/bootstrap.
- Script 26: auditoria concluída em 20,461 s; oito textos/168 valores reproduzidos,
  tokenizer local em 11 frases artificiais, sem forward E5. O primeiro teste
  bloqueou a leitura do arquivo inteiro de descritores por orçamento; a versão
  final leu só a projeção de 9,68 MiB e registrou que não refez hash integral.
  A verificação de equivalência de prefixos detectou a diferença real, que foi
  investigada e preservada no relatório em vez de ocultada.
- Script 27: diagnóstico limitado motivado pelo desvio, 20,702 s incluindo
  carregamento; quatro frases artificiais/oito forwards curtos, sem corpus/cache.
- `resumir_cauda_auxiliar.py`: CLI que reproduz as contagens adicionais; verifica
  igualdade sem sobrescrever o complemento existente.
- 17 testes passaram: quatro novos de fechamento, oito do encoder, quatro de
  descritores e um de pooling com estados artificiais. Sem treinos reais nesses
  testes. Ruff check/format e `git diff --check` verificados ao concluir.

Os scripts de auditoria recusam substituir saídas existentes. O script 25 permite
um novo `--output` para reprodução deliberada; não executar novamente 19–24.
Não há tarefa pesada necessária neste parecer. Não oferecer uma nova rodada
massiva de experimentos como condição para escrever a discussão.
