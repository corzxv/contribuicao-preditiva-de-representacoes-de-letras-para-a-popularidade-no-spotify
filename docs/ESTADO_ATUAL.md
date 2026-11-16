# Estado atual — 16/11/2026

Leia este arquivo primeiro ao continuar em outro chat. Depois: `CONTEXTO_TCC.md`,
`PLANO_EXECUCAO.md`, `MAPA_ARTEFATOS.md` e `decisions.md`. Não recomeçar o TCC.

## Próxima ação vigente — revisão acadêmica (D-049)

O pesquisador confirmou a compilação da edição D-048 no Overleaf.
Os materiais atuais estão referenciados no README do repositório. O título
integral do TCC é usado no README e transliterado no endereço GitHub.
As próximas alterações acadêmicas seguem sob revisão com o orientador.

## Histórico — versão otimizada para Overleaf (D-048)

Novo ZIP em reports/monografia_template_overleaf.zip. PDF em
output/pdf/monografia_template_overleaf.pdf. Importar como novo projeto no
Overleaf com main.tex e XeLaTeX. PDF com 36 páginas, 21 figuras e 14 tabelas.
Revisão do GitHub em etapa posterior. O bootstrap 58 usa semente 42 em
previsões seladas, e os sorteios históricos mantêm suas sementes.

## Histórico — monografia revisada (D-047)

O ZIP está em reports/monografia_template_revisada.zip e o PDF em
output/pdf/monografia_template_revisada.pdf. Usar main.tex e XeLaTeX.
O corpo tem 31 páginas, com 21 figuras e 14 tabelas. Inclui as descrições
do Spotify e do LRCLIB, o cálculo amostral, o cruzamento, as representações
textuais e a avaliação das 9.526 faixas. O resumo segue os modelos do
pesquisador. A cobertura de 3.869 pertence ao sorteio original. A coorte
final vem do quadro de 80.943 vínculos e compartilha 461 faixas com o sorteio.
Próximo passo: revisão acadêmica com o orientador.

## Histórico — monografia D-046

O ZIP para Overleaf está em reports/monografia_template_final.zip. O PDF
está em output/pdf/monografia_template_final.pdf. Usar main.tex e XeLaTeX.
A versão consolida a descrição do catálogo, o sorteio probabilístico,
a cobertura do LRCLIB e a classificação ordinal das 9.526 faixas
selecionadas no quadro vinculado. A etapa de 200 mil é retomada em apêndice.
O próximo passo é a revisão acadêmica com Leandro Tavares Correia.

## Histórico — resultados da candidata v2 (D-045)

57 REAL concluído e conferido nas 9.526 faixas. A acurácia balanceada foi
56,14% no Baseline, 56,24% no Tradicional, 55,91% no Profundo e 55,96% no
Combinado. O Profundo teve o maior acerto na classe alta. Interpretação em
reports/classificacao_9526_v1/interpretacao_resultados.md.

## Histórico — executar a classificação da candidata v2 (D-044)

A candidata v2 de 9.526 faixas foi adotada para esta avaliação. O script 57
prepara 21 descritores, completa 482 embeddings e compara quatro blocos com
logística ordinal. As divisões comuns agrupam 6.271 componentes. A conferência
prévia encontrou suporte das três classes em todas as partes. Execução manual
pendente conforme docs/protocolo_classificacao_9526_v1.md.

## Histórico — definir o uso da candidata v2 (D-043)

55 foi concluído e conferido. Das 22.443 consultas, 179 trouxeram letras
aceitas. Quadro ampliado de 80.943 faixas. A candidata v2 tem 9.526 letras
verificadas e 82 gêneros, com os mesmos totais das cinco bandas de
popularidade do sorteio original. As cotas abaixo do alvo são `sleep` (23
de 147) e `indie-pop` (81 de 82). 9.033 faixas vieram da coorte histórica
de modelagem. Definir o domínio e a função dessa exposição com o pesquisador.
O diagnóstico complementar de `sleep` analisou 48 casos de metadados por
chave nativa exata e encontrou zero candidatas textuais nessa amostra.

## Histórico — recuperar letras nos gêneros deficitários (D-042)

53 revalidou 42 das 43 consultas históricas. 54 identificou 22.443 faixas
novas de `sleep`, `romance` e `detroit-techno` com artistas nos índices
existentes. 55 está preparado e precisa de execução manual com o SSD em D:.
Guia docs/recuperacao_generos_deficitarios_v1.md. A prioridade é medir a
capacidade para preencher as cotas originais desses três gêneros.

## Histórico — amostra completa com letras e cobertura (D-041)

O pesquisador exige 9.526 letras vinculadas e autorizou explorar outras faixas.
52 REAL leve sorteou uma candidata com 9.526 vínculos e textos conferidos,
a partir de 80.722 faixas com letras aceitas. Todas as faixas de popularidade
têm os mesmos totais do sorteio original. Os 82 gêneros estão presentes,
com quatro cotas inviáveis na capacidade conhecida e diferenças acústicas.
Resultados em reports/amostra_com_letras_candidata_v1. O uso definitivo e a
inferência dependem do domínio acordado. O sorteio original segue com 5.657
faixas sem letra aceita. A revisão de caches antigos encontrou 43 consultas
candidatas em três gêneros para revalidação, sem expansão automática.

## Histórico — definir o domínio da nova avaliação (D-040)

50 REAL concluído pelo pesquisador e conferido. Das 40 consultas por limite,
25 foram aceitas. As outras 15 ficaram pendentes no manifesto de vínculos,
com oito divergências entre textos, um conflito plain/LRC, três limites de
elegíveis, um sem compatível e duas indicações instrumentais registradas
separadamente no resumo de 50.

51 REAL leve consolidou todas as 9.526 faixas por referência às fontes. Total
3.869 aceitas (40,62%, ponderado 40,63%), 1.085 ambíguas, 4.155 sem candidato,
416 instrumentais de origem e uma sem texto. A cobertura é 29,99% na faixa 0–19
e 60,75% na faixa 40–59. Dois gêneros sem letra aceita. Os arquivos estão em
reports/recuperacao_consolidada_nova_amostra_v1. A avaliação anterior está
preservada e a escolha do novo domínio precisa de decisão do pesquisador.

## Histórico — revisar o teto de candidatos locais (D-039)

49 REAL concluído e conferido. Das 100 buscas HTTP 200, 93 vieram vazias, cinco
trouxeram candidatos incompatíveis, uma indicação instrumental e uma atingiu
o teto. Zero candidatas. Evidência em reports/piloto_online_nova_amostra_v1.
O mesmo protocolo online fica encerrado nesta rodada. Total de 3.844 aceitas.

50 preparado para as 40 consultas locais limitadas pelo volume. A inspeção de
sete casos mostrou seis com candidatos elegíveis após filtrar os metadados.
Execução manual pendente com SSD D:. Guia
docs/execucao_revisao_limites_nova_amostra_v1.md.

## Histórico — piloto online de recuperação (D-038)

49 preparado e testado. A seleção real de 100 entre as 4.155 pendências sem
candidato foi selada localmente, com 100 consultas distintas. Execução online
manual pendente. Basta a internet e o ambiente do projeto. O guia
docs/execucao_piloto_online_nova_amostra_v1.md traz comando e retomada.
O piloto mede candidatas provisórias e guarda evidências privadas.

## Histórico — avaliar recuperação das faixas sem candidato (D-037)

47 REAL concluído pelo pesquisador, com 58 novas aceitas de 108 conflitos
plain/LRC em 3,64 s. Restaram 29 conflitos internos e 21 divergências entre
candidatos. 48 REAL leve revisou os 13 casos de grafia com fontes de catálogo.
Nove novas aceitas e quatro casos inconclusivos por edição ou créditos.

Total verificado de 3.844 aceitas (40,35%, ponderado 40,37%), 1.110 ambíguas,
4.155 sem candidato pelos métodos usados, 416 instrumentais e uma sem texto.
Cobertura 29,76% na faixa de popularidade 0–19 e 60,53% na faixa 40–59.
Agregados em reports/cobertura_pos_revisao_variantes_nova_amostra_v1.
Fichas, fontes e complementos privados em data/derived/private_revisao_variantes_artista_nova_amostra_v1.
Próximo candidato de trabalho é um piloto limitado na fonte atual para medir
se há recuperação adicional nas pendências sem candidato, antes de expandir.

## Histórico — revisar conflitos plain/LRC (D-036)

46 REAL concluído pelo pesquisador e conferido. Das 831 consultas, 130 passaram
e 701 seguiram distintas. Total de 3.777 aceitas (39,65% do sorteio, 39,66%
ponderado), 1.168 ambíguas, 4.164 sem candidato, 416 instrumentais e uma sem
texto. Vínculos e textos conferidos por hash e chave, sem sobreposição com as
aceitas anteriores. Agregados em reports/cobertura_pos_revisao_caixa_nova_amostra_v1.

47 preparado/testado para as 108 ambiguidades plain/LRC. A amostra diagnóstica
de 12 consultas teve cinco com concordância de todos os candidatos elegíveis
após uniformizar caixa, espaços e tipografia. A execução completa é manual,
com SSD D:, pelo guia docs/execucao_revisao_caixa_plain_lrc_nova_amostra_v1.md.
As 13 variantes de artista continuam em fichas, para validação separada.

## Histórico — revisão de caixa em textos concorrentes (D-035)

44 REAL concluído pelo pesquisador e conferido: 4.164 diagnósticos, 137,64 s.
2.059 mesmo artista/outro título, 1.676 sem candidato pelos métodos, 410 mesmo
título/outro artista, 13 variações de artista e seis outros. 332 consultas
atingiram limites de registros. 45 REAL leve concluído pelo agente com 9.526
linhas de metadados projetadas, 12 variáveis e 82 gêneros. Cobertura seletiva:
popularidade média 24,156 e instrumentalidade 0,108 nas 3.647 aceitas, contra
18,383 e 0,252 no catálogo. Comparativos e figura em reports/consolidacao_dados_nova_amostra_v1.
Os 13 casos geraram 16 pares privados com validação pendente.

Pesquisador escolheu continuar a recuperação antes de modelar. Em doze exemplos
de textos concorrentes, cinco coincidiram após uniformizar caixa, espaços e a
tipografia vigente. 46_revisar_caixa_textos_concorrentes.py preparado e testado
com sete verificações sintéticas. Execução real manual pendente com SSD D:.
Alvo de 831 consultas. Saída incremental de letras originais e vínculos, baseada
nos índices e resultados selados de 43. Guia docs/execucao_revisao_caixa_nova_amostra_v1.md.
Após a execução, conferir ganho e continuar recuperação dirigida.

## Histórico — diagnóstico de chaves (D-034)

43 REAL concluído/conferido: 3.647 aceitas (38,28%; ponderado 38,30%), ganho de
2.222; 1.298 ambíguas/4.164 sem candidato/uma sem texto/416 instrumentais, zero
erro/pendência. Todas as 1.425 aceitas/362 instrumentais de 42 preservadas;
54 novas indicações instrumentais. Sem rebuild, tempo registrado 41,79 s.
Interpretação: reports/interpretacao_revisao_matching_nova_amostra_v2.md.

Remanescentes: 831 textos concorrentes diferentes sob a comparação atual,
153 versões sem elegível, 152 metadados, 108 plain/LRC, 40 limites, oito
instrumental/texto e seis formatos. Oito exemplos textuais limitados não se
igualaram apenas por whitespace; sem extrapolar prevalência/verdade semântica.

Índices nativos do dump conferidos por schema/EXPLAIN e doze consultas limitadas
de metadados: um exemplo &/and com título/duração próximos, sem aceitação nova.
44_diagnosticar_consultas_sem_candidato.py/native_lookup_audit.py preparados,
três testes sintéticos aprovados. **Execução real pendente manual**, SSD D:.
Diagnostica 4.164 por índices nativos/FTS, sem ler letras, criar índice ou mudar
aceitações. Candidatos/aliases não são vínculos validados. Guia:
docs/execucao_diagnostico_chaves_nova_amostra_v1.md. Não repetir 42/43 ou treinar.
Cobertura ainda seletiva; pesos do sorteio não corrigem seleção de letras.
Evidência: reports/verificacao_revisao_matching_e_preparacao_diagnostico_20261106.json.

## Histórico — correção dos bloqueios (D-033)

42 REAL concluído/conferido: 1.425 aceitas, 3.574 ambíguas, 4.164 sem candidato,
uma sem texto, 362 indicações instrumentais; zero erro/pendência, 1.422,90 s.
Instrumentais são indicação LRCLIB + ausência de texto compatível (87 herdadas,
275 novas), não a variável Spotify ou confirmação humana. Não ressortejar.

Auditoria leve após questionamento: 2.139 plain_synced_conflict; dez consultas
pontuais examinadas e todas coincidem ao uniformizar whitespace, sem mudar
palavras/pontuação. Amostra diagnóstica determinística, sem extrapolação.
1.176 positive_version_conflict, dos quais 1.023 têm candidato plenamente
compatível vetado pela presença de outra versão. Dois bloqueios reais da regra
reutilizada; agente reconheceu a falha. Não atribuir toda a perda à falta de letras.

43_revisar_bloqueios_vinculacao.py/lyrics_matching_revision.py preparados,
quatro testes sintéticos aprovados, **execução real pendente manual**. Reavalia
apenas 3.162 consultas nos índices prontos, sem rebuild/varredura. Igualdade
exata após whitespace/tipografia, texto original preservado; candidatos
incompatíveis não vetam os compatíveis. Conteúdo/versão errados continuam barrados.
42 e 1.425 aceitas/362 instrumentais permanecem preservados. Os 4.164 sem
candidato exigem diagnóstico separado; nenhuma recuperação adicional garantida.
Guia/protocolo docs/revisao_bloqueios_vinculacao_v2.md. Não repetir 42 ou treinar.
Evidência: reports/auditoria_bloqueios_matching_nova_amostra_v1.json; referências
dos casos examinados ficam privadas, sem corpos de letras.

## Histórico — preparação da busca local (D-032)

41 REAL concluído pelo pesquisador/conferido: 9.526 consultas em 30,32 s;
682 aceitas, 87 instrumentais, 8.757 pendentes, zero metadados insuficientes ou
erros. Hashes dos três Parquets/duas tabelas e código/fontes conferidos.
7,16% é reaproveitamento do cache, não cobertura final do LRCLIB. Amostra mantida.
Interpretação: reports/interpretacao_reaproveitamento_nova_amostra_v1.md.
Evidência: reports/verificacao_cache_e_preparacao_busca_nova_amostra_20261106.json.

42_buscar_letras_nova_amostra.py preparado/testado em quatro testes sintéticos;
**execução real pendente manual**. SSD conectado em D:. Reutiliza índice v2
selado (24.330 artistas/5.726.985 entradas); identifica artistas faltantes e
constrói somente complemento quando necessário, com uma passagem retomável de
metadados do dump. Não refaz índices antigos. As aceitas/instrumentais de 41 e
amostra inteira são preservadas; negativas controladas completas compatíveis
podem ser reutilizadas. Mesmas regras v2, sem aceitar só por chave normalizada.
Guia: docs/execucao_busca_nova_amostra_v1.md. Não repetir 39–41 ou executar a
busca/varredura real pelo agente. Próximo: conferir cobertura após saída de 42.

## Histórico — amostra real e reaproveitamento preparado (D-031)

40 REAL executado pelo pesquisador e conferido: 9.526 faixas, 82 gêneros,
fonte/plano/Parquet/agregados selados. Soma dos pesos 1.159.764 (arredondamento
numérico 2e-10). Todas as categorias somam n e N. Agente conferiu hashes/schema
e tabelas agregadas; não releu o cadastro nem linhas individuais da amostra.

Diferenças entre médias ponderadas: máximo absoluto 0,01901 DP (liveness).
Popularidade 18,3975 vs 18,3831; BPM 121,2241 vs 121,3771. Por período,
diferença máxima 0,4050 pp. Dispersões/quantis próximos, sem afirmar igualdade
de distribuições. Gêneros coincidem ponderados por construção. Manter sorteio.
Interpretação em reports/interpretacao_nova_amostra_catalogo_v1.md; duas figuras
comparativas PNG/SVG conferidas visualmente na pasta do sorteio.
Evidências: reports/verificacao_sorteio_nova_amostra_20261106.json, com 128
células categóricas reconciliadas e registros dos testes/preparação de 41.

Próximo: execução **manual** do script 41_reaproveitar_letras_nova_amostra.py.
Preparado/testado em seis verificações sintéticas; não executado no cache real.
Consultas exatas por chave nos estados v2/v1; texto/vínculo conferidos, campos
e pesos preservados. Sem SSD/rede/índice novo; negativa no cache é pendência,
não ausência de letra. Guia execucao_reaproveitamento_nova_amostra_v1.md.
Depois: avaliar quantas decisões foram reutilizadas e preparar busca das
pendências. Não repetir 39/40, buscar em massa ou treinar automaticamente.

## Histórico — preservação e dimensionamento da amostra menor (D-030)

Preservação solicitada pelo pesquisador concluída: pacote local de 430 arquivos,
16.872.772 bytes, em reports/preservacao_monografia_20261106/. Inclui PDFs,
fontes acadêmicas e resultados agregados das versões históricas e descrição 39.
Todos os membros do ZIP conferidos por SHA-256/CRC; originais mantidos. Não é
backup externo, publicação Git ou cópia de bases/letras/modelos.

Dimensionamento concluído pelo agente somente em agregados: N=1.159.764,
n=9.526, AAS sem reposição nos 82 gêneros, alocação proporcional por maiores
restos, 5–179 faixas por gênero, semente 20261106. Metas escolhidas: margem
individual aproximada de 1 pp/95% para proporção global e margens de até
0,05 DP/95% conjunto para doze médias (Bonferroni). Não assegura recuperação
de letras, equivalência de distribuições ou precisão preditiva/por gênero raro.

Script 40_preparar_nova_amostra.py e sample_redesign.py preparados; quatro
testes sintéticos e lint aprovados. Plano/alocação/precisão/cenários reais em
reports/nova_amostra_catalogo_v1. **Sorteio real ainda não executado.** Comando
único manual no guia docs/execucao_nova_amostra_catalogo_v1.md; protocolo em
docs/plano_nova_amostra_catalogo_v1.md. Não repetir dimensionar/39.
Evidência: reports/verificacao_nova_amostra_20261106.json; soma planejada dos
pesos 1.159.764, n efetivo de Kish 9.525,93. Sem sorteio/linhas reais pelo agente.

Após a execução manual: conferir resumo/comparativos da única amostra e
organizar recuperação das letras selecionadas, reutilizando evidência compatível.
Não executar busca, novo treino ou substituição de perdas automaticamente.

## Histórico — descrição concluída antes do dimensionamento (D-029)

Pesquisador determinou nova sequência: descrição completa da população acessível
de 1.159.764 faixas → dimensionamento estatístico de amostra menor → recuperação
das letras → modelagem posterior a definir. A descrição ocupa a parte inicial
da monografia; não seu centro. Preservar todo o trabalho anterior.

39 REAL concluído pelo pesquisador e conferido: 1.159.764 faixas, vinte campos,
82 gêneros, 44 arquivos agregados/figuras, tempo registrado 32,71 s. Agente leu
somente esses agregados/figuras; não repetiu o processamento individual.
Médias reconciliadas com auditoria anterior; frequências, histogramas e 36 eta²
conferidos. Treze figuras reais revisadas. Saída: reports/descritiva_catalogo_completo_v1.

Gênero apresenta eta² de 45,99% para energia, 51,76% para caráter acústico e
8,50% para BPM: candidato à estratificação, sem bastar para equilibrar tudo.
PCA: 1.158.565 casos completos (1.199 tempos zero fora apenas desta análise);
CP1/CP1–2/CP1–3 retêm 29,12/44,35/57,85%, oito componentes 95,66%. Não são clusters.
Log1p da popularidade inverte assimetria de +0,8100 a -0,7947, sem forte ganho
de simetria; 13,66% de zeros preservados. Interpretação:
reports/interpretacao_descritiva_catalogo_completo_v1.md; evidência:
reports/verificacao_descritiva_catalogo_20261106.json. Fontes/artefatos preservados.

Próximo: pesquisar/definir dimensionamento e alocação de amostra menor com
referências e metas explícitas para várias características. Começar estudando
estratificação por gênero e compromisso entre metadados. Nenhum tamanho ou
desenho novo adotado ainda, letra buscada ou modelo preditivo treinado. Não
repetir 39, voltar à revisão automática de v3 ou à modelagem dos 200 mil.

## Histórico — monografia versão 3 (D-028)

Autorização do pesquisador em 06/11: gerar nova versão acadêmica. Concluída:
reports/monografia_template_200k_v3/main.tex, ZIP correspondente e
output/pdf/monografia_template_200k_v3.pdf (45 páginas). Objetivos integrados à
introdução; regressão preservada, extensão ordinal/PCA e sensibilidade posterior
separadas. Catorze tabelas, sete figuras, 34 equações e 32 referências originais.
PDF compilado e revisado visualmente; ZIP extraído e recompilado sem referências
indefinidas ou estouro de caixas. Sete testes leves e lint do script 38 aprovados.
Nenhum dado individual lido, modelo ajustado ou trabalho pesado executado para
esta entrega. Versão 2/PDF/ZIP, fontes científicas e resultados anteriores
conferidos por hash. Guia execucao_monografia_template_200k_v3.md; evidências em
reports/verificacao_monografia_template_200k_v3.json.

Próximo: leitura com Leandro Tavares Correia e discussão da utilidade dos erros,
sem escolher a alternativa como principal ou repetir treinamentos automaticamente.
Não houve commit/push nesta consolidação editorial.

## Histórico — consolidação científica após D-027

36 REAL concluído pelo pesquisador e conferido: métricas principais reproduzidas,
77.535 faixas/21.893 componentes, sem ajuste ou mudança de probabilidades.
Combinado: BA 60,58→64,43%, acurácia 65,82→63,09%, sensibilidade elevada
40,75→71,52%, precisão elevada 72,38→51,75%. Alternativa tem compromisso, não
ganho universal; manter principal e sensibilidade separados, sem escolha retrospectiva.
Incremento textual alternativo +1,16 ponto sobre Baseline e +0,13 sobre Profundo.

37 executado pelo agente só em agregados e cauda delimitada de 128 faixas/96
componentes; 120 métricas reconciliadas com 1.080 células e duas figuras verificadas.
Na cauda ≥80, Combinado declara nível ≥40 em 119/128 principal e 125/128 alternativa;
não é detecção binária de hits. Relatório interpretacao_sensibilidade_decisao_ordinal_v1.md;
verificação verificacao_sensibilidade_ordinal_20261106.json. Nenhuma execução
pesada pendente necessária agora. Próximo: integrar resultados e objetivos à
introdução em nova versão acadêmica, preservando PDFs/resultados atuais e discutir
custos/limites com orientador. Não iniciar novo treino ou cruzamento automaticamente.

## Histórico imediato — produção e preparo da sensibilidade

34 integral REAL concluído pelo pesquisador e conferido: 20 partes ordinais,
cinco referências, 480 ajustes internos, 77.535 probabilidades por variante,
zero pendências; máximo 311 iterações e zero avisos registrados. Fontes/partes/
footers/hashes conferidos sem refit ou leitura integral da coorte pelo agente.

Acurácia balanceada: Baseline 59,19%, Tradicional 59,69%, Profundo 60,45%, Combinado
60,58%. Combinado: acurácia 65,82%, sensibilidade elevada 40,75%, precisão elevada
72,38%; incremento +1,39 ponto sobre Baseline e +0,13 sobre Profundo. PCA escolhida
em 3/20 partes, nove de onze componentes numéricos, sem ganho consistente.
Lambda 0,001 (menor da grade) escolhido em 20/20 partes; documentar limite sem
expandir grade após observar resultados. Sem significância ou inferência de catálogo.

35 concluído pelo agente somente com agregados e parâmetros de três modelos PCA;
três figuras PNG/SVG verificadas visualmente. Relatório interpretacao_classificacao_ordinal_200k_v1.md;
agregados em diagnosticos_classificacao_ordinal_200k_v1. 36 preparado/testado:
reproduziu métricas e comparou argmax com regra fixa p/pi usando proporções dos
treinos externos. Execução manual já concluída acima, sem treino,
recalibração ou substituição do resultado principal. Análise exploratória posterior.
Guia: execucao_sensibilidade_decisao_ordinal_v1.md. 58 testes/lint aprovados;
registro em reports/verificacao_producao_ordinal_20261105.json.

## Histórico do primeiro lote ordinal (D-026)

Primeiro lote real concluído pelo pesquisador: Combinado/externo 0, 24 ajustes
internos e reajuste externo, treino 62.028/avaliação 15.507. Tempo registrado
105,42 s, sem avisos registrados. Selos/hashes/checkpoints conferidos, sem refit.
1/20 partes concluídas, 19 pendentes; métricas globais ainda indisponíveis.
Pesquisador deseja deixar a execução integral rodando; próximo comando é
34_classificar_niveis_popularidade.py all, sem limite. Retomada já concluída acima.
Registro: reports/verificacao_primeiro_lote_ordinal_20261105.json.

32 v1.1 concluído pelo pesquisador: 133 fichas, 130 com evidência em cache, 22
listas truncadas. Triagem técnica 33 executada pelo agente sobre essas fichas:
dos quarenta casos aceitos, 35 com metadados selecionados compatíveis e cinco
sem candidato selecionado disponível. Sem inferência de precisão semântica,
sem alteração de vínculos ou nova busca. Outputs em triagem_piloto_vinculacao_200k_v1.

34 preparado/testado: logística ordinal regularizada, quatro blocos, folds
existentes, PCA das numéricas como opção interna. Smoke REAL concluído pelo
pesquisador: 318 faixas, quatro partes, 96 ajustes internos, recarga com diferença
máxima 0,0, gate verified=true. Selos/partes conferidos sem refit pelo agente.
Nenhuma métrica científica global no smoke. A produção foi concluída depois,
conforme D-027 acima; não repetir esses comandos.
53 testes
selecionados e lint passaram. Guia execucao_classificacao_ordinal_200k_v1.md;
relatório reports/preparacao_classificacao_ordinal_20261105.md e verificação JSON
de mesmo prefixo verificacao_classificacao_ordinal_20261105.json. Conferência do
smoke: reports/verificacao_smoke_ordinal_20261105.json.

## Histórico imediato — níveis e piloto de vinculação (D-025)

Pesquisador autorizou execução autônoma do plano discutido com o orientador,
preservando a regressão anterior e a regra manual. Nova etapa exploratória no
domínio das 77.535 faixas: principal 0–19/20–39/40–100; sensibilidade 0–39/40–59/60–100.
Não são definições oficiais de hit. Acurácia balanceada é o critério primário
planejado para classificação; PCA apenas dentro dos treinos, depois do diagnóstico.

31 agregados executado pelo agente somente sobre 2.009 linhas públicas:
classes aceitas 34.069 / 30.785 / 12.681. Fontes seladas e PDFs anteriores
conferidos, sem alterações. 31 previsoes executado pelo pesquisador e conferido:
completed=true, 77.535 faixas/21.893 componentes, suporte aprovado em todas as
partições, mínimos 2.381 faixas/1.322 componentes por classe. Acurácia balanceada
das previsões antigas categorizadas: Baseline 58,32%, Combinado 60,42%; não é
resultado de um classificador novo. Nenhum ajuste novo realizado.

32 foi interrompido antes da seleção: popularity bruto é texto. Versão corrigida
v1.1 cria review_popularity_numeric, ordena/compara como número e preserva o bruto.
Saídas novas private_linkage_review_200k_v1_1/piloto_vinculacao_200k_v1_1; registros
parciais v1 preservados. 28 testes selecionados passaram; execução real v1.1
posteriormente concluída, conforme seção D-026 acima. Evidências da correção em
reports/diagnostico_niveis_e_correcao_piloto_20261105.md e
reports/verificacao_correcao_piloto_20261105.json.
Guia: docs/execucao_nova_etapa_niveis_v1.md. Analisar fichas antes de preparar
treino ordinal. Caches locais
v1/v2 disponíveis, abertura somente leitura/busca por chave conferidas sem ler
registros. Nenhum dump/SSD/rede consultado ou novo vínculo incorporado.

34 páginas/ZIP/monografia v2 e todos os resultados da primeira regressão mantidos.
As indicações abaixo de modelagem congelada se referem à primeira etapa, não
impedem a nova investigação explicitamente autorizada em 04/11. A revisão de
introdução/objetivos será integrada em nova versão acadêmica, preservando a atual.

## Organização do Git e publicação — D-024

Publicação concluída em corzxv/tcc-popularidade-musical, master, privado.
Commit principal 082a9a0 confirmado no remoto; 564 arquivos versionados.
394 testes locais e lint aprovados. CI do commit 9b375a8 aprovada após incluir
Polars no ambiente das fixtures, sem mudar código científico. Quinze selos e
154 artefatos anteriores preservados. Oito prévias/roteiros antigos retirados
apenas do índice; originais locais e histórico mantidos. Evidências em
reports/publicacao_github_20261102.json. Naquela publicação, a entrada era a versão 2;
a versão 3 editorial de D-028 ainda não foi publicada.

## Entrada acadêmica anterior — template fornecido (D-023, 02/11)

Usar reports/monografia_template_200k_v2/main.tex e ZIP de mesmo nome.
PDF em output/pdf/monografia_template_200k_v2.pdf: 34 páginas, cinco seções,
dois apêndices científicos, dez tabelas, cinco figuras, 27 fontes originais.
Formato baseado no template/Ana e três TCCs de Estatística da BDM. Orientador
**Leandro Tavares Correia**, grafia corrigida e confirmada pelo pesquisador.

Descrição Spotify/LRCLIB, fórmulas e percurso amostragem → integração → domínio
observado reescritos. Inventário/hashes/pendências administrativas fora do PDF,
preservados no repositório. Fontes originais citadas diretamente; não os TCCs que
ajudaram a localizá-las. Versão de 57 páginas abaixo é histórica e intacta.
Overleaf: main.tex/XeLaTeX/BibTeX. Relatório: revisao_template_monografia_200k_v2.md;
guia: execucao_monografia_template_200k_v2.md. Compilação/34 páginas verificadas,
dez testes/lint passaram. Modelagem/resultados congelados; sem tarefa pesada.

## Confirmado na consolidação anterior (histórico preservado)

### Modelagem encerrada e monografia única — 02/11/2026 (D-022)

O pesquisador determinou congelar a avaliação principal e concentrar o trabalho
na monografia completa. Não iniciar novos treinos, buscas LRCLIB ou embeddings
massivos. Baseline 8,3525 / Tradicional 8,2957 / Profundo 8,1285 / Combinado
8,1151 preservados; ganho conjunto 2,84%, pequeno incremento frente ao Profundo
inconclusivo na análise auxiliar. Folds, modelos, previsões e regras não mudaram.

Nova entrada única: reports/monografia_consolidada_200k_v1/main.tex. ZIP de mesmo
nome; PDF efetivamente compilado do TeX em output/pdf/monografia_consolidada_200k_v1.pdf.
57 páginas, 11 capítulos, quatro apêndices, 14 tabelas, oito figuras, 19 referências.
Orientador confirmado: Leandro Tavares Correa. Título escolhido com autorização
do pesquisador. Não é template institucional homologado nem versão aprovada para
depósito: pendências específicas no Apêndice D e no relatório de consolidação.

195 materiais acadêmicos inventariados, 135 textos lidos; dois pacotes anteriores
preservados e universos históricos separados. Compilação Tectonic/BibTeX e editor
integrado verificadas; 57 páginas inspecionadas, com remoção de URL órfã na
bibliografia. Dez testes leves passaram; lint/format/diff conferidos. Script 28
produz somente tabelas/figuras de agregados públicos, sem bases individuais.
Relatório: reports/relatorio_consolidacao_monografia_200k_v1.md; guia
execucao_monografia_consolidada_200k_v1.md. Nenhum trabalho pesado necessário.

### Fechamento metodológico após o PDF — 02/11/2026

Solicitação atual concluída em diagnósticos leves 25/26/27, sem treino/buscas ou
embeddings do corpus. Parecer completo: reports/parecer_fechamento_metodologico_200k_v1.md;
agregados em reports/fechamento_metodologico_200k_v1/. PDF/ZIP atuais preservados
por SHA-256; códigos/protocolos 19–23 e todos os resultados principais mantidos.

- **Achado real:** tokenizar `query: ` separado adiciona um token de espaço (ID 6).
  Apareceu em 11 frases artificiais e oito textos; quatro frases artificiais
  codificadas nas duas receitas confirmaram vetores diferentes (cosseno 0,99664–
  0,99943). Não mede impacto no MAE. Corrigir a descrição da variante atual;
  correção de implementação exige futura versão, sem editar o selo 20 ou disparar
  regeneração. Não alegar conformidade exata à receita oficial.
- Oito textos × 21 descritores reproduzidos com diferença máxima 0,0; código,
  contrato e normalização selados conferidos. Tokenização/janelas até 512 e pooling
  mascarado/L2 verificados em amostras/fixtures. Auditoria integral anterior de
  vetores (21) é evidência distinta, não repetida aqui. Pesos do encoder tiveram
  hash novamente conferido somente no diagnóstico sintético motivado pelo desvio.
- Limites auxiliares condicionais por componente/fold, combinados com Bonferroni
  sem supor folds independentes: Combinado−Baseline −0,23736 [−0,31400; −0,16073];
  Combinado−Profundo −0,01340 [−0,03027; +0,00347]. 95% nominais sob modelo auxiliar
  de grupos; NÃO IC integral de CV/treinamento ou inferência probabilística de
  catálogo. Não declarar significância da pipeline. Sensibilidade ponderada concorda.
- Cauda 80–100: 128 faixas/96 componentes, y real 80–96, todas subestimadas;
  média y=81,8125/previsão=52,4414, mediana residual −28,7755. 0,1651% das faixas
  produzem 0,5975% do erro absoluto total e 0,04849 ponto do MAE global.
- Clipping separado mantém ordenação; MAE Combinado 8,11512→8,09701. Não altera
  a cauda. 615 negativos são principalmente valores baixos de y; extrapolação
  de suporte do Ridge, sem evidência de corrupção. Não substituir métrica principal.
- 17 testes específicos passaram; lint/formato/diff verificados. Nenhum treino
  real. Scripts 25/26/27 já executados em escopo leve; não são tarefas pesadas a
  mandar repetir ao pesquisador. D-021 documenta classificação/limites.

- Git inspecionado antes de editar; alterações pessoais preservadas. Organização
  lógica; nenhum movimento/exclusão ou commit/push.
- Catálogo e amostra têm resumos concluídos; amostra/footer 200.000. Não foram
  reprocessados aqui. Pesos, estratos e registros devem permanecer.
- V2 recente concluída: 77.535 aceitas em 200.000 linhas; textos privados com
  mesmo número de consultas. É a fonte textual principal do domínio congelado, sem filtro novo.
- Script 17 executado pelo pesquisador: completed=true, 77.535 vínculos/hashes
  auditados, 18,79 s. Não carregou modelos, alvos históricos ou SSD. 484 registros
  excedentes compartilham texto estrito e 16 textos ligam artistas diferentes.
- Linhagem: 421 IDs do teste v0.6, 438 colisões de composição e 7.162 de artista;
  13.558 IDs com vínculo LFM2b antigo, 63.977 sem vínculo. Flags sobrepostas.
  As quatro chaves antigas não resolvidas são do artista `!!!`: manter literalmente.
- Script 19 executado pelo pesquisador: completed=true, 361,67 s; 77.535 faixas
  preservadas, 77.051 inputs normalizados únicos, 21 descritores finitos. 484
  reusos, 21.893 componentes, maior 186; zero chaves não resolvidas e zero textos
  sem segmentos lexicais. A flag correspondente é constante zero; tratar no treino.
- Componentes com história v0.6: 358 por ID avaliado, 367 por composição e 1.141
  por artista; essas contagens se sobrepõem, não confundir com números de faixas.
- Script 20: download e smoke reais executados pelo pesquisador. Resumo do smoke
  completed=true, 24 vetores de dimensão 384, 68 janelas, 55,26 s, repetição do
  controle com diferença máxima 0,0. Maior entrada ao modelo: 512 tokens. Metadados
  dos 24 vetores confirmam cobertura integral, inclusive texto de 9.193 tokens de
  conteúdo. Avisos do tokenizer não interromperam o teste. Integral agora concluída.
- Primeiro lote all --limit-texts 1000 executado pelo pesquisador: 1.000 novos
  vetores e 24 reutilizados em 296,25 s; 1.024 salvos e 76.027 pendentes. Exportação
  parcial: 1.055 referências de faixas, dimensão 384, 1.246 janelas acumuladas,
  entradas até 512 tokens. completed=false por limite planejado, sem erro registrado.
  Contagem do SQLite, smoke_verified=true e hashes do código/protocolo conferidos.
- Script 20 integral concluído pelo pesquisador após pausa/retomada: completed=true,
  77.051 vetores e índice com 77.535 faixas, zero pendências; 91.156 janelas até
  512 tokens. Última execução: 27.352 novos + 49.699 reutilizados, 4.914,39 s.
  SQLite confirma 77.051 vetores, smoke_verified=true e selos/código preservados.
  Footers confirmam contagens e Float32[384]; inspeção limitada de 8 vetores e
  8 vínculos passou. Não foi repetida a varredura integral pelo agente.
- Ponderação aprovada pelo pesquisador (D-017): pesos iguais por faixa no ajuste
  e nas métricas principais, MAE primário/seleção; RMSE e R² complementares.
  Sensibilidade com MAE ponderado pelos pesos originais, mesmas faixas/folds/
  previsões externas e sem retreinar ponderado. Não corrige seleção textual.
- CV agrupada aninhada 5×3 aprovada pelo pesquisador nesta conversa, em 01/11.
  Folds reais agora gerados no script 21; quatro blocos têm os mesmos componentes/divisões e
  exposição histórica declarada. D-015 registra o desenho.
- Script 21 concluído pelo pesquisador em 8,323 s: 77.535 faixas, 77.051 vetores
  integralmente auditados (dimensão/finitude/hash/L2), 21.893 componentes, maior
  186; zero metadados ausentes/inválidos nos 15 campos Baseline. Cinco testes
  externos de 15.507, treinos de 62.028; internos de avaliação 20.676 e treino
  41.352. Separação/alinhamento aprovados; pesos/estratos/originais preservados.
  Footers e agregados conferidos pelo agente, sem repetir processamento integral.
- Script 22 smoke executado pelo pesquisador: completed=true, 318 faixas,
  72 ajustes internos + quatro partes Ridge + duas referências, 1,843 s.
  Treino externo do smoke 251/avaliação 67; repetição após recarga com diferença
  máxima 0,0, zero avisos internos, máximo 109 iterações. Gate verified=true,
  assinatura 34e5e6e0b46462ec2bafe4aa9e05769c254c1bf00792debdc07170e3ee3682b9.
  Hashes dos seis modelos/previsões e código/protocolo conferidos por metadados.
  Não é desempenho científico; global_metrics_available=false. Produção iniciada abaixo.
- Script 22 primeiro lote de produção concluído: Combinado externo 0, 18 ajustes
  internos e refit, duas referências, 67,775 s; 1/20 partes Ridge, 19 pendentes.
  Treino externo 62.028/avaliação 15.507; três arquivos de previsão com 15.507
  linhas cada. Máximo interno 352 iterações, zero avisos, hashes das partes e
  código/protocolo inalterados. completed=false por limite, sem erro registrado.
  Métricas globais ainda não disponíveis; não comparar blocos sobre partes diferentes.
- Script 22 integral concluído pelo pesquisador: 20/20 partes Ridge, dez
  referências, zero pendências, 77.535 previsões por variante e cinco contrastes.
  Última retomada 651,372 s (19 novas/uma reutilizada), não tempo total acumulado.
  360 ajustes internos, máximo 352 iterações, zero avisos; 30 pares de arquivos
  modelos/previsões e hash do arquivo global conferidos pelo agente sem refit ou
  desserialização. Código/protocolo e assinatura anteriores preservados.
- Métricas externas globais: MAE Baseline 8,352484; Tradicional 8,295691;
  Profundo 8,128523; Combinado 8,115122. Combinado−Baseline = −0,237363
  (redução 2,842%); Combinado−Profundo = −0,013402. MAE ponderado original:
  8,219436 / 8,165233 / 8,003171 / 7,990828; mesma ordenação, redução conjunta
  relativa 2,781%. Resultados descritivos sob Ridge, sem IC/significância.
  Relatório interpretativo em reports/interpretacao_modelagem_200k_v1.md.
- Script 23 executado pelo pesquisador: completed=true em 0,608 s, 77.535 faixas,
  30 partes/métricas/contrastes reproduzidos, 21.893 componentes, sem treino/IC.
  116 células publicadas, 77 com métricas omitidas por limiares. Código/protocolo
  e hash da tabela privada de perdas por componente conferidos, sem repetir análise.
- Combinado melhora Baseline nos cinco folds (delta -0,2724 a -0,2070); cinco
  contrastes mantêm sinal negativo na retirada de qualquer componente da avaliação,
  com previsões/modelos fixos. Isso não é IC. MAE Combinado na faixa 80-100:
  29,3711 (n=128); no idioma incerto piora 0,4204 (n=180), sem exclusão.
- Material de escrita 24 gerado pelo agente somente com 696 linhas de agregados
  públicos: trecho parcial de métodos/resultados/discussão, seis tabelas, quatro
  figuras PNG 300 dpi/SVG e referências. Novo projeto/ZIP
  reports/overleaf_dominio_observado_200k_v1, separado do pacote histórico.
  main.tex compilado com sucesso no editor integrado. PDF de leitura ReportLab
  em output/pdf/resultados_dominio_observado_200k_v1.pdf: sete páginas renderizadas
  e inspecionadas, sem página órfã ou sobreposições. Não é exportação do TeX.
- Parecer v2 concluído: incompatível com margens do catálogo; 72 diferenças
  simultâneas apoiadas. O pesquisador aprovou estudar o domínio analítico observado,
  sem presunção de representatividade. Decisão D-014 contém suas cinco condições.
- V3 diagnóstico concluído em ~181 s: 1.000 casos, 31 novas decisões aceitas por
  classificador, zero por busca ampliada, duas aceitações antigas inconclusivas.
  Não houve aplicação integral; não somar 31 às 77.535. Não executar script 15 apply
  como continuação automática. Arestas de normalização e revisão humana continuam
  registradas, sem obrigação de nova busca em massa.
- Experimentos anteriores existem e foram executados em outros universos. Footer
  v0.5: 7.648 desenvolvimento/2.592 teste. v0.6 avaliou quatro blocos em teste
  aberto em 14/10/2026. Coorte antiga ampliada: 58.633 e 50 modelos verificados
  (somente Baseline/Tradicional). Não misturar suas métricas com a coorte recente.
- Overleaf existente é parcial e referente à coorte antiga, não monografia final.

## Entregas desta rodada

Contexto, mapa, plano, registro D-014 e regras permanentes atualizados. README
agora aponta para o caminho atual e identifica comandos históricos. Inventário
individual: `reports/inventario_projeto_20261101.json` (somente metadados).

Verificação executada nesta rodada: 10 testes aprovados (`test_project_consolidation.py`
e `test_normalization.py`), incluindo checkpoint/retomada, vínculos e hashes de
textos/IDs LRCLIB, preservação de entradas e lineage sem alvos. Ruff check e format
nos dois módulos novos, dois scripts e teste de consolidação aprovados. Inventário
leve executado; help do script 17 conferido. Essas verificações foram da preparação;
a execução real posterior do script 17 foi do pesquisador, não do agente.

Script 17 preparado para auditoria de pré-fechamento: valida vínculos/hashes,
idioma estimado, duplicação textual e relação com dados/partições/teste antigos,
sem carregar alvos históricos, treinar, gerar representações ou consultar SSD.
Reutiliza validação da amostra, fingerprints e normalização. Execução real agora
**concluída**, conforme `reports/prontidao_dados_200k_v1/resumo_prontidao.json`.
Contrato `contrato_representacoes_200k_v1.md` e script 19 preparados: 21 descritores
operacionais lexicais/estruturais, texto comum para o futuro encoder e componentes,
sem filtro de idioma. Geração real desta etapa agora **concluída**, conforme
`reports/descritores_textuais_200k_v1/resumo_descritores.json`. Encoder congelado
em D-016/protocolo novo; download e teste real agora **concluídos**, conforme
`reports/embeddings_multilingues_200k_v1/smoke/resumo_embeddings.json`.

Verificação da nova etapa: 14 testes aprovados (descritores, consolidação e
normalização), lint/formatação dos arquivos alterados aprovados. Cobertura de
descritores Unicode/normalização/repetição,
componentes transitivos/literais, checkpoint/retomada, join 1:1 e preservação de
fontes em fixtures. Aprovação de CV 5×3 é do desenho, não execução de treinamento.

## Orientação de revisão — atualizada por D-028

Revisar reports/monografia_template_200k_v3/main.tex com Leandro Tavares Correia;
usar o ZIP v2 no Overleaf. A modelagem permanece congelada.

O registro a seguir descreve o fechamento anterior, preservado como histórico.
Revisar academicamente a monografia única já produzida, junto ao orientador.
O novo main.tex resolve a pendência de entrada principal; os dois trechos antigos
continuam preservados. O parecer de fechamento foi integrado, inclusive desvio
do prefixo, limites condicionais, cauda e clipping separado. Confirmar dados
documentais/institucionais do Apêndice D sem inventar datas ou taxa de matching.
Guia atual: execucao_monografia_consolidada_200k_v1.md. Não reabrir a modelagem
automaticamente para revisar texto. Nenhum processamento pesado está pendente.

Não há processamento pesado imediato necessário para a comparação Ridge atual.
Etapas 17/19/20/21/22/23 concluídas; não repetir. Script 24 só agrega fontes públicas
pequenas e pode ser reproduzido sem tocar dados/modelos. Revisão humana de matching,
redação/inferência/adequação ao template continuam distintas da conclusão técnica.

Sensibilidade concluída de retirada de um componente mantém modelos e previsões fixos:
diagnóstico de influência da avaliação, não validação leave-one-group-out com
refit ou IC. Protocolo 23 preparado depois de ler as métricas globais, antes dos
erros por subgrupo; é análise exploratória. Não declarar significância por esses extremos.
Agora há limites auxiliares adicionais (25), distintos dessa faixa de remoção;
a incerteza integral continua não estimada, sem necessidade de novos treinos para
encerrar a avaliação exploratória documentada.

Privados da etapa 21 concluída: coorte_modelagem.parquet, folds_5x3.parquet, blocos.json e
metadados_invalidos.parquet em private_modeling_200k_v1. Não duplica quatro
matrizes ou o armazenamento de vetores. Públicos: resumo/relatório, contagens de
folds e qualidade de metadados em reports/base_modelagem_200k_v1. Fontes/selos
anteriores intactos. Protocolo novo separado; método para monografia em
metodologia_modelagem_200k_v1.md. Qualidade semântica do matching e ganho preditivo
continuam por avaliar. Folds/modelos integrais concluídos. Saídas smoke/integral em
private_regression_200k_v1 e reports/modelagem_200k_v1. Saídas 23 concluídas em
private_results_diagnostics_200k_v1 (perdas por componente) e
reports/diagnosticos_modelagem_200k_v1 (agregados). Material 24 usa apenas agregados.
Checkpoints por ajuste interno/parte externa, caches separados por modo. Código
e protocolo 22 selados: não alterar para atualização de status ou otimização.
Protocolo novo em protocolo_regressao_200k_v1.md (D-018), separado dos selos 19–21.

Verificação desta preparação: 23 testes aprovados (7 novos da base/folds, 8 do
encoder sintético, 4 de descritores e 4 de consolidação), Ruff check/format e
git diff --check aprovados. Help do script 21 conferido. Nenhum processamento
integral real ou treino executado pelo agente.

Verificação da etapa 22: 29 testes aprovados (6 novos de regressão e os 23
anteriores), incluindo treino sem pesos, métricas pareadas, pré-processamento
restrito ao treino, alteração do alvo externo sem efeito em alpha/previsões,
gate técnico, limite/retomada, reuso sem novos fits e bloqueio de modelo corrompido.
Ruff check/format, diff --check e help de 22 aprovados. Treinos somente em
fixtures sintéticas de 40 observações; nenhum treino real pelo agente.

Verificação da preparação 23: dez testes aprovados (4 novos de resultados e 6
de regressão), Ruff check/format, diff --check e help. Cobrem reprodução de
métricas/partes, preservação de pesos/fontes, ausência de fit/desserialização,
influência de componentes com comparação direta, células pequenas e histórico
desconhecido. Diagnósticos reais executados pelo pesquisador; código/protocolos
anteriores permanecem intactos.

## Pendências para fechar dados

1. Revisar o main.tex consolidado e seus capítulos/figuras; etapas científicas
   encerradas por decisão do pesquisador. Preservar todos os resultados originais.
2. Revisão humana dirigida dos pares já existentes, com limites declarados; não
   inventar taxa de precisão. Inspeção de dois controles v3 não valida todo corpus.
3. Compatibilidade dos descritores LFM2b é desconhecida para a nova coorte; medir
   interseção por ID não comprova mesma letra/versão. Os descritores do próprio
   texto já concluídos evitaram impor aquela integração como elegibilidade.
4. Manter todos os idiomas: 56.908 inglesas, 20.447 não inglesas e 180 incertas
   estimadas. Adequação semântica não é certificada pela auditoria; contribuição
   preditiva já avaliada no procedimento congelado. Vetores antigos não foram importados.
5. Preservar componentes/divisões auditados e a exposição histórica declarada.
   CV 5×3 e ponderação D-017 aprovadas; runner 22 e diagnósticos concluídos.
   Próxima etapa é revisão acadêmica da versão consolidada. Não criar teste
   alegadamente intocado. Não tratar erros/folds como réplicas independentes.

Não fazer novas buscas, recalibrar pesos, substituir faixas, reorganizar dados
fisicamente ou abrir/retunar modelos para preencher essas pendências.
