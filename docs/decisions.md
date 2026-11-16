# Decisões técnicas e científicas

Este é o registro canônico equivalente a `DECISOES_METODOLOGICAS.md` solicitado
na consolidação. Não criar outro histórico paralelo. Contexto em
`CONTEXTO_TCC.md`, estado em `ESTADO_ATUAL.md`.

## D-049 — Publicação e nome do repositório (16/11/2026)

O pesquisador confirmou que o ZIP da D-048 compilou no Overleaf e autorizou
a publicação da edição e a renomeação do remoto para o título da monografia.
O nome no endereço usa letras minúsculas, sem acentos e com hífens. O README
usa o título integral e reúne monografia, protocolo, métricas e reprodução.

A seleção inclui código e testes, documentação, agregados que sustentam o
estudo, PDF, ZIP e fontes LaTeX da D-048. Cópias editoriais intermediárias
inéditas e o pacote local de preservação ficam fora do commit. Os arquivos
já publicados e as sementes científicas históricas são preservados.
O repositório segue privado, no ramo master.

## D-048 — Edição otimizada para Overleaf e semente 42 (16/11/2026)

O pesquisador solicitou reduzir o custo de compilação, retirar créditos
repetidos e reduzir espaços entre figuras. O pacote passou de cerca de
3,05 MB para 1,25 MB, com os mesmos arquivos e figuras otimizadas. As figuras
6 e 7 estão lado a lado. Compilação limpa do ZIP com Tectonic/XeTeX e
BibTeX em cerca de 5,4 segundos, ante 15,1 segundos da D-047 no mesmo
ambiente. O tempo no servidor Overleaf ainda não foi medido.

Semente 42 passa a ser o padrão de novas execuções estocásticas. O script
58 recalculou os percentis do bootstrap de 8.000 réplicas com 42, mantendo
os contrastes pontuais e a leitura dos limites. As seleções de D-031 e
D-043, com sementes de execução 20261106 e 20261108, e a avaliação selada
de 57 foram preservadas. A opção `--semente 20261113` em 58 permite
reproduzir os limites das edições anteriores em uma pasta separada.
Não houve publicação no GitHub nesta etapa.

## D-047 — Revisão da estrutura da monografia (13/11/2026)

A pedido do pesquisador, as análises descritivas, a PCA, o dimensionamento,
a vinculação e as definições das representações passam ao corpo do texto.
Resumo em português em página própria e palavras-chave conforme o template
e o exemplo de Ana. A etapa histórica entra na narrativa apenas como parte
da proveniência e da exposição prévia, com a edição anterior preservada.

59 conferiu os selos e os IDs do sorteio, da coorte e da vinculação original.
A coorte classificada de 9.526 faixas contém 461 IDs do sorteio inicial e
9.065 de fora dele. Os formatos são 3.726 letras só simples e 5.800 com
ambas as formas nos registros de origem, por faixa Spotify. O resultado
refere-se à coorte e não aos 33.714.178 registros do dump. As métricas
de 57 e a interpretação condicionada de 58 foram mantidas.

O ZIP foi compilado de uma extração limpa e o PDF revisado visualmente.
Artefatos e hashes em reports/verificacao_monografia_template_revisada.json.

## D-046 — Monografia final para revisão (13/11/2026)

O pesquisador autorizou a consolidação editorial e o uso das previsões
existentes. A monografia incorpora o dicionário e a exploração do catálogo,
o dimensionamento probabilístico e a cobertura seletiva. A análise principal
é a classificação ordinal nas 9.526 faixas sorteadas dentro do quadro de
80.943 vínculos aceitos. Os pesos de um quadro não substituem os do outro.
As avaliações de 77.535 faixas são mantidas em apêndice como histórico.

58 validou o hash das probabilidades externas e reproduziu a acurácia
balanceada. Calculou 8.000 réplicas de bootstrap pareado por componente,
com previsões fixas, semente 20261113 e limites percentílicos marginais.
Todos os contrastes de acurácia balanceada apresentados incluem zero.
O resultado para sensibilidade alta descreve uma redistribuição de erros.
Os limites não representam a variabilidade dos treinos e da seleção.

A entrega usa o template institucional e mantém os objetivos na introdução.
O ZIP e o PDF são versões distintas da V3 preservada. A compilação foi
testada a partir do ZIP extraído e o PDF passou por revisão visual. Nenhuma
nova busca, geração de embeddings ou treinamento foi executada.

## D-045 — Classificação concluída e verificada

57 concluiu a avaliação agrupada das 9.526 faixas. A acurácia balanceada
foi de 56,14% no Baseline, 56,24% no Tradicional, 55,91% no Profundo e 55,96%
no Combinado. Na classe alta, as sensibilidades do Baseline e do Profundo
foram 26,25% e 31,07%. São diferenças de desempenho observadas no procedimento
avaliado. A interpretação por classe e a sensibilidade ao peso de desenho
constam em reports/classificacao_9526_v1/interpretacao_resultados.md.

## D-044 — Classificação na amostra de 9.526 faixas com letra

O pesquisador autorizou a modelagem da candidata v2 com quatro conjuntos
de preditores. A resposta tem níveis baixo (0–19), médio (20–39) e alto
(40–100). 57 usa logística ordinal com penalização L2 e divisão agrupada
5×3 construída na amostra atual. A grade de penalização tem quatro valores
e o pré-processamento principal usa as covariáveis diretamente. A acurácia
balanceada das previsões externas é a métrica principal. Os pesos da
candidata entram na análise de sensibilidade. O alcance é o conjunto de
faixas com letra verificada.

O protocolo em docs/protocolo_classificacao_9526_v1.md registra a composição
da amostra, a sobreposição com a coorte histórica e seus quatro blocos.
O diagnóstico real de preparação verificou 6.271 componentes, com 9.018
vetores reutilizáveis para 9.500 textos distintos. Treino manual pendente.

## D-043 — Conferência de 55 e candidata v2 (13/11/2026)

55 terminou com 179 vínculos entre 22.443 consultas. Selos, equivalência
entre checkpoint e Parquet e correspondência com gravações e textos
originais foram verificados. Para 166 faixas, a diferença de duração foi
de até dois segundos. As outras 13 ficaram dentro da margem de dez segundos.
O quadro ampliado tem 80.943 IDs distintos.

56 revisou a alocação por restrições de capacidade. Mantém os totais das
cinco bandas de popularidade, prioriza a redistribuição proporcional das
vagas e minimiza desvios nas células observadas. A seleção é aleatória
sem reposição dentro das células. Todos os 9.526 textos foram rechecados
por hash. `sleep` tem 23 dos 147 previstos e `indie-pop` tem 81 dos 82.
9.033 faixas pertenciam à coorte histórica de modelagem. Os pesos da nova
candidata referem-se ao quadro observado de vínculos aceitos.

Em `sleep`, 55 encontrou 18 letras em 13.983 consultas. Uma inspeção de
48 das 680 faixas fora dos índices, por chave nativa de artista, título
e duração, encontrou 17 registros compatíveis marcados como instrumentais
e zero campos de letra compatíveis. O diagnóstico tem escopo de verificação
local por chave exata. O uso analítico da candidata depende da definição do
domínio e do tratamento da exposição histórica com o pesquisador.

## D-042 — Revalidação de caches e recuperação dirigida (13/11/2026)

53 revalidou 42 de 43 consultas históricas. Aplicou o hash da fonte, a
identidade da consulta e as regras atuais de compatibilidade e concordância
textual. Um vínculo de `guitar` ficou incompatível. O quadro potencial
passou de 80.722 para 80.764 faixas. `minimal-techno` alcançou capacidade
de 151 para a cota de 125. As cotas ainda deficitárias somam 205 vínculos.

54 triou `sleep`, `romance` e `detroit-techno` no catálogo selado. A lista
contém 22.443 consultas distintas de faixas fora dos sorteios de 200 mil e
9.526, com artistas nos índices existentes. 55 usa a regra textual de 50 e
registra os desfechos e a capacidade resultante. A execução real é manual.
A decisão sobre o quadro final considera esse resultado, a exposição anterior
e o domínio da avaliação.

## D-041 — Candidata de 9.526 faixas com vínculo textual (07/11/2026)

O pesquisador fixou o requisito de 9.526 faixas com letra vinculada e pediu
explorar outras faixas e fontes. 52 combinou 77.535 faixas da coorte histórica
e 3.869 aceitas do sorteio menor. As 682 duplicatas conferiram em metadados e
hash, resultando em 80.722 IDs elegíveis. Houve sorteio estratificado de uma
candidata de 9.526, com textos não vazios e hashes conferidos. O desenho é
condicional a esse quadro observado e preserva os totais das bandas de
popularidade do sorteio inicial. Quatro cotas de gênero excedem a capacidade
disponível. A avaliação definitiva, o alcance de inferência e o tratamento da
exposição anterior precisam ser acordados antes de modelar. A comparação e
as fontes potenciais estão em docs/amostra_com_letras_candidata_v1.md.

## D-040 — Recuperação local conferida e cobertura consolidada (07/11/2026)

50 real concluído pelo pesquisador, com 25 aceitações em 40 consultas por
limite. Checkpoint, chaves, selos e hashes verificados. As 25 letras foram
conferidas por ID no dump com leitura pontual. O complemento altera apenas
as 25 faixas aceitas. Os 15 demais casos mantêm o status-base, com desfechos
da revisão registrados à parte, incluindo duas indicações instrumentais.

51 reconciliou os complementos disjuntos de 46, 47, 48 e 50 ao resultado 43,
preservando os campos originais, pesos e faixas do sorteio. Total de 3.869
aceitas (40,62%; 40,63% com os pesos do sorteio). Cobertura de 29,99% em
popularidade 0–19 e 60,75% em 40–59. Os dois gêneros sem letras aceitas foram
detroit-techno e sleep. O domínio observado apresenta seleção por metadados e
popularidade. O próximo passo é decidir o domínio da avaliação com o
pesquisador, mantendo os resultados acadêmicos anteriores separados.

## D-039 — Resultado do piloto online e revisão dos limites locais (07/11/2026)

49 real concluído pelo pesquisador. As 100 respostas foram HTTP 200. Houve
93 vazias, cinco sem candidato compatível, uma indicação instrumental e uma
resposta no teto. Zero candidatas e 3.844 letras aceitas no conjunto local.
O limite superior unilateral exato de 95% para o rendimento do mesmo
protocolo é 121/4.155 (2,91%), pela hipergeométrica de uma AAS sem reposição,
sob a hipótese de resposta fixa no período. O evento avaliado é produzir
candidata segundo as regras do piloto. A rodada online fica encerrada com
esse protocolo. A indicação instrumental continua registrada como desfecho
do piloto, com o status local de origem preservado.

Entre as 1.110 ambiguidades, 40 foram barradas pelo teto de 500 resultados
da chave antes da elegibilidade. Em sete consultas inspecionadas, seis
tinham 1 a 457 compatíveis e uma tinha zero. A etapa 50 antecipa a filtragem
pelos mesmos critérios de metadados. O teto de leitura de 2.500 metadados
e o de 500 elegíveis exigem conjunto completo antes de aceitar texto.
A execução real continua manual com SSD D: e saída incremental separada.

## D-038 — Piloto online nas pendências sem candidato (07/11/2026)

O pesquisador autorizou testar a API atual do LRCLIB antes de expandir a
recuperação. Seleção aleatória simples sem reposição de 100 das 4.155 faixas
sem candidato após 48, semente 20261107. O tamanho é operacional para o
piloto e a taxa se refere a essas pendências. O manifesto foi selado antes
das consultas, com 100 consultas distintas.

Somente a busca GET `/api/search`, com artista e título. O controle local
exige identidade, participações, versão e diferença de duração de até dois
segundos, além de consistência textual sob as regras de 46–47. Retornos no
teto de 20 ficam inconclusivos. A API pode trazer tanto novos registros
quanto registros alcançados por outro mecanismo de busca. Atribuir a origem
do ganho exige comparação posterior com o dump.

Resultados positivos são candidatos provisórios até a conferência. Falhas
operacionais são pendências separadas. Execução real manual, em série e
retomável. Nove testes e um fluxo com respostas simuladas passaram.

## D-037 — Revisão plain/LRC conferida e variantes documentadas (07/11/2026)

47 real concluído pelo pesquisador em 3,64 s. Das 108 consultas, 58 foram
aceitas, 29 mantiveram divergência plain/LRC e 21 mantiveram diferenças entre
candidatos. Conferência de hashes, originais e vínculos confirmou 3.835 aceitas.

48 revisou individualmente 13 variantes de grafia por fichas do Spotify e
catálogos de lançamento. Foram aceitos nove casos com concordância de título,
versão, crédito essencial e edição, duração a até um segundo e textos elegíveis
consistentes. A aprovação vale apenas para os pares documentados. Dois casos
ficaram pendentes por edição insuficientemente identificada e dois por
participações ausentes no cadastro do LRCLIB. A revisão verifica evidência
documental de vínculo, sem comparação de áudio ou anotação humana da letra.

Os complementos disjuntos somam 3.844 aceitas (40,35%; 40,37% com os pesos do
sorteio), 1.110 ambíguas, 4.155 sem candidato pelos métodos usados, 416
instrumentais e uma sem texto. A cobertura foi 29,76% na popularidade 0–19 e
60,53% em 40–59. Próximo passo em avaliação é testar uma fonte atual em um
piloto pequeno das pendências, com validação antes de eventual expansão.

## D-036 — Caixa entre representações simples e sincronizada (07/11/2026)

46 real concluído pelo pesquisador em 39,60 s, com 130 novas aceitações nas
831 consultas e 701 ainda diferentes. Arquivos, hashes de texto, decisões e
chaves conferidos. Total de 3.777/9.526 (39,65% sem peso e 39,66% com os pesos
originais). Restam 1.168 ambiguidades, 4.164 sem candidato pelos métodos usados,
416 indicações instrumentais e uma faixa sem texto. As duas faixas de
popularidade 0–19 e 40–59 têm coberturas de 29,33% e 59,57%, respectivamente.
Os pesos do sorteio descrevem a cobertura e as perdas continuam seletivas.

Em 12 das 108 pendências plain/LRC inspecionadas em ordem determinística, cinco
ficaram inteiramente equivalentes com a normalização de 46 aplicada também ao
par simples/sincronizado do mesmo candidato. Outras quatro mantiveram conflito
plain/LRC e três mantiveram diferenças entre candidatos. A inspeção é dirigida.
Com essa evidência, 47 reaplica caixa, espaços e tipografia apenas a esse tipo
de conflito. Todos os candidatos elegíveis passam pelas mesmas regras de
metadados e pelo analisador LRC vigente. O original aceito é preservado, com
vínculos em complemento. Execução real manual pendente, SSD D:.

## D-035 — Continuidade da recuperação e comparação de caixa (07/11/2026)

O pesquisador escolheu continuar a recuperação antes de modelar. 44 concluiu
4.164 diagnósticos em 137,64 s. Houve 13 consultas com variação de artista,
16 pares para revisão e 332 consultas com truncamento por limite de registros.
Conferência pontual dos 13 casos encontrou pelo menos um registro com campo
textual preenchido por consulta. Fichas privadas guardadas para validar o vínculo.

45 concluiu a consolidação leve das 9.526 linhas de metadados. As 3.647 aceitas
têm popularidade média 24,156, energia 0,686 e instrumentalidade 0,108. As
médias do catálogo são 18,383, 0,640 e 0,252. A descrição condicional ponderada
também está disponível. A seleção permanece uma limitação do domínio com letras.

Inspeção de doze ambiguidades por textos concorrentes identificou cinco com
igualdade após uniformização de caixa, espaços e tipografia vigente. O agente
escolheu essa comparação restrita para a revisão 46, com evidência caso a caso.
A elegibilidade de metadados e os conflitos plain/LRC continuam avaliados pelo
classificador de origem. A comparação conserva acentos, ordem das palavras e
pontuação além da tipografia preexistente. A saída guarda o texto original e
registra os vínculos em complemento separado. A execução de 831 consultas é
manual e está pendente. Sete verificações sintéticas aprovadas. Guia
execucao_revisao_caixa_nova_amostra_v1.md.

## D-034 — Revisão conferida e diagnóstico nativo das chaves (06/11/2026)

43 real concluído pelo pesquisador/conferido: 3.647 aceitas, ganho de 2.222,
1.298 ambíguas, 4.164 sem candidato, 416 instrumentais, uma sem texto, zero
erro/pendência. Preservadas 1.425 aceitas/362 instrumentais de 42; 54 ambiguidades
viraram indicação instrumental. Tempo 41,79 s, sem rebuild. Taxa sem peso 38,28%,
ponderada 38,30%; não é prova de representatividade ou revisão humana dos vínculos.

Transições: 1.614 aceitações após bloqueio plain/LRC e 608 após veto de versão.
Motivos restantes: 831 textos concorrentes, 153 versões sem elegível, 152
metadados, 108 plain/LRC, 40 limites, oito instrumental/texto e seis formatos.
Oito casos do primeiro motivo inspecionados pontualmente; diferenças persistiram
após whitespace. Não inferir que todos os 831 sejam conflitos semânticos reais.
Cobertura por popularidade/gênero continua desigual; não transportar margem do
sorteio completo ao subconjunto textual ou interpretar pesos como correção de perdas.

Doze consultas sem candidato inspecionadas por metadados e índices nativos,
com limites temporais/numéricos. Um exemplo &/and, mesmo título/duração próxima;
título de outra consulta apareceu com artistas diferentes. Nenhuma aceitação
decorrente dessas inspeções; não extrapolar suas frequências aos 4.164.

44/native_lookup_audit.py preparado para diagnóstico manual dos 4.164, usando
índices B-tree de nome/artista e FTS5 existentes. Sem varredura/rebuild ou corpo
de letra. Consultas parametrizadas, duração ±10 s, cem registros por método,
cinquenta salvos, dois segundos totais por consulta; truncamentos explícitos.
Classificação de indícios não aceita aliases/covers nem modifica status. Mesmo
artista/outro título ou mesma duração não prova mesma faixa. Sem popularidade,
gênero/peso ou similaridade aproximada para aceitar. Referência técnica oficial
SQLite no guia execucao_diagnostico_chaves_nova_amostra_v1.md.

Três testes sintéticos/lint aprovados: &/and como indício, outro artista como
não vínculo, limites e retomada preservando 43. Execução real 44 pendente. Após
resultado, justificar recuperação/revisão dirigida. Não iniciar modelagem por
ter atingido um número de aceitas ou aumentar cobertura sem critério.

## D-033 — Auditoria e correção de dois bloqueios indevidos (06/11/2026)

42 executado pelo pesquisador: 1.425 aceitas, 3.574 ambíguas, 4.164 sem candidato,
uma sem texto, 362 instrumentais, zero erro/pendência. O pesquisador questionou
a baixa recuperação e o significado de instrumental. Indicação vem do LRCLIB
e ausência de texto nos candidatos compatíveis; 87 herdadas/275 novas, sem uso
da instrumentalness Spotify ou confirmação humana. Preservar o sorteio.

Auditoria leve do estado 42 (9.526 decisões, agregação SQL com limite temporal)
identificou 2.139 plain_synced_conflict e 1.176 positive_version_conflict. Dez
consultas do primeiro motivo, em ordem determinística de hash, foram examinadas
por ID no dump; todas coincidiram após whitespace/tipografia, sem mudar palavras,
ordem, pontuação ou capitalização. Não é validação probabilística das 2.139.
Das versões, 1.023 tinham candidato já elegível; outra versão vetava a consulta.
Agente reconheceu a falha ao reutilizar esses filtros sem diagnosticar o efeito.

Correção fundamentada no comportamento e em exemplos, não em escolher regras
por desempenho preditivo. Novo VERSION nova-amostra-matching-v2, sem alterar
bytes, resultados ou protocolos 200k/42. Duas mudanças: ignorar diferença apenas
de whitespace entre plain e extração LRC quando igualdade exata for comprovada
em cada candidato; excluir candidatos incompatíveis quando há candidato
plenamente compatível, eliminando veto global por outra versão. Preservar
conflitos substantivos, qualificadores, convidados, duração e limite operacional.
Não usar similaridade aproximada, fingerprint flexível ou popularidade para aceitar.

43 preparado/testado em quatro verificações sintéticas; execução real manual
pendente. Alvos: 2.139 + 1.023 = 3.162 consultas, pelos índices prontos. Sem
rebuild, varredura de metadados ou nova amostra. Textos originais e 1.425
aceitas/362 instrumentais protegidos. 4.164 sem candidato/153 versões sem elegível
e demais causas permanecem fora da correção; investigar separadamente.
Não prometer que todos os alvos virarão aceitos. Guia revisao_bloqueios_vinculacao_v2.md.

Nenhuma reavaliação integral real, nova letra aceita, treino, embedding, PDF ou
publicação pelo agente; inspeções textuais limitadas, sem divulgar corpos.

## D-032 — Cache conferido e preparação da busca local (06/11/2026)

41 executado pelo pesquisador; resumo e hashes conferidos. 9.526 consultas,
682 aceitas, 87 instrumentais, 8.757 pendentes; zero erro/insuficiência de
metadados, 30,32 segundos. Não usar os 7,16% de cache como cobertura final.
Amostra, pesos, dados e resultados históricos mantidos.

Avança a recuperação autorizada por D-029/030. 42/new_sample_local.py preparado
para execução manual no SSD. Índice v2 real inspecionado só por meta/schema/
EXPLAIN e lista selada: completo, 33.714.178 registros históricos percorridos,
5.726.985 entradas/24.330 chaves de artista, mesmo código e identidade de dump.
Nenhuma faixa/letra real foi consultada pelo agente nesta preparação.

Reutilizar esse índice, cuja normalização corresponde à classificação v2,
em vez de assumir compatibilidade de índices antigos de normalização diferente.
A execução determina artistas não cobertos, registra a lista e só então cria
complemento separado/retomável para eles. Uma passagem de metadados pode ser
necessária; não reconstruir índices existentes, duplicar dump ou gerar índice
para toda a população Spotify. Trabalho pesado permanece manual.

Preservar 682 aceitas/87 instrumentais de 41 e todos os sorteados. Reutilizar
também negativas somente se decorrentes de busca controlled_lookup v2 completa,
sem limite operacional, da mesma consulta/snapshot/código, com origem comprovada.
Outras negativas e consultas novas seguem para busca; regras, tolerância e
conflitos de versões/textos não são relaxados. Ausência continua restrita às
chaves controladas no snapshot, sem alegar inexistência universal de letra.

Novos checkpoints por consulta, complemento por lote. Evidência não aceita
guarda IDs, metadados e hashes, sem duplicar corpos; candidatos recuperáveis
do dump por ID. Aceitas mantêm plain/synced originais e texto efetivo separado.
Nenhuma seleção usa popularidade/gênero/pesos; estes entram só na descrição
posterior. Nenhuma substituição de faixas ou decisão de modelagem.

Quatro testes em dump sintético de nove registros e lint aprovados, com
retomada, preservação dos vínculos, complemento e controle de versões. Execução
real 42 ainda pendente; guia execucao_busca_nova_amostra_v1.md. Não houve
varredura real, nova letra real, treino, embedding, PDF ou publicação pelo agente.

## D-031 — Sorteio conferido e reaproveitamento dirigido de cache (06/11/2026)

Pesquisador executou 40 sortear; conferidos resumo concluído, hash do plano,
Parquet e agregados. 9.526 faixas, 82 gêneros, soma dos pesos 1.159.764 com erro
numérico 2e-10. Agente não repetiu sorteio, CSV ou processamento individual.
Doze médias: máximo desvio absoluto 0,01901 DP; maior desvio por período
0,4050 pp. Gêneros ponderados coincidem por construção, sem teste independente
de representatividade. Manter o sorteio; diferenças não justificam reamostragem.

Interpretados dispersões e quantis além de médias; não alegar igualdade de
distribuições. Duração/speechiness têm DP amostral cerca de 3,6% menor. Relatório
interpretacao_nova_amostra_catalogo_v1.md e duas figuras PNG/SVG produzidos de
agregados e inspecionados. Metas de dimensionamento não corrigem futura seleção
de letras nem estabelecem suficiência preditiva.

Próximo passo autorizado no plano é recuperar letras: começar pelo reaproveitamento
**exato** de decisões v2/v1. 41/sample_cache_reuse.py preparado/testado (seis
verificações sintéticas), execução real manual pendente. O agente inspecionou
somente schemas/planos de acesso/metadados dos caches (1,04/6,20 GB, WAL vazio);
nenhum texto real ou consulta de faixa foi lido. Não recalcular hash integral
dos bancos só para esta preparação: caminho/tamanho/mtime registrados e hashes
de cada texto importado conferidos durante a execução.

Reuso exige mesma consulta completa e fingerprint, duração/qualificadores,
integridade do texto efetivo e vínculo ao ID LRCLIB. Decisão exata v2 tem
prioridade; v1 somente na ausência da consulta no v2. Nunca usar v1 para contornar
uma decisão v2. Não transferir apenas por track_id ou chave de composição.
Sem nova aceitação por critérios relaxados ou releitura massiva do dump.

Aceitações/instrumentais anteriores ficam como decisões herdadas, sem alegar
revisão humana. Casos não aceitos, erros e ausência no cache ficam distintos;
negativa antiga não vira ausência de letra. Todos os sorteados e pesos continuam
no resultado; nenhuma substituição de perdas. Checkpoint novo por consulta,
campos originais intactos, textos privados separados de agregados públicos.
Conclusão desta passagem não é conclusão integral da recuperação. Não houve
busca no SSD/rede, índice novo, encoder, treino, PDF ou publicação.

## D-030 — Preservação acadêmica e nova amostra dimensionada (06/11/2026)

Pesquisador solicitou guardar os resultados da monografia e avançar. Pacote
local de 430 arquivos/16.872.772 bytes concluído em
reports/preservacao_monografia_20261106, com PDFs/fontes/tabelas/figuras e
agregados históricos/descrição nova; originais preservados, hashes/CRC de cada
membro conferidos. Retrato da documentação incluído; não é backup externo ou
publicação. Bases, letras, vetores/modelos não foram duplicados.

Sob autonomia D-029, adotadas metas de planejamento antes do novo sorteio:
proporção global com margem individual aproximada de 1 pp/95%, e doze médias
de metadados com margem até 0,05 DP/confiança conjunta aproximada 95% usando
Bonferroni. Metas são decisões do estudo, não números impostos pela literatura.
Fundamentação: Cochran (1977), capítulos 3–5, e Statistics Canada (2010),
capítulos 6–8; fontes verificadas e fórmulas em plano_nova_amostra_catalogo_v1.md.

Desenho: AAS sem reposição independente nos 82 gêneros, alocação proporcional
com maiores restos/empate alfabético, π=n_h/N_h e peso=N_h/n_h; semente20261106.
Gênero fundamentado pela descrição; precisão usa todos os doze metadados,
incluindo BPM, sem depender exclusivamente da PCA. Perfis de BPM reconciliados
com reinserção dos 1.199 zeros documentados, sem excluí-los do cadastro.

Primeiro tamanho inteiro que atende às metas nesse algoritmo: **9.526**, com
5–179 por gênero. Cenários de 2/1,5 pp: 3.195/4.254. Margem escolhida efetiva
0,999974 pp; maior margem conjunta das médias 0,028874 DP. Não se declara
ótimo global, igualdade de distribuições, precisão por gênero/cauda extrema,
precisão preditiva ou quantidade de letras garantida. Margem de proporção é
individual; não conjunta com todas as características. Aproximação normal e
resposta completa explicitadas. Perdas na recuperação exigirão diagnóstico e
hipóteses próprias para eventual inferência além do domínio observado.

40/sample_redesign.py preparado, quatro verificações sintéticas e lint aprovados;
dimensionamento real executado pelo agente só em agregados (sem CSV individual).
**Sorteio real pendente manual**, um comando `40_preparar_nova_amostra.py sortear`.
Saídas em pastas novas, vinte campos originais preservados, comparativos sem
ressorteio para melhorar aparência e nenhuma busca/modelo embutidos. Não altera
amostra antiga, pesos D-017, folds, modelos, selos ou PDFs. Próximo consumidor:
organizar recuperação das selecionadas com reaproveitamento de evidência compatível.

## D-029 — Descrição inicial e novo dimensionamento amostral (06/11/2026)

Pesquisador definiu expressamente a sequência que passa a orientar o trabalho:
descrição completa do catálogo original, com dicionário/distribuições/gênero/
período/relações/PCA; dimensionamento de uma nova amostra menor com técnica
estatística fundamentada; busca das letras sorteadas; modelagem a decidir depois.
Descritiva é parte inicial para apresentar os dados, não o centro do TCC.
Não desviar para novos treinos, classificação ou cruzamento integral automático.
Resultados anteriores e PDFs permanecem preservados.

Autonomia autorizada para preparar esse trabalho, com execução integral manual
pelo pesquisador. Fluxo simples: um comando de descrição; nenhum smoke obrigatório
ou rodada de treinamento. Linguagem escolhida: Python, no ambiente existente.
Script 39/catalog_description.py preparado: todos os campos, perfis e relações,
PCA das dez contínuas acústicas/duração, com ano/gênero para contextualização.
Popularidade é descrita também em log1p, sem mudar resposta de modelos.
Registros inválidos permanecem na população e são contados; casos completos
apenas nas análises multivariadas, com denominadores explícitos.

Não foi fixado tamanho ou método da nova amostra: a escolha virá depois da
descrição, fundamentada em livro/artigo e critérios de confiança/precisão e
composição. Nenhuma probabilidade de recuperação ou representatividade textual
é garantida pelo tamanho. A escolha efetiva e o tratamento de perdas serão
documentados na etapa própria, sem impedir o trabalho descritivo atual.

Preparação inicial: execução real 39 estava pendente, com conferência sintética
e lint concluídos. Nenhuma leitura integral pelo agente. Guia:
docs/execucao_descritiva_catalogo_completo_v1.md.

### Conclusão real da descrição e encaminhamento

Pesquisador executou 39; resumo concluído em 1.159.764 faixas/vinte campos/
82 gêneros e 32,71 s registrados. Conferidos 44 arquivos por hash, totais de
categorias e histogramas, 36 eta² e 100 coeficientes de PCA; treze figuras reais
inspecionadas. Matrizes agregadas reproduzem a PCA até erro numérico <4e-15,
sem releitura de linhas individuais ou recalcular PCA no catálogo.

Gênero apresenta eta² de 45,99% para energia, 51,76% para acousticness e 8,50%
para BPM, fundamentando estudar estratificação sem presumir balanceamento total.
PCA de dez contínuas em 1.158.565 casos completos: 44,35% em dois eixos,
57,85% em três, 95,66% em oito; não descreve clusters ou variância do alvo.
Tempos zero (1.199) permanecem na população, fora apenas do cálculo multivariado.
Log1p mantém zeros e muda assimetria de +0,8100 a -0,7947: não apresentar como
solução demonstrada para simetria.

Interpretação concluída para a parte inicial do TCC, sem editar a versão 3.
Próximo: dimensionamento/alocação multivariada de uma amostra menor, com metas
e fontes explícitas. Nenhum desenho ou n adotado ainda. Não repetir treino,
busca ou recuperação por continuidade automática. Relatórios:
interpretacao_descritiva_catalogo_completo_v1.md e
verificacao_descritiva_catalogo_20261106.json.

## D-028 — Monografia consolidada com extensão ordinal (06/11/2026)

Após a conclusão/conferência de 36/37, pesquisador autorizou gerar nova versão
acadêmica. Entrada passa a reports/monografia_template_200k_v3/main.tex, com
PDF de 45 páginas e ZIP completo para Overleaf/XeLaTeX/BibTeX. Objetivos integrados
à introdução, mantendo a narrativa catálogo → amostragem → LRCLIB → domínio aceito.
Regressão original, extensão ordinal/PCA e sensibilidade posterior são distinguidas;
não substituir resultado principal pela alternativa de maior AB. Ganho textual
modesto, custos de decisão, chances proporcionais, grade finita, exposição
histórica e limites de cobertura/inferência permanecem explícitos.

Catorze tabelas, sete figuras, 34 equações e 32 referências originais; cinco fontes
acrescentadas/conferidas em editoras/periódicos/autores para ordinal/PCA/perdas.
Nenhum TCC citado como autoridade científica. Script 38 gera quatro tabelas e
copia duas figuras somente de agregados leves; textos TeX editáveis, sem dados
individuais ou novos ajustes. Versões anteriores e fontes seladas conferidas por
hash. Compilação real, ZIP extraído/recompilado, páginas revisadas, sete testes
e lint aprovados. Evidência: reports/verificacao_monografia_template_200k_v3.json.
Próximo trabalho é revisão acadêmica com o orientador, sem experimento automático.
Não foi feito commit/push nesta entrega editorial.

## D-027 — Produção ordinal concluída e sensibilidade da decisão (05/11/2026)

34 real concluído pelo pesquisador: vinte partes ordinais/cinco referências,
480 ajustes internos, 77.535 probabilidades por variante e zero pendências.
Hashes das 25 partes/arquivo global e checksums internos conferidos, sem refit.
Máximo interno 311 iterações, gradiente 9,99e-7 e zero avisos registrados.

BA principal 59,19/59,69/60,45/60,58% em Baseline/Tradicional/Profundo/Combinado.
Ganhos Combinado−Baseline +1,39 ponto e Combinado−Profundo +0,13 ponto. Sensibilidade
elevada 40,75%, precisão 72,38%. PCA95 selecionada em 3/20, nove das onze numéricas;
lambda mínimo da grade em 20/20. Documentar limite sem expandir a grade por
resultados conhecidos. Sem causalidade, significância ou inferência ao catálogo.

35 analisa somente agregados, reconcilia métricas com matrizes, compara com a
regressão categorizada e inspeciona parâmetros de três PCA, sem fit/predict novo.
Resultado ordinal Combinado tem BA apenas +0,16 ponto frente à regressão
categorizada. Curvas mostram desvios de calibração; chances proporcionais não
foram formalmente testadas. Resultados atuais preservados como principais.

Sob autonomia D-025, preparar sensibilidade delimitada por problema demonstrado:
59,25% das elevadas não são reconhecidas pela regra argmax. Regra alternativa
fixa argmax p(k|x)/pi_k usa proporções do respectivo treino externo e atribui
importância igual às classes no risco de classificação. Sem otimizar custos no
teste, retreinar, recalibrar ou normalizar escores como novas probabilidades.

Análise POSTERIOR aos resultados, condicional às probabilidades de modelos cujas
configurações foram selecionadas para a regra original. Não é CV completa de
nova pipeline, não substitui retrospectivamente principal nem comprova melhora
integral do procedimento. Adoção futura como principal exigiria protocolo e
participação do pesquisador. Mesmas observações/folds; pesos amostrais apenas
na avaliação de sensibilidade, sem correção automática da seleção de letras.

Script 36 preparado/testado; leitura integral individual é manual. 58 testes
selecionados e lint aprovados; 35 real concluído, 36 real pendente. Protocolo:
protocolo_sensibilidade_decisao_ordinal_v1.md; guia de mesmo sufixo execucao_.
Relatório interpretacao_classificacao_ordinal_200k_v1.md e verificação
reports/verificacao_producao_ordinal_20261105.json. Não repetir 34.

### Conclusão da sensibilidade e consolidação — 06/11/2026

Pesquisador informou conclusão real de 36; resumos, assinaturas e agregados
conferidos. 77.535 faixas/21.893 componentes, métricas principais reproduzidas,
sem treino, mudança de probabilidades ou substituição de resultados principais.
37 reconciliou as 120 métricas decisórias com 1.080 células e consolidou figuras.
Somente a cauda delimitada de 128 faixas/96 componentes foi inspecionada em nível
individual, sem repetir a análise completa da coorte pelo agente.

Combinado: BA 60,58→64,43%, acurácia 65,82→63,09%, sensibilidade elevada
40,75→71,52%, precisão elevada 72,38→51,75%; Macro-F1 0,6251→0,6208.
Reconhece mais 3.901 elevadas, com mais 6.485 falsas elevadas; sensibilidade
intermediária cai de 66,07% a 49,98%. É compromisso de custo, não ganho universal.
Incremento textual alternativo sobre Baseline +1,16 ponto e sobre Profundo +0,13.

Na cauda observada ≥80, principal/alternativa atribuem nível ≥40 a 119/125 das
128 faixas; não confundir com detector binário de hits ≥80. Manter regras lado
a lado e caráter exploratório condicional, sem escolher principal retrospectivo
pelo resultado externo. Não iniciar mais treinos/coletas sem nova justificativa.
Próxima ação é consolidação acadêmica em versão nova, preservando PDFs atuais,
e discussão da utilidade dos erros com o orientador. Nenhum novo comando pesado
é necessário para esta consolidação. Relatório:
interpretacao_sensibilidade_decisao_ordinal_v1.md; verificação:
reports/verificacao_sensibilidade_ordinal_20261106.json.

## D-026 — Classificação ordinal e triagem técnica preparadas (05/11/2026)

Continuidade técnica sob autonomia autorizada em D-025. 31 real tem suporte
aprovado; 32 v1.1 real concluiu 133 fichas. Triagem 33 concluída apenas nessas
fichas, sem consultar dump/caches novamente: quarenta casos aceitos, 35 com
metadados selecionados compatíveis e cinco sem candidato selecionado disponível.
Não houve revisão semântica humana, estimativa de precisão ou alteração de vínculo.
Truncamento/limites são inconclusivos, não prova de erro. Não ampliar cruzamento
integral ou ajustar aceitações automaticamente para tentar melhorar o resultado.

Preparar logística ordinal com chances proporcionais, limiares ordenados e L2,
quatro blocos, cortes 20/40 e mesmas observações/folds/vetores. Implementação de
verossimilhança estável e gradiente analítico com SciPy, sem pacote novo. Chances
proporcionais é hipótese ainda não testada formalmente. Não usar coeficientes
penalizados como evidência causal ou p-valores convencionais.

Grade técnica definida antes de resultados ordinais reais: lambda 0,001/0,01/0,1/1,
com/sem PCA95 apenas nas onze numéricas Baseline. Seleção pela acurácia balanceada
da matriz interna somada, empate favorece penalização maior e ausência de PCA.
Pré-processamento dentro de cada treino; pesos iguais no ajuste e pesos originais
somente na sensibilidade da avaliação. Classificação por maior probabilidade, sem
ajuste de corte no teste. Referência pelas proporções do treino externo.

Script 34 preparado e testado com fixtures. Pesquisador executa primeiro smoke,
sem métricas científicas globais, com recarga auditada. Depois de conferir saída,
um bloco de produção mede custo antes de retomar os vinte. Gate/checkpoints por
assinatura; erro de convergência interrompe, sem trocar família/grade. Sensibilidade
40/60 continua diagnóstica nesta execução, sem novos treinos automáticos.

53 testes selecionados, incluindo gradiente, verossimilhança independente,
384 dimensões sintéticas, PCA, retomada e reprodução das métricas, passaram.
Nenhum treino real pelo agente; 34 real ainda pendente. Fontes/modelos/PDFs da
primeira regressão preservados. Protocolo: protocolo_classificacao_ordinal_200k_v1.md;
guia: execucao_classificacao_ordinal_200k_v1.md; verificação em
reports/verificacao_classificacao_ordinal_20261105.json.

### Smoke ordinal real concluído — 05/11/2026

Pesquisador executou 34 smoke: completed=true, 318 faixas, treino externo 251 e
avaliação 67, 96 ajustes internos e quatro partes ordinais/uma referência. Recarga
das quatro probabilidades reproduzida com diferença máxima 0,0; gate aprovado.
Agente conferiu resumos/selos/hashes/metadados, sem refit ou reprocessar a coorte.
Métricas globais indisponíveis por desenho; escolhas internas do smoke não são
conclusões científicas ou razão para alterar grade/PCA. Próximo: lote limitado de
produção 34 all --limit-outer-blocks 1. Conferência em
reports/verificacao_smoke_ordinal_20261105.json. Código e protocolo permanecem.

### Primeiro lote ordinal e continuidade integral — 05/11/2026

Primeiro lote real concluído/conferido: Combinado externo 0, 24 ajustes internos,
reajuste 62.028/15.507 faixas, 1/20 partes e 19 pendentes, tempo registrado 105,42 s,
sem avisos registrados. Partes/checkpoints/fontes preservados e conferidos pelo
agente sem refit. Pesquisador pediu poder deixar toda a execução rodando e seguir
à análise depois; orientar 34 all sem limite, reutilizando o bloco pronto.
Não ampliar experimentos para ocupar a noite. Métricas globais só após conclusão.
Registro: reports/verificacao_primeiro_lote_ordinal_20261105.json.

## D-025 — Nova investigação de níveis e vinculação (04/11/2026)

Após reunião com o orientador, pesquisador autorizou condução autônoma do plano
proposto, mantendo a primeira regressão e a execução manual de trabalhos pesados.
O escopo autoriza desenvolver uma etapa exploratória nova; não autoriza apagar,
substituir ou alterar retrospectivamente métricas, modelos, folds e códigos selados.

Escolha técnica nesta delegação: começar nas mesmas 77.535 faixas, sem nova amostra
ou cruzamento integral. Níveis principais 0–19/20–39/40–100; sensibilidade única
0–39/40–59/60–100. Reagrupamento de bandas existentes, definido com suporte
descritivo antes de calcular métricas categorizadas. Limites operacionais, sem
significado oficial de hit e sem selecionar cortes por melhor desempenho.

Critério primário planejado para classificação: acurácia balanceada; complementos
por classe, macro-F1, erros extremos e probabilidades/calibração quando houver
classificador treinado. Pesos iguais no treino; pesos originais só na sensibilidade
de avaliação. D-017 continua regendo a regressão anterior. Manter grupos/CV 5×3
quando a coorte não mudar. Nova coorte/vínculos exigiriam auditoria de componentes.

31 agregados foi executado sobre 2.009 linhas de contagens públicas, sem dados
individuais; confirma 34.069/30.785/12.681 nas classes principais. 31 previsoes
foi preparado para execução manual: alinha/confere selos e categoriza as previsões
antigas. Não representa resultado de logística, não produz IC nem teste independente.

32 prepara piloto de até vinte consultas por célula status×cauda ≥80, unidade de
revisão sendo consulta única. Evidências existentes por chave, sem buscar letras.
Ficha parcialmente mascarada, sem status/popularidade e sem texto de letra, com
campos de revisão vazios. Preparação não estima precisão/recall de matching.
Manter incompatíveis/ausências/limites como inconclusivos; não relaxar regras para
atingir cobertura. Novo cruzamento integral depende de necessidade demonstrada.

Depois dos diagnósticos, preparar logística ordinal regularizada; PCA das numéricas
padronizadas com 95% de variância como alternativa dentro dos treinos. Log1p,
pesos por custo, correção massiva do encoder e amostra menor não são executados
por esta abertura. A classificação permanece preditiva/associativa, sem causalidade
ou generalização automática. Revisão dos objetivos como introdução será incorporada
na próxima versão acadêmica, preservando a monografia anterior.

Protocolos: protocolo_niveis_popularidade_200k_v1.md e
protocolo_piloto_vinculacao_200k_v1.md. Evidência de preparo/testes e o que foi
realmente executado em reports/verificacao_nova_etapa_20261104.json.

### Adendo de execução e correção — 05/11/2026

31 previsoes executado pelo pesquisador, completed=true; 77.535 faixas e 21.893
componentes. Suporte aprovado em todas as partições, mínimos 2.381 faixas/1.322
componentes por classe. Acurácia balanceada categorizada Baseline 0,583175 e
Combinado 0,604247, sem refit nem inferência de significância.

32 interrompido antes de selecionar/exportar fichas: popularity é large_string
no Parquet bruto. Corrigir somente o módulo novo do piloto: coluna derivada
review_popularity_numeric Float64, validação de finitude/inteiro/0..100 e ordenação
numérica, preservando popularity original. Fixtures passam a reproduzir tipos
textuais de popularidade e duração; teste específico 9 versus 100 impede seleção
lexicográfica errada do representante. Valores inválidos bloqueiam, sem exclusão.

Código e selo mudaram; não reutilizar owner da tentativa falha. v1.1 grava em
private_linkage_review_200k_v1_1 e reports/piloto_vinculacao_200k_v1_1, mantendo
pastas v1 intactas. Mesmo comando 32; não repetir 31. Critérios científicos,
população, cortes, seed e pesos não mudaram. Testes/correção não executam o piloto
real pelo agente. Detalhes em reports/verificacao_correcao_piloto_20261105.json.

## D-024 — Organização e publicação do repositório (02/11/2026)

Pesquisador autorizou revisar a trajetória, retirar materiais não usados da
versão corrente e publicar os códigos/documentação no GitHub, com novos commits e
comentários em português. Remoto existente: corzxv/tcc-popularidade-musical,
master; visibilidade privada preservada. A autorização inclui commit/push; não
inclui tornar público, reescrever commits anteriores ou retreinar modelos.

A revisão dos 18 commits anteriores e das importações distingue linha recente,
dependências históricas e materiais apenas locais. Módulos antigos ainda
importados permanecem nos caminhos originais. Oito arquivos de prévias/roteiros
superados saem somente do índice: originais locais e histórico são preservados.
Dados brutos, letras, matrizes, modelos/vetores, caches e credenciais não entram.

README e guias em português passam a apontar para reprodução e monografia atual.
Requisitos científicos observados registrados separadamente. `.gitattributes`
impede conversão de quebras de linha: os hashes da execução selada usam bytes.
A política de idioma vale para textos novos; códigos/protocolos selados e commits
históricos não são traduzidos por alteração de bytes ou reescrita de história.

Script 30 audita caminhos, tamanho, segredos e tabelas individuais nos blobs do
índice, inclusive ZIP atual. CI contém somente auditoria/lint/testes leves, sem
encoder, corpus ou treino. Relatório de publicação registra testes, preservação,
seleção e confirmação remota; preparação não é presumida como push concluído.

Execução confirmada: commit principal 082a9a0 enviado ao remoto; 564 arquivos
versionados, 394 testes locais e lint aprovados. Os 15 selos científicos e 154
artefatos acadêmicos anteriores foram conferidos. CI inicialmente falhou por
Polars ausente no ambiente; a configuração foi corrigida em 9b375a8, com 19
testes direcionados locais e CI aprovada. Não houve alteração científica.
Relatório: reports/publicacao_github_20261102.json. Commits históricos não foram
reescritos; retirar do índice atual não apaga conteúdo de commits anteriores.

## D-023 — Relatório no template e referências originais (02/11/2026)

Pesquisador forneceu Template_Relatório_TCC.zip e relatorio_tcc_ana.zip e pediu
reescrita direta, fórmulas fundamentadas e narrativa Spotify bruto → amostra →
LRCLIB → aceitas → modelos. Solicitou BDM e referências originais pertinentes
localizadas em TCCs de Estatística, sem citar esses TCCs como fontes metodológicas.
Esse escopo editorial não reabre a modelagem congelada em D-022.

Nova entrada: reports/monografia_template_200k_v2/main.tex, ZIP e PDF TeX de 34
páginas. Cinco seções principais, dois apêndices científicos, dez tabelas, cinco
figuras e 27 referências originais. Versão anterior de 57 páginas e seus arquivos
preservados. Inventário/hashes/pendências administrativas ficam fora do PDF.

Nome corrigido com resposta explícita: **Leandro Tavares Correia**, conforme
SIGAA/Departamento. Correa em D-022 é informação histórica, sem editar PDFs antigos.
Título: “Contribuição preditiva de representações de letras para a popularidade
no Spotify”, dentro da autorização para defini-lo. Sem dados de defesa inventados.

Diagramação segue template/Ana: article 12pt/A4, margens, cabeçalhos, espaçamento,
pré-textuais e equações por subseção. Backend autor-data abntex2/BibTeX acompanha
Ana, em lugar do Biber do template; duplicações/numeração fixa corrigidas.
BDM consultada: Escobar (10483/41348), Mendonça (10483/36446), Loreto (10483/34267).
Indicações Cochran, Lohr, Hyndman e Izbicki/Santos rastreadas às fontes originais,
com edições conferidas. Critério é pertinência e verificação, não copiar bibliografia.

Descrição usa agregados existentes. 33.714.178 são metadados percorridos no
snapshot LRCLIB, não letras distintas/aceitas. Não inventar seu censo global de
idiomas. Fórmulas conferidas com a implementação: equivalência usa t/Satterthwaite;
limites condicionais dos contrastes mantêm sua aproximação normal. Sem alteração
de dados, código científico, modelos, folds, população, pesos ou estimando.

34 páginas revisadas, compilação TeX/BibTeX e editor integrado conferidos; dez
testes leves/lint passaram. Script 29 apenas editorial em agregados públicos
pequenos. Relatório reports/revisao_template_monografia_200k_v2.md e verificação
de hashes. Próxima ação: revisão acadêmica com orientador na nova entrada.

## D-022 — Encerramento principal e monografia consolidada (02/11/2026)

Instrução explícita do pesquisador: congelar modelos, previsões, folds e resultados
atuais e concentrar o desenvolvimento na monografia completa; não iniciar novos
treinos, buscas LRCLIB ou embeddings massivos. O ganho Combinado/Baseline de 2,84%
e o incremento pequeno/inconclusivo frente ao Profundo permanecem. Dependência da
CV, seleção de letras, exposição histórica, cauda e desvio de tokenização devem
acompanhar a interpretação; limites auxiliares não cobrem a incerteza integral.

Orientador informado pelo pesquisador: **Leandro Tavares Correa**. Autorizou seguir
com título escolhido pelo agente: “Representações textuais de letras e popularidade
observada no Spotify: contribuição preditiva incremental no domínio com letras
aceitas”. Não presumir titulação, banca ou data de defesa.

Nova fonte única: reports/monografia_consolidada_200k_v1/main.tex, sem substituir
os dois pacotes parciais. Texto completo para revisão: 11 capítulos, quatro
apêndices, 14 tabelas, oito figuras e .bib com 19 referências. PDF compilado do
TeX tem 57 páginas; não é o PDF ReportLab de uma etapa anterior. Pacote ZIP
standalone contém os recursos necessários e apenas agregados públicos pequenos.

Reaproveitamento documentado de 195 materiais acadêmicos, com 135 textos lidos.
História LFM2b, v0.1–v0.9 e coorte de 58.633 não foi misturada ao resultado
Ridge recente. Caracterização das fontes, probabilidades/pesos, seleção, entrada
textual efetiva e parecer 25–27 integrados à redação. Nenhum novo experimento.

Compilação Tectonic 0.17.0/BibTeX, revisão visual e referências cruzadas conferidas;
modelo institucional não localizado no repositório, sem declaração de conformidade
UnB/ABNT. Datas da resposta, versão do CSV, significado de year, elementos de
depósito e avaliação humana do matching continuam como pendências específicas,
não impedimento para entregar o texto completo revisável. Próximo trabalho:
revisão com orientador, conforme relatório de consolidação/Apêndice D. Não reabrir
a modelagem automaticamente sob pretexto de corrigir redação ou preencher lacunas.

## D-021 — Fechamento metodológico solicitado após o PDF (02/11/2026)

Pesquisador solicitou investigar inferência pareada, auditar representações,
aprofundar cauda/clipping e mapear pendências da monografia, sem novos treinos,
buscas LRCLIB ou experimentos custosos. Escopo realizado em 25/26/27 e parecer
reports/parecer_fechamento_metodologico_200k_v1.md; resultados principais/PDF/ZIP
preservados. Código/protocolos 19–23 não foram editados.

Modelo auxiliar de incerteza: linearização da razão de totais de diferenças
pareadas por componente dentro de cada teste externo, condicionando separadamente
em seu treino. Família Bonferroni dois contrastes × cinco folds, separada por
ponderação; combinação ponderada dos extremos sem independência entre folds.
Limites 95% nominais Combinado−Baseline [−0,31400; −0,16073] e Combinado−Profundo
[−0,03027; +0,00347]. Exigem independência/regularidade de componentes em uma
superpopulação auxiliar, não demonstradas pelo desenho da amostra aceita. Não
são IC integral da CV/treinamento ou do catálogo, nem confirmação independente.
Não usar cinco folds como réplicas, bootstrap simples de perdas como inferência
integral ou estabilidade individual do Ridge como prova da estabilidade relativa
da comparação. Métodos completos investigados, mas sem necessidade de iniciar
refits para encerrar a comparação exploratória atual.

**Achado real:** `query: ` tokenizado à parte acrescenta token de espaço ID 6.
Difere da concatenação oficial em 11 frases artificiais e oito textos da amostra.
Quatro frases artificiais em duas receitas (oito forwards curtos) produziram
cossenos 0,99664–0,99943; não medem impacto preditivo no corpus. Esse diagnóstico
limitado foi motivado pela evidência concreta; zero embeddings do corpus gerados,
zero vetores exportados/cache alterado. Corrigir descrição da variante atual e
recomendar receita corrigida em futura versão, sem modificar o script 20 selado.
Decidir por nova representação/cálculo integral requer justificativa adicional e
participação do pesquisador; não declarar impacto nulo ou invalidar métricas sem
evidência. Pooling/L2/cobertura adequados aos critérios; oito textos × 21
descritores reproduzidos exatamente. Auditoria integral de vetores anterior (21)
mantida distinta da inspeção pequena atual.

Cauda: 128 faixas/96 componentes, y=80–96, todas subestimadas por quatro blocos.
Combinado: y médio 81,8125, previsão 52,4414; residual mediano −28,7755. Cauda
representa 0,1651% dos casos e 0,5975% do erro absoluto, contribuindo 0,04849
ponto ao MAE global. Condicionar no alvo não equivale a calibração por previsão.
Clipping analisado como sensibilidade pós-resultado autorizada: Combinado
8,11512→8,09701, mesma ordenação; não altera cauda. Nenhuma substituição do
resultado principal. 615 negativos são limite do Ridge irrestrito, não prova
de corrupção dos vetores. Não mudar estimando para hits por esse diagnóstico.

Próximo: integrar parecer/errata à monografia, fontes/normalização/matching,
referências e limites; datas de popularity/versão Kaggle não confirmadas devem
permanecer explícitas. A análise de integridade não certifica precisão semântica
do matching. Nenhum novo treino pesado necessário/recomendado nesta rodada.

## D-020 — Diagnósticos concluídos e escrita da linha recente (02/11/2026)

23 executado pelo pesquisador: 77.535 casos, 30 partes/métricas reproduzidas,
21.893 componentes, 0,608 s, sem treino/IC. Ganho Combinado/Baseline nos cinco
folds e sinal negativo dos cinco contrastes em toda retirada condicional de
componente, com previsões fixas. Não interpretar isso como IC ou retreino.

Limites concretos incorporados ao texto: MAE 29,3711 na faixa 80-100 (128 casos),
piora no grupo de idioma incerto (180), e melhora em 59/76 gêneros com métricas
publicadas. Mantidos todos os casos e as quatro chaves históricas indeterminadas;
116 células com métricas/77 apenas contagens por limiares. Sem ajustes posteriores
para melhorar os números. Código/protocolos 19–23 preservados.

Avançar para escrita em vez de novos treinos/buscas. 24 usa somente os agregados
públicos pequenos, gerando trecho parcial recente com seis tabelas/quatro figuras,
proveniência, fontes TeX/ZIP e PDF de leitura. O pacote Spotify-LFM2b histórico
permanece separado. Compilação TeX local pelo editor integrado verificada; PDF
de leitura ReportLab tem sete páginas renderizadas/revisadas e não é exportação
desse compilador, podendo ter paginação diferente. Não é monografia completa
nem classe institucional oficial. Nenhum dado individual/modelo incluído no ZIP.

Integração depende de identificar o arquivo principal da monografia completa,
solicitado ao pesquisador após busca no repositório encontrar apenas projetos
parciais. Isso é informação de localização, não pedido de nova aprovação trivial.
Enquanto isso, a entrega parcial é concreta e revisável. Revisão humana de
matching, redação dos demais capítulos e alcance de eventual inferência permanecem
explícitos. Não há processamento pesado novo imediato para a comparação Ridge.

## D-019 — Resultados Ridge preservados e diagnósticos descritivos (02/11/2026)

Execução 22 concluída manualmente: 20 partes Ridge/dez referências, mesmas 77.535
observações, cinco contrastes, zero pendências. MAE Baseline 8,352484,
Tradicional 8,295691, Profundo 8,128523, Combinado 8,115122; redução conjunta
2,842% frente ao Baseline. Com pesos originais, 2,781%, mesma ordenação.
Combinado−Profundo apenas −0,013402. Não equivale a significância, causalidade,
representatividade ou superioridade de toda representação/algoritmo.

Preservar protocolo, grade, pesos, folds, modelos e previsões; não ampliar grade,
aplicar clipping ou coletar novas letras com base no resultado externo observado.
Seis seleções de alpha no extremo inferior e previsões fora de 0..100 são limites
documentados da execução fixada, não falhas que autorizem substituí-la.

Escolha técnica seguinte: auditoria/diagnóstico 23 sem novos ajustes, splits,
bootstrap, IC ou p-valores. Conferir igualdade com base e partes, métricas e
contrastes; descrever folds/subgrupos e influência de retirar componente apenas
da avaliação, mantendo previsões fixas. Não chamar faixa de remoção de IC ou
leave-one-group-out com refit. Estado histórico unknown_key é separado de
detected_collision/no_detected_collision; ausência de detecção não é independência.

Subgrupos: idioma/status estimados, banda de popularidade/período originais,
gênero de Baseline e exposição do componente. Métricas públicas somente em
células >=100 faixas e >=20 componentes; demais células têm contagens/motivo,
sem alterar análise global. Isso não garante precisão/poder estatístico.
O protocolo é posterior à leitura das métricas globais; exploratório, não
pré-registro. Nenhuma alteração do domínio, estimando ou validação D-014/015/017.
Execução real dos diagnósticos é manual; agente só testa fixtures.

Intervalos/testes para o desempenho do procedimento exigem plano específico que
respeite componentes e dependência da CV. Não usar cinco folds como réplicas
independentes. Fundamentação em protocolo_diagnosticos_modelagem_200k_v1.md.
Primeiro texto interpretativo para monografia em reports/interpretacao_modelagem_200k_v1.md.

## D-018 — Comparação inicial Ridge e execução em etapas (01/11/2026)

Base/folds 21 concluídos pelo pesquisador: 77.535 faixas, 77.051 vetores auditados,
21.893 componentes, zero metadados ausentes/inválidos; cinco testes externos de
15.507. Sem treino realizado. Código/protocolo 21 preservados e selados.

Escolha técnica nesta preparação, dentro do plano de regressão regularizada:
Ridge comum aos quatro blocos, referências média/mediana, grade fixa de alpha
0,1/1/10/100/1.000/10.000, LSQR tol=1e-5/max_iter=10.000, duas threads. Não foi
escolhida pela popularidade ou por métricas externas recentes; estas ainda não
existem. Não equivale a comparar quatro famílias de algoritmos. O objetivo inicial
é avaliar incremento de representações com regularização comum e custo controlado.

Pré-processamento somente em cada treino; constantes numéricas centradas para
zero, categorias aprendidas no treino, sem PCA ou clipping. Alpha selecionado
por MAE interno reunido; empate exato favorece maior penalização. D-015/017
preservadas: CV 5×3, treino com pesos iguais, MAE não ponderado primário e MAE
ponderado apenas em sensibilidade das mesmas previsões externas. Não retreinar
ponderado nem ampliar grade guiando-se por teste externo/sensibilidade.

Script 22 smoke real executado pelo pesquisador: 318 casos em componentes
inteiros, externo 0/3 internos, quatro blocos/duas referências, 1,843 s,
72 ajustes internos sem avisos e reprodução exata de modelos recarregados.
Não é avaliação científica. Primeiro lote de produção concluído/revisado:
Combinado externo 0, 18 ajustes internos e refit, 67,775 s, sem avisos. Há 1/20
partes Ridge e duas referências salvas, 19 partes pendentes. Próximo all sem
limite retoma checkpoints, sem novo desenho ou alteração por desempenho parcial.
Checkpoint por ajuste interno/parte externa evita repetir concluídos. Métricas
globais somente com todas as 77.535 previsões por variante. São 390 ajustes
totais previstos, sem promessa de duração baseada em fixtures/smoke.

Contrastes descritivos pré-fixados no protocolo_regressao_200k_v1.md, sem p-valores
ou intervalos que ignorem grupos/dependência da CV. Eventual inferência exige
método declarado antes de uso. Exposição histórica e alcance observado mantidos.

## D-017 — Ponderação principal e sensibilidade pareada (01/11/2026)

**Aprovado explicitamente pelo pesquisador nesta conversa, com seis condições:**

1. Pesos iguais por faixa no ajuste e nas métricas principais dos quatro blocos.
   Estimando: desempenho preditivo médio na distribuição empírica das 77.535
   faixas observadas com letras aceitas, sem generalização automática ao catálogo.
2. Preservar pesos amostrais originais e estratos para descrição, cobertura e
   diagnóstico de seleção, bem como sensibilidade posterior.
3. Comparar MAE não ponderado e MAE ponderado original nas mesmas observações,
   previsões externas e folds, verificando sensibilidade das conclusões sobre
   incremento de descritores/embeddings à ponderação.
4. Pesos originais não corrigem automaticamente disponibilidade de letras.
   Ampliação de inferência exige estimando, hipóteses e cobertura explícitos.
5. MAE não ponderado é primário para comparação/seleção; RMSE e R² são
   complementares. Ponderar apenas a avaliação de sensibilidade não pondera
   o treinamento, que permanece com pesos iguais. Não retreinar/selecionar pelo
   resultado ponderado como parte desta análise de sensibilidade.
6. Documentar política e justificativas na metodologia da monografia, preservando
   CV agrupada aninhada 5×3 e execução pesada manual pelo pesquisador.

Texto para a monografia em metodologia_modelagem_200k_v1.md. O MAE ponderado
normaliza pela soma dos pesos dos casos observados; não é estimador identificado
do risco no catálogo sob seleção textual desconhecida. Mesmas previsões externas
para comparar blocos e ponderações; métricas globais reunidas, não média de R²
dos folds. Incerteza deverá respeitar componentes/dependência da CV.

Implementação da próxima etapa: script 21 prepara base/folds e manifesto dos
quatro blocos, com política explícita; não ajusta modelo nem aplica ponderação.
Novos campos model_* preservam originais, inválidos ficam nulos com registro
privado, transformações aprendidas somente nos treinos futuros. Folds por
componentes, balanceamento determinístico de contagens sem usar alvo; desenho
5×3 aprovado não alterado. Atualização: script 21 executado e auditado, conforme
D-018; smoke real de 22 concluído, produção permanece pendente.

## D-016 — Encoder multilingue congelado e teste antes da escala (01/11/2026)

Script 19 executado pelo pesquisador: completed=true, 77.535 faixas, 77.051 inputs
únicos, 21 descritores finitos, 21.893 componentes, maior 186, nenhuma chave não
resolvida; campos/pesos preservados. Os 484 reusos de texto não removem faixas.
`text_no_lexical_segments` é constante zero; tratamento de constantes fica no
pré-processamento interno ao treino, sem reextrair o corpus.

Escolha técnica para representação profunda: `intfloat/multilingual-e5-small`,
commit `614241f622f53c4eeff9890bdc4f31cfecc418b3`, CPU float32, dimensão 384,
prefixo query, contexto total 512 e sobreposição de 32 tokens. Critérios: corpus
multilingue, dimensão/custo e infraestrutura existente; nenhum teste preditivo
foi usado na escolha. Fontes oficiais e limites no protocolo novo, separado do
contrato textual v1 já selado. Compatibilidade/ganho semântico ainda não comprovados.

Preparar download manual, smoke até 24 inputs e modo integral separado com
checkpoint. Escala exige smoke verificado sob o mesmo selo e revisão do resultado;
não inicia automaticamente. Reusar utilitários de janelas/normalização/agregação
e integridade vetorial, sem importar vetores antigos. Não truncar textos longos,
excluir idiomas ou carregar pesos/rede na preparação pelo agente. Nenhum novo
modelo preditivo, fold ou embedding real foi produzido nesta preparação.

**Atualização operacional:** download e smoke reais concluídos pelo pesquisador.
Resumo completed=true, 24 vetores de 384 dimensões, 68 janelas até 512 tokens,
55,26 s, reprodução máxima 0,0 e cobertura integral confirmada nos metadados.
Avisos do tokenizer não invalidaram o teste; código/protocolo selados preservados.
Primeiro lote all --limit-texts 1000 executado: 1.000 novos + 24 reutilizados,
296,25 s, dimensão 384, entradas até 512. Integral posteriormente concluída após
pausa/retomada: 77.051 vetores, 77.535 referências, zero pendências, 91.156 janelas
até 512. Última retomada: 27.352 novos e 49.699 reutilizados em 4.914,39 s.
Próximo passo manual é a montagem da base/folds (21), sem repetir inferência.
Sem alteração do código/protocolo/modelo. Não altera
população, encoder, desenho de validação ou critérios científicos aprovados.

## D-015 — CV agrupada 5×3 e contrato das representações (01/11/2026)

**Desenho aprovado explicitamente pelo pesquisador:** CV aninhada agrupada,
cinco folds externos e três internos, mesmos folds para Baseline, Tradicional,
Profundo e Combinado; declarar exposição histórica do teste antigo. Os folds não
foram gerados e nenhum treino recente foi executado. A aprovação não certifica
identidades universais dos grupos nem torna o estudo confirmação independente.

Após auditoria 17 concluída pelo pesquisador (77.535 consultas verificadas),
preparar 21 descritores lexicais/estruturais diretamente do texto aceito e
componentes ligados por artista/composição/texto. Preservar todos os idiomas,
as linhas e pesos; tratar nomes só com símbolos literalmente, sem excluir o artista
`!!!`. Não transportar os descritores LFM2b por ID (somente 13.558 IDs em comum;
compatibilidade de texto/versão não demonstrada).

Definições operacionais em `contrato_representacoes_200k_v1.md`. Segmentos Unicode
não são palavras universais; não prometer sentimento/legibilidade ou equivalência
com os descritores LFM2b. Representação profunda candidata multilingue ainda
precisa de revisão congelada, teste pequeno e execução manual; escolha não será
guiada por popularidade. Política de ponderação das métricas permanece pendente
de declaração antes dos modelos. Script 19 gera apenas descritores/componentes;
os resultados da geração real ainda são desconhecidos.

Atualização posterior: geração 19 e encoder 20 concluídos (D-016); a pendência
de ponderação foi resolvida por aprovação explícita em D-017. Folds recentes
concluídos em 21; modelos ainda pendentes, runner 22 preparado conforme D-018.

## D-014 — Domínio analítico observado e encerramento dirigido dos dados (01/11/2026)

**Aprovado explicitamente pelo pesquisador nesta conversa**, após apresentação
da alternativa de priorizar as letras aceitas da amostra recente. Condições:

1. Tratar as aceitas como domínio analítico observado; não presumir representação
   probabilística de todas as músicas com letras nem do catálogo Spotify.
2. Preservar amostra de 200 mil e pesos para descrição, cobertura e seleção.
3. Comparar quatro blocos nas mesmas observações/splits, prevenindo vazamento
   entre artistas, composições e versões relacionadas.
4. Declarar limitações; investigação futura de ampliação de alcance não bloqueia
   avanço no domínio observado.
5. Preservar o trabalho anterior; nova recuperação somente com evidência concreta
   de necessidade. Priorizar fechamento de dados, descritores, embeddings e modelos.

**Implementação operacional desta rodada:** organização lógica, sem movimentos
ou exclusões; referência provisória v2 de 77.535 aceitas, sem incorporar as 31
mudanças diagnósticas v3. Preparar auditoria manual de integridade, idioma e
linhagem antes de congelar contrato de dados. A v3 integral permanece adiada;
seu ganho de busca ampliada foi zero no diagnóstico, e testes sintéticos não
validam precisão real. Não reexecutar índices ou buscas de todo o catálogo.

**Recomendação técnica, ainda não decisão de implementação final:** descritores
diretamente do mesmo texto LRCLIB do embedding; reutilizar utilitários e validação
agrupada, não copiar descritores/vetores LFM2b por ID. Política multilingue,
encoder/recursos/licença, lista final de descritores, tratamento de textos/grupos,
ponderação de métricas e desenho de avaliação recente permanecem por congelar
após o diagnóstico. Isso não autoriza filtros de idioma ou novas exclusões.

O teste V0.6 exposto permanece parte da proveniência. A adequação para comparar
modelos dentro do domínio observado não é certificado de tamanho amostral ou de
validade do matching. Não treinar a Base v0.1 nem alterar modelos históricos.

## D-013 — Avaliação limitada v3 e parecer de domínio (01/11/2026)

Corrigir vetos globais v2: versão incompatível é excluída individualmente;
sincronização não suportada não invalida plain utilizável. Comparar sequência
textual sem caixa/espaçamento, preservando pontuação, palavras e repetições.
Reutilizar índices/caches existentes; busca aproximada só propõe revisão. Nenhum
novo índice automático. Avaliar 600/300/100 por AAS com probabilidades registradas,
seed fixa e orçamento padrão 600 s, antes da aplicação separada. Reavaliar também
aceitações antigas coerentemente; não impedir quedas de cobertura artificialmente.

Parecer independente usa base completa v2 inicialmente, sem SSD; atualização v3
só após aplicação. Fixar margens operacionais solicitadas antes da rodada, declarar
conhecimento prévio dos resultados. Razões de domínio e Taylor estratificado com
FPC usando toda a amostra; TOST 5% e decisão conjunta por todos os critérios.
Diferença relevante conjunta requer intervalos Bonferroni; raridade/variância
não estimável é inconclusiva. Não confundir matching, concordância marginal,
representatividade genérica e suficiência preditiva. Protocolos e comandos em
`docs/execucao_avaliacao_parecer_v3.md`. Execuções reais pelo pesquisador.

## D-012 — Rodada delimitada de recuperação de letras v2 (31/10/2026)

Preparar comando único `scripts/14_recuperar_letras_amostra_200k.py`, sem executar
recuperação real. Preservar amostra/pesos e resultados v1 (77.391 aceitações,
8.748 instrumentais). Reutilizar evidências/textos v1 em estado novo. Diagnosticar
perdas por motivo e conferir símbolos apagados; não importar ambiguidades como
aceitas nem modificar decisões v1 silenciosamente.

Adicionar chaves contextuais de versão e crédito feat./ft./featuring explícito,
sem dividir bandas por separadores ambíguos. Acentos e símbolos literais permanecem;
sem aliases/transliteração/fuzzy. Índice auxiliar separado, uma passagem retomável
de metadados, cobre os créditos primários necessários à rodada controlada. Não
variar regras/orçamento em ciclos até aumentar cobertura.

Permitir candidatos vazios quando o conjunto textual compatível é equivalente e
não há conflito positivo. Extrair apenas LRC de linhas validado; preservar fontes,
texto derivado e motivos de formatos não suportados/conflito. Fingerprint estrito
permanece; equivalência adicional só de sinais tipográficos listados no protocolo,
sem apagar palavras, versos, repetições ou diferenças clean/explicit. Duração
continua ≤10 segundos, sem escolher entre textos distintos. Alvo/gênero/peso não
participam do matching. Instrumental exige fonte, nunca corte de instrumentalness.

Exportar resultado integral, transições e métodos sem dupla contagem, comparações
antes/depois sem/com pesos e inspeção privada dirigida. Precisão ainda não validada
em dados reais; pesos não corrigem perdas por disponibilidade/aceitação. Sem novos
splits/modelos ou afirmações causais. Protocolo:
`docs/protocolo_recuperacao_letras_200k_v2.md`; execução:
`docs/execucao_recuperacao_letras_200k_v2.md`.

## D-011 — Letras locais e cobertura da amostra fixa (31/10/2026)

Preparar `scripts/13_buscar_letras_amostra_200k.py` para execução manual pelo
pesquisador, sem executar busca real na preparação. Reutilizar construtor/consulta
SQLite dos scripts 06/07, diagnósticos conservadores, fingerprint estrito e motor
de comparação amostral. Validar hashes, 200.000 IDs, desenho e 499 faixas ≥80;
preservar todas as linhas, originais e pesos, sem substituição ou filtro de idioma.

O índice anterior restringe artistas ao manifesto antigo. Reutilizá-lo após
validar selos e criar suplemento separado apenas para artistas adicionais, com
uma varredura retomável de metadados. Dump/índice/estado antigos permanecem
somente leitura. Não importar aceitações antigas: a nova guarda de versão e o
universo diferem. Estado e textos ficam em workspace privado exclusivo.

Matching recebe apenas artista, título e duração, com ID para ligação. Reutilizar
compatibilidade de versões e tolerância de dez segundos; adicionar igualdade do
título completo normalizado quando houver marcador de versão. Aceitar somente
texto simples único ou equivalência estrita de todos os elegíveis. Representante
determinístico só após equivalência. Não converter sincronização nem usar fuzzy,
fingerprint flexível ou popularidade. Instrumental exige evidência compatível.

Separar aceitação, ambiguidade, ausência, ausência de texto simples, instrumental,
metadados insuficientes, erro técnico e pendência. Checkpoints por consulta e
retentativas técnicas explícitas preservam resultados concluídos. A saída privada
mantém uma linha por faixa e referência para tabela de textos por consulta aceita.
Publicar apenas agregados, com denominadores reais/ponderados, diferenças de
proporções e médias padronizadas; pesos não corrigem seleção adicional por letras.
Idioma offline estima incerteza sem decidir aceite. Sem novos splits/modelos.
Detalhes: `docs/protocolo_busca_local_200k.md` e `docs/execucao_busca_local_200k.md`.

## D-010 — Amostra fixa estratificada de 200.000 faixas (31/10/2026)

Por solicitação do pesquisador, substituir a proposta amostral ainda aberta
da D-009 por desenho fixo: 200.000 IDs, seed 20261031, inclusão integral de
popularidade ≥80 dentro do total, e AAS sem reposição no restante por gênero ×
período × banda de popularidade. Reservar min(2,N_h), distribuir vagas por
capacidade residual e maiores restos inteiros, desempate por chave estável.
Trata-se de alocação desproporcional operacional, não ótima/proporcional pura.

Validar SHA-256, recontar/reconciliar 1.159.764 faixas e 499 ≥80 com a auditoria
concluída; bloquear antes do sorteio diante de IDs ausentes/repetidos,
popularidade inválida ou mudança material dos estratos. Não deduplicar por
título/crédito nem excluir versões, idiomas, ausências de título/artista ou
problemas acústicos. Todos os campos originais permanecem no Parquet.

Registrar probabilidades/pesos, versões/hashes e verificações. Comparar catálogo,
amostra sem pesos e com pesos; quantis pela inversa da CDF, desvio descritivo
com divisor soma(w), sem teste de significância como selo de representatividade.
Preservar amostra em reexecução idêntica; nunca variar seed para equilíbrio.
Letras, grupos de composição, splits, embeddings/modelos e interface estão fora
do escopo. Ausência futura de letra não causa substituição automática. A exposição
do teste V0.6 persiste. Protocolo e referências: `docs/plano_amostral_200k.md`.
Preparação verificada apenas com dados sintéticos; execução real pelo pesquisador.

## D-009 — Auditoria independente do catálogo original (31/10/2026)

Preparar CLI offline sobre `data/raw/spotify/spotify_data.csv`, anterior ao
matching, para execução real pelo pesquisador. Preparação verificada somente
com fixtures sintéticas; nenhuma amostra definitiva, split ou modelo criado.
LFM2b não é condição de elegibilidade. Não abrir LRCLIB nem buscar letras.

Faixa Spotify é a unidade inicial. Publicar escopos separados por linha e por
ID sem conflito; comparar duplicatas exatas incluindo índice e igualdade
substantiva sem índice. Não resolver IDs conflitantes nem escolher maior
popularidade. Campos originais permanecem e derivações são temporárias, com
prefixo `audit_`; exceções são contadas, sem arquivo de rejeitados. Gêneros são
células textuais inteiras; artistas/pares não são identidades universais.

Propor sorteio aleatório estratificado sem reposição com alocação proporcional
por período e gênero, avaliando esparsidade antes de adicionar popularidade.
Não fixar tamanho, cotas iguais ou buscar seed por equilíbrio. Disponibilidade
de letras e splits são etapas distintas. O teste V0.6 foi aberto em 14/10/2026;
novo sorteio não restaura independência. Futura divisão exigirá reconciliação
com registros/grupos anteriores e agrupamento por artista e composição
operacional. Regras e incertezas em `docs/auditoria_catalogo_spotify.md`.

## D-001 — Parquet + DuckDB

Polars processa Spotify e lotes LFM2b; Parquet Zstandard é a camada persistente; DuckDB cataloga views. Alternativa rejeitada nesta versão: banco servidor, por aumentar operação sem necessidade.

## D-002 — Popularidades separadas

`spotify_popularity`, `genius_lyrics_views` e `lfm_playcount` nunca são fundidas. A primeira é snapshot Spotify; a segunda são visualizações de letra no Genius; a terceira é contagem de escutas LFM-2b.

## D-003 — Matching conservador

Somente artista+título, nunca título isolado. Pares normalizados precisam ser únicos e compatíveis em versões. Ambiguidades são preservadas. Fuzzy gera fila de revisão, não decisão.

## D-004 — Datas MongoDB heterogêneas

O schema real contém 573.829 datas ISO e 8.930 epochs negativos em `$numberLong`. Ambos permanecem; `lfm_release_year` é derivado. Anos <1850 recebem flag, sem exclusão.

## D-005 — Gêneros Spotify

Os 82 gêneros têm contagens bastante variáveis; não foi observado balanceamento por contagem exatamente igual. Isso não comprova representatividade: a fonte informa extração via Spotipy, mas o mecanismo de seleção de faixas/gêneros não permite inferir uma amostra probabilística de todo o Spotify.

## D-006 — Sem modelos na Base v0.1

Não há treinamento, embeddings nem redes neurais. Na modelagem futura, splits devem ser agrupados por artista e composição para reduzir leakage entre versões relacionadas.

## D-007 — Base v0.1.1 e holdout agrupado

A Base v0.1.1 mantém as 111.758 observações aceitas, mas reduz a matriz de 310 para 228 colunas: três identificadores, três grupos operacionais, o rótulo do split, o alvo e 220 preditoras autorizadas. O split é determinístico (`random_state=42`), aproximadamente 75/25 e feito sobre componentes conexos de artista e composição. Assim, uma composição que ligue registros ou artistas permanece integralmente no mesmo subconjunto. Não houve sobreposição de `artist_group_id`, `composition_group_id` nem `split_group_id`.

As 12 preditoras constantes foram identificadas exclusivamente no desenvolvimento e removidas da matriz. As 42.517 linhas com ausências em descritores estruturais foram preservadas; não se imputou zero. `genius_lyrics_views`, `lfm_playcount`, chaves, nomes e artefatos de matching são proibidos como preditores. O holdout não deve ser usado para seleção de variáveis, PCA ou ajuste de hiperparâmetros.

## D-008 — Escopo da revisão de matching

O status aceito continua sendo a regra da Base v0.1; divergências temporais não são convertidas automaticamente em erro. A amostra manual contém 225 casos, reaproveita 222 registros do artefato existente e faz três reposições determinísticas para cobrir chave de composição ausente e flags raras de versão. Os cinco campos humanos são entregues em branco.
