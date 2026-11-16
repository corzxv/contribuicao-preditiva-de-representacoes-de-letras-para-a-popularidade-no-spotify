# Regras duráveis do projeto

## Próxima ação vigente — revisão acadêmica (D-049)

- Repositório do TCC em `corzxv/contribuicao-preditiva-de-representacoes-de-letras-para-a-popularidade-no-spotify`, ramo `master`, privado.
- O README aponta para o PDF, o ZIP e o código da edição mais recente.
  Preservar materiais científicos, usar português em novos commits e
  comentários e auditar o índice com o script 30 antes de publicar.

## Histórico — edição otimizada para Overleaf (D-048)

- Versão atual: reports/monografia_template_overleaf.zip e
  output/pdf/monografia_template_overleaf.pdf. Usar main.tex com XeLaTeX.
  O ZIP extraído compila localmente em cerca de 5,4 segundos. A confirmação
  no servidor Overleaf depende da importação pelo pesquisador.
- A semente padrão de novas execuções estocásticas é 42. O bootstrap editorial
  58 foi refeito com 42 sobre as mesmas previsões. Reproduções de resultados
  selados usam as sementes e os parâmetros efetivamente registrados.
- O PDF D-047 e seu ZIP permanecem disponíveis. A revisão do GitHub será
  tratada em etapa posterior. Novos comentários e commits em português.

## Histórico — monografia revisada (D-047)

- Versão atual: reports/monografia_template_revisada.zip e
  output/pdf/monografia_template_revisada.pdf. Overleaf com main.tex e XeLaTeX.
- Resumo em português em página própria, conforme os dois modelos enviados.
  Descritivas, descritores e resultados ordinais no corpo. Usar a sequência
  sorteio de 9.526, 3.869 vínculos, quadro de 80.943 e coorte de 9.526.
- 59 verificou 461 faixas do sorteio original na coorte e os formatos dos
  vínculos nas 9.526 faixas. A tabulação não é censo do LRCLIB.
- Reaproveitamento da etapa de 200 mil descrito como origem e exposição.
  Resultados científicos e a entrega D-046 seguem preservados.
  Revisão acadêmica com Leandro Tavares Correia, sem nova execução pesada.

## Histórico — monografia D-046

- Versão final para revisão entregue em reports/monografia_template_final.zip
  e output/pdf/monografia_template_final.pdf. Entrada LaTeX em
  reports/monografia_template_final/main.tex. Upload do ZIP no Overleaf com
  XeLaTeX, main.tex e BibTeX automático.
- Foco na avaliação ordinal das 9.526 faixas com letra; sorteio probabilístico
  original e seleção textual documentados. Resultados de 200 mil no apêndice.
  Bootstrap 58 usa as previsões existentes e limites condicionais.
- Seguir com revisão do orientador. Preservar a versão anterior e os selos
  científicos. Nenhuma nova execução de treino ou busca é necessária.

## Histórico do relato da comparação das 9.526 faixas (D-045)

- 57 REAL concluído e conferido nas 9.526 faixas. Acurácia balanceada de
  56,14% Baseline, 56,24% Tradicional, 55,91% Profundo e 55,96% Combinado.
  O Profundo acertou 329 de 1.059 faixas altas frente a 278 no Baseline.
- Resultados e interpretação em reports/classificacao_9526_v1. Usar as
  métricas pareadas e o alcance da amostra com letra no relato do TCC.

## Histórico da preparação da classificação (D-044)

- Pesquisador autorizou seguir com a candidata v2 e os quatro blocos.
  Níveis 0–19, 20–39 e 40–100. Logística ordinal com L2, mesmas divisões
  agrupadas 5×3 e acurácia balanceada primária.
- Script 57 preparado. A conferência da base real validou 9.526 faixas,
  6.271 componentes e suporte nas 5×3 divisões. Há 9.018 embeddings
  reaproveitáveis por hash e 482 textos para o encoder local. O pesquisador
  executa o comando do guia docs/protocolo_classificacao_9526_v1.md.
- Após o treino, conferir cobertura das previsões e ganho de cada bloco.

## Histórico da candidata ampliada (13/11/2026, D-043)

- 55 REAL concluído pelo pesquisador. 22.443 consultas e 179 novos vínculos
  conferidos com o checkpoint, Parquet e registros originais do LRCLIB.
- 56 REAL leve produziu candidata v2 de 9.526 faixas e letras conferidas,
  em quadro de 80.943. As cinco bandas marginais do sorteio original estão
  preservadas. `sleep` tem 23 de 147 e `indie-pop` tem 81 de 82. 9.033 faixas
  da candidata vieram da coorte histórica de modelagem.
- Em `sleep`, 55 encontrou 18 letras em 13.983 consultas. Diagnóstico por
  metadados de 48 faixas entre 680 fora dos índices existentes encontrou 17
  indicações instrumentais e zero candidatas textuais pela chave nativa exata.
- Próximo ponto metodológico: definir com o pesquisador o domínio e o
  tratamento da exposição histórica antes do treinamento da candidata v2.
  Ver docs/recuperacao_generos_deficitarios_v1.md e decisão D-043.

## Histórico da recuperação dirigida (13/11/2026, D-042)

- 53 conferiu 43 caches locais históricos e revalidou 42 letras. O quadro
  disponível chega a 80.764 faixas. Persistem déficits de 142 em `sleep`,
  42 em `romance` e 21 em `detroit-techno` em relação às cotas de 40.
- 54 encontrou 22.443 faixas dos três gêneros com artista coberto nos índices
  existentes, fora dos dois sorteios anteriores. 55 preparado para busca
  dirigida manual no SSD D:, com checkpoint por consulta. Guia
  docs/recuperacao_generos_deficitarios_v1.md.
- Conferir os resultados de 55 e a capacidade por gênero antes de definir
  o quadro da análise. O uso definitivo da candidata requer definição do
  domínio e tratamento da exposição histórica com o pesquisador.

## Histórico da candidata com letras (07/11/2026, D-041)

- Pesquisador exige 9.526 faixas com letra vinculada e admite novas faixas.
  Preservar sorteio original e 3.869 aceitas como diagnóstico de cobertura.
- 52 REAL leve produziu candidata com 9.526 IDs distintos e textos íntegros
  conferidos por hash. Quadro de 80.722, 82 gêneros na candidata e totais das
  cinco bandas de popularidade iguais ao sorteio original. Quatro cotas de
  gênero são inviáveis na capacidade atual. Peso `linked_weight` refere-se
  ao quadro de vínculos aceitos. Uso definitivo requer definição do domínio.
- Próxima frente: avaliar revalidação de caches históricos nos estratos
  deficitários. Candidata não é avaliação independente das análises anteriores.
  Plano docs/amostra_com_letras_candidata_v1.md. Sem treino ou ressorteio
  oportunista para aproximar os metadados.

## Histórico da cobertura consolidada (07/11/2026, D-040)

- 50 REAL concluído pelo pesquisador e conferido. 25 novas aceitas nas 40
  consultas de limite. Textos originais conferidos por ID no dump.
- 51 REAL leve concluído pelo agente. Manifesto privado referencia as letras
  nas fontes seladas, sem duplicar os textos. Total 3.869/9.526 (40,62%), 1.085
  ambíguas, 4.155 sem candidato, 416 instrumentais e uma sem texto. Sorteio,
  pesos e categorias de origem preservados. As duas novas indicações
  instrumentais ficam como evidência de 50, sem recodificar o status-base.
- Cobertura em reports/recuperacao_consolidada_nova_amostra_v1. Discutir com
  o pesquisador domínio e avaliação antes de qualquer treino. Nova busca
  requer evidência de uma via distinta de recuperação.

## Histórico do piloto online e preparação da revisão local (07/11/2026, D-039)

- 49 REAL concluído pelo pesquisador e conferido. 100 respostas HTTP 200, zero
  candidatas, 93 vazias, cinco sem compatível, uma indicação instrumental e
  uma no teto da API. O resultado não sustenta ampliar esse protocolo online.
- 50_revisar_limite_de_candidatos.py preparado/testado para 40 consultas
  locais barradas pelo teto de 500 antes da elegibilidade. Em sete inspeções
  de metadados, seis tinham de 1 a 457 compatíveis. Execução real manual
  pendente, SSD D:. Guia docs/execucao_revisao_limites_nova_amostra_v1.md.
- Conferir ganho de 50. As 3.844 aceitas e o sorteio seguem selados.

## Histórico do piloto online (07/11/2026, D-038)

- 49_pilotar_busca_online_lrclib.py preparado/testado. Sorteio local selado de
  100 das 4.155 faixas sem candidato, AAS sem reposição, semente 20261107.
- Execução online manual pendente, sem SSD. Busca sequencial apenas em
  `/api/search`, por artista e título. Teto de 100 consultas distintas, pausa
  conforme `Retry-After`, checkpoint por consulta. Guia
  docs/execucao_piloto_online_nova_amostra_v1.md.
- Candidatas provisórias ficam separadas das 3.844 aceitas. Verificar vínculo
  e resultado do piloto antes de decidir expansão ou modelagem.

## Histórico da revisão documental (07/11/2026, D-037)

- 47 REAL concluído pelo pesquisador e conferido. 58 novas aceitas entre 108
  conflitos plain/LRC, total 3.835. As outras 50 permaneceram ambíguas.
- 48 REAL leve concluído pelo agente. Revisão documental de 13 grafias, nove
  novas aceitas e quatro inconclusivas. Total 3.844/9.526 (40,35%), 1.110
  ambíguas, 4.155 sem candidato pelos métodos usados, 416 instrumentais e uma
  sem texto. Complementos disjuntos, amostra e pesos conferidos.
- Próxima frente de recuperação em avaliação: piloto pequeno nas pendências
  sem candidato, com fonte atual e validação dos vínculos. Registrar resultados
  separadamente. Os quatro casos inconclusivos exigem evidência adicional.

## Histórico de caixa e texto sincronizado (07/11/2026, D-036)

- 46 REAL concluído pelo pesquisador e conferido. 130 novas aceitas, total 3.777
  de 9.526 (39,65%), 1.168 ambíguas, 4.164 sem candidato, 416 instrumentais e uma
  sem texto. Sorteio, pesos e resultados 43 preservados.
- 47_revisar_caixa_plain_lrc.py preparado/testado. Execução real manual com SSD
  D:. Revisa 108 conflitos plain/LRC pelos IDs já registrados em 43. Confere
  hashes e mantém os critérios de metadados. Guia
  docs/execucao_revisao_caixa_plain_lrc_nova_amostra_v1.md.
- Depois conferir as novas aceitações e avaliar as fichas de variantes de artista.
  Os 13 casos requerem validação de identidade. A cobertura segue seletiva.

## Histórico da continuidade da recuperação (07/11/2026, D-035)

- Pesquisador escolheu continuar a recuperação antes de modelar. 44 e 45 reais
  concluídos e conferidos. Consolidação mantém 3.647 aceitas e fichas para 13
  consultas de variantes de artista, com validação pendente.
- 46 preparado e testado em sete verificações. Execução real manual pendente
  para 831 ambiguidades por textos concorrentes, SSD D:. Guia
  docs/execucao_revisao_caixa_nova_amostra_v1.md. Usa índices existentes e
  registra complemento de vínculos e textos originais.
- A comparação nova uniformiza caixa, espaços e a tipografia vigente. A
  elegibilidade de metadados e o controle plain/LRC seguem o classificador
  de origem. Prosseguir com recuperação dirigida após conferir a execução.

## Histórico do diagnóstico de chaves (06/11/2026, D-034)

- 43 REAL concluído/conferido: 3.647 aceitas (+2.222), 1.298 ambíguas, 4.164
  sem candidato, 416 instrumentais/uma sem texto, zero erros; amostra preservada.
  Não repetir 42/43 ou flexibilizar conteúdo para aumentar contagens.
- 44_diagnosticar_consultas_sem_candidato.py preparado/testado (três testes),
  execução real manual pendente, SSD D:. Guia
  docs/execucao_diagnostico_chaves_nova_amostra_v1.md. Só metadados dos 4.164,
  índices nativos/FTS, sem letras, rebuild, rede ou mudança de status.
- Indícios de alias/título/duração não são vínculos validados. Não aceitar
  covers, aliases genéricos ou similaridade aproximada automaticamente.
- Depois avaliar diagnóstico/candidatos e justificar recuperação/revisão dirigida.
  Cobertura continua seletiva; pesos não corrigem perdas. Modelagem a definir.

## Histórico da revisão de bloqueios (06/11/2026, D-033)

- 42 REAL concluído: 1.425 aceitas/362 instrumentais/3.574 ambíguas/4.164 sem
  candidato/uma sem texto; zero erros. Indicação instrumental vem do LRCLIB,
  não de instrumentalness Spotify ou confirmação humana. Preservar resultados.
- Após questionamento, auditoria demonstrou filtros excessivos: 2.139 plain/LRC,
  com dez casos pontuais iguais após whitespace, e 1.023 versões com candidato
  compatível vetado por outra versão. Não atribuir perdas só à base disponível.
- 43_revisar_bloqueios_vinculacao.py preparado/testado (quatro testes), execução
  real manual pendente, SSD D:. Guia docs/revisao_bloqueios_vinculacao_v2.md.
  Só 3.162 consultas, índices prontos, sem rebuild. Não executar reavaliação
  integral pelo agente ou modificar bytes/protocolos/avaliações anteriores.
- Correção: igualdade exata após whitespace/tipografia, textos originais intactos;
  candidatos incompatíveis não vetam os compatíveis. Sem fuzzy, alteração de
  duração/qualificadores, aceitação de conteúdo diferente ou nova amostra.
- 4.164 sem candidato e demais ambiguidades exigem diagnóstico separado.
  Não prometer quantidade de novas aceitas nem iniciar modelos automaticamente.

## Histórico da busca local (06/11/2026, D-032)

- 41 REAL concluído/conferido: 682 aceitas, 87 instrumentais, 8.757 pendentes;
  zero erros, 9.526 consultas, 30,32 s. Não é cobertura final do LRCLIB.
- 42_buscar_letras_nova_amostra.py preparado/testado (quatro testes sintéticos),
  **execução real pendente manual**, SSD em D:. Guia:
  docs/execucao_busca_nova_amostra_v1.md. Não executar busca/varredura pelo agente.
- Reutiliza índice v2 completo/selado, 24.330 artistas. Complemento separado só
  para artistas cuja falta de cobertura for demonstrada na execução; não refazer
  índices antigos. Mesmas regras v2, sem relaxar versões/duração/equivalência.
- Preserva aceitas/instrumentais de 41 e todos os sorteados; negativas locais
  completas só reutilizadas com mesma consulta/snapshot/código e sem limite.
  Resultados negativos não são ausência universal. Não substituir faixas.
- Depois receber resumo/cobertura/transições, diagnosticar seleção e pendências.
  Não repetir 39–41, treinar, gerar embeddings ou alterar monografias automaticamente.

## Histórico do reaproveitamento (06/11/2026, D-031)

- 40 REAL concluído pelo pesquisador/conferido: 9.526 faixas, 82 gêneros, hashes,
  contagens e pesos reconciliados. Doze médias com desvio máximo 0,01901 DP;
  diferença máxima por período 0,4050 pp. Manter sorteio, sem ajuste oportunista.
- Interpretação em reports/interpretacao_nova_amostra_catalogo_v1.md; duas figuras
  agregadas salvas/revisadas. Não repetir 39/40, código selado ou monografias.
- 41_reaproveitar_letras_nova_amostra.py preparado/testado (seis verificações
  sintéticas), **execução real pendente manual**. Guia:
  docs/execucao_reaproveitamento_nova_amostra_v1.md. Só caches locais por chave,
  sem SSD/rede/índice novo. Agente não executa o processamento individual real.
- Reuso exige mesma consulta completa e texto/vínculo íntegros. Prioridade v2;
  v1 só quando consulta ausente em v2. Negativas/ausência de cache são pendências,
  não inexistência de letra. Aceitação herdada não equivale a revisão humana.
- Depois receber contagens, preparar busca dirigida das pendências e diagnosticar
  cobertura; não substituir músicas perdidas ou iniciar modelos automaticamente.

## Histórico da preparação (06/11/2026, D-030)

- Preservação acadêmica concluída: reports/preservacao_monografia_20261106,
  430 arquivos, PDFs/fontes/agregados, hashes/CRC conferidos; originais mantidos.
- Dimensionamento concluído em agregados: n=9.526 de N=1.159.764, 82 gêneros,
  AAS sem reposição/alocação proporcional, 5–179 por gênero, semente 20261106.
  Metas: proporção global individual aproximada 95%/1 pp; doze médias conjuntas
  aproximadas 95%/0,05 DP (Bonferroni). Não garante letras ou precisão preditiva.
- 40_preparar_nova_amostra.py sortear preparado e testado em fixtures;
  **execução real pendente manual**. Não executar sorteio integral pelo agente.
  Plano/cenários em reports/nova_amostra_catalogo_v1; guia e protocolo em
  docs/execucao_nova_amostra_catalogo_v1.md e docs/plano_nova_amostra_catalogo_v1.md.
- Próximo: receber resumo/comparativos do sorteio, interpretar sem ressorteio
  oportunista e organizar recuperação das selecionadas, reutilizando evidências
  compatíveis. Não repetir 39/dimensionar ou buscar letras/treinar automaticamente.

## Foco vigente definido pelo pesquisador (06/11/2026, D-029)

- Seguir exatamente: descrição completa do catálogo original → dimensionamento
  estatístico e nova amostra menor → recuperação de letras → modelagem a definir.
- Descritiva é a parte inicial de apresentação dos dados, não o centro do TCC.
  Incluir dicionário, distribuições, gênero/período, relações e PCA exploratória.
- Script 39 REAL concluído pelo pesquisador e conferido: 1.159.764 faixas,
  treze figuras, PCA descritiva. Não repetir a execução. Interpretação em
  reports/interpretacao_descritiva_catalogo_completo_v1.md; guia:
  docs/execucao_descritiva_catalogo_completo_v1.md.
- Dimensionamento posteriormente concluído em D-030, com literatura e metas de
  precisão. Não congelar arbitrariamente 10 mil ou adotar só os eixos da PCA.
  Dois primeiros eixos retêm 44,35%; log1p não reduziu muito a assimetria.
- Preservar resultados/PDFs anteriores como histórico; não retreinar ou ajustar
  a monografia v3 automaticamente. Esta prioridade supera o encaminhamento D-028.

## Consolidação acadêmica vigente (06/11/2026, D-028)

- Nova monografia autorizada e concluída: reports/monografia_template_200k_v3/main.tex,
  ZIP correspondente e PDF de 45 páginas em output/pdf/. Objetivos integrados à
  introdução; regressão, ordinal/PCA e sensibilidade posterior separadas.
- Versão 2/PDF/ZIP e fontes/resultados científicos preservados por hash. Script 38
  é editorial e leve; não justifica repetir processamento científico.
- Próxima etapa: revisão com orientador e discussão dos custos de decisão.
  Sem novo treino/coleta automático. Guia docs/execucao_monografia_template_200k_v3.md.

## Nova etapa exploratória autorizada (04/11/2026, D-025)

- Atualização 06/11/D-027: 36 real concluído e conferido; 37 agregados/cauda
  delimitada de 128 faixas/figuras concluído sem treino. Principal e sensibilidade
  preservados; alternativa melhora BA/recuperação e reduz precisão/acurácia global.
  Próximo é consolidação científica/monografia, sem novo processamento pesado
  necessário ou adoção retrospectiva da regra alternativa como principal.
- Histórico D-027: produção ordinal 34 concluída/conferida (20 partes,
  480 ajustes internos, 77.535 faixas); 35 agregados/PCA concluído sem refit.
  36 sensibilidade da regra de decisão posteriormente concluído/conferido.
  Mantém probabilidades e resultados principais; nenhum treino automático.
  Guia: docs/execucao_sensibilidade_decisao_ordinal_v1.md.

- Atualização 05/11/D-026: 31/32 reais concluídos; triagem técnica 33 das 133
  fichas concluída, sem revisão semântica humana ou mudança de vínculos. 34
  classificação ordinal com smoke real concluído/conferido: 318 faixas, recarga
  exata e gate aprovado. Primeiro lote real concluído/conferido, 1/20 partes;
  posteriormente produção integral concluída; não repetir treino para analisar.
  Protocolo e guia em docs/protocolo_classificacao_ordinal_200k_v1.md e
  docs/execucao_classificacao_ordinal_200k_v1.md. Não executar treino real pelo agente.

- O pesquisador autorizou condução autônoma do plano de níveis de popularidade,
  PCA e auditoria dirigida da vinculação, preservando a primeira regressão.
- A nova investigação é separada da avaliação congelada. Protocolos atuais:
  docs/protocolo_niveis_popularidade_200k_v1.md e
  docs/protocolo_piloto_vinculacao_200k_v1.md. Não alterar os selos 19–23.
- Começar pelo domínio observado existente e limites operacionais 20/40;
  sensibilidade 40/60, sem escolher limites pelo desempenho. Não alegar hits
  oficiais ou representatividade do catálogo. Novo treino só após diagnóstico.
- 31 agregados é leve; 31 previsoes e 32 percorrem tabelas individuais completas
  e são executados manualmente pelo pesquisador. Autonomia não revoga essa regra.
- Novo cruzamento integral, nova amostra e regeneração de embeddings dependem de
  necessidade demonstrada. Não executar automaticamente comandos históricos.

## Objetivo científico

Avaliar associação e contribuição preditiva incremental de descritores de letras para estimar a popularidade Spotify observada no snapshot da fonte, em conjunto com descritores acústicos e metadados. Não fazer afirmações causais.

## Engenharia e dados

- Usar Python; não usar R.
- Preservar dados brutos imutáveis e nunca versionar bases brutas, derivados volumosos, letras ou credenciais.
- Toda normalização cria colunas novas e preserva campos originais.
- Documentar regras, quantidades antes/depois, exceções e destino de rejeitados.
- Separar sempre `spotify_popularity`, `genius_lyrics_views` e `lfm_playcount`.
- Atualizar dicionário de dados, decisões e proveniência quando o schema mudar.
- Não usar notebooks como única fonte da lógica; a pipeline deve ser reproduzível por CLI.
- Executar testes e lint antes de concluir alterações.
- Não fazer scraping massivo nem treinar modelos na Base v0.1.

## Modelagem futura

- Evitar leakage por artista, composição e versões da mesma faixa.
- Exigir splits agrupados por artista e por chave operacional de composição.
- Não tratar a chave normalizada como identificador universal.

## Continuidade e autoridade (consolidação de 01/11/2026)

- Este é o TCC existente, não um projeto novo. Atuar como agente técnico principal;
  concluir tarefas autorizadas e manter contexto no repositório.
- Ler, nesta ordem, `docs/ESTADO_ATUAL.md`, `docs/CONTEXTO_TCC.md`,
  `docs/PLANO_EXECUCAO.md` e `docs/MAPA_ARTEFATOS.md`. O registro canônico de
  decisões é `docs/decisions.md` (equivale a DECISOES_METODOLOGICAS; não duplicar).
- Não inferir execução pela existência de um script. Relacionar resultados a
  resumos/checkpoints, schemas e verificações; distinguir confirmado de pendente.
- Antes de editar, inspecionar Git; preservar alterações pessoais. Não fazer
  commit/push sem instrução explícita. Não mover arquivos com consumidores sem
  análise; movimentações incompatíveis/destrutivas exigem autorização concreta.
- Preservar toda a história; organizar primeiro por documentação e entradas.
  Não excluir resultados, mover dump LRCLIB, duplicar bases ou reconstruir índices
  sem necessidade demonstrada. Não coletar letras para pequenas metas de cobertura.

## Regra obrigatória de execução manual

- O agente prepara/revisa Python, comandos PowerShell, entradas/saídas, logs,
  checkpoints, retomada e critérios de conclusão. O pesquisador executa trabalhos
  pesados. Parar antes de executá-los, mesmo com permissão técnica disponível.
- Isso inclui varreduras extensas, buscas em larga escala no LRCLIB, grandes
  índices, processamento integral de centenas de milhares de registros, geração
  massiva de descritores/embeddings, treinamento e experimentos custosos.
- Não contornar a regra com processos em segundo plano. Não assumir que um
  artefato foi produzido sem evidência. Aguardar resultados do usuário, analisá-los
  e continuar. Inspeções limitadas de metadados, amostras pequenas, testes com
  fixtures e lint são permitidos; interromper inspeção que se torne custosa.
- Não executar comandos históricos `all`, scripts 01–16 ou treinos apenas para
  verificar organização. Usar testes específicos; registrar exatamente o executado.

## Decisão científica aprovada em 01/11/2026

- Priorizar o domínio analítico observado de faixas com letras aceitas da amostra
  de 200 mil. Não presumir amostra representativa do catálogo nem de todas as
  músicas com letras. Não reiniciar recuperação sem evidência concreta.
- Preservar as 200 mil faixas e pesos para descrição/cobertura/seleção. Os pesos
  não corrigem automaticamente disponibilidade de letras. D-017 aprovada:
  ajuste/métricas principais com pesos iguais por faixa, MAE primário/seleção;
  RMSE/R² complementares. Sensibilidade com MAE ponderado pelos pesos originais,
  mesmas observações/folds/previsões externas e sem retreinar ponderado. Não
  selecionar modelos pela sensibilidade. Preservar pesos/estratos para descrição.
- Comparar Baseline, Tradicional, Profundo e Combinado nas mesmas observações e
  divisões. Prevenir vazamento por artista, composição operacional, versões e
  textos iguais; reconciliar exposições históricas antes de definir validação.
- CV agrupada aninhada 5 folds externos × 3 internos aprovada pelo pesquisador
  em 01/11/2026 (D-015). Componentes/base/folds reais concluídos no script 21,
  com separação auditada; não redesenhar splits para melhorar resultados.
  Script 22 smoke real concluído: 318 faixas, reprodução exata, sem avisos.
  Produção 22 concluída, conferida em 02/11: 20 partes Ridge + dez referências, 77.535
  previsões por variante. Não alterar código/protocolo/modelos/folds por resultado.
  Diagnósticos 23 concluídos, métricas reproduzidas sem refit/IC. Material parcial
  24 para monografia gerado de agregados leves, sem dados individuais/modelos.
  Próximo: integração/escrita, não retreino automático. Não declarar significância
  com métricas pontuais ou tratar cinco folds como réplicas independentes.
- O teste V0.6 foi aberto em 14/10/2026. Novo sorteio/split não restaura confirmação
  independente. Não carregar alvos históricos em auditorias apenas de linhagem.
- Não transportar descritores LFM2b ou embeddings antigos por simples track_id.
  Demonstrar compatibilidade de texto/versão/normalização/modelo e dimensão.
- Idioma automático não é verdade humana e não autoriza exclusão silenciosa.
  Alterar população, amostragem, resposta, desenho de validação ou alcance de
  inferência requer participação do pesquisador. Correções leves e documentação
  dentro do escopo autorizado não exigem nova aprovação.
- Após etapa relevante: atualizar estado, decisões e plano; manter rastreabilidade
  e limitações para a monografia. Não alegar suficiência preditiva pelo tamanho.

## Encerramento principal e revisão acadêmica (02/11/2026)

- O pesquisador determinou congelar a avaliação existente e produzir a monografia
  completa (D-022). Não iniciar novos treinamentos, LRCLIB ou embeddings massivos
  como continuação automática. Manter resultados, modelos, previsões e folds.
- A entrada acadêmica daquela etapa foi reports/monografia_template_200k_v2/main.tex (D-023),
  com ZIP e PDF TeX de 34 páginas no template fornecido. Versão de 57 páginas e
  dois trechos anteriores preservados. Orientador: **Leandro Tavares Correia**,
  grafia confirmada explicitamente pelo pesquisador. Próximo: revisão acadêmica.
- Template/Ana e TCCs de Estatística da BDM orientam apresentação; citar fontes
  originais pertinentes e verificadas. Engenharia e pendências administrativas
  ficam fora do PDF acadêmico; não apagar seus registros nem PDFs históricos.
- Texto registra token adicional de espaço do E5 e limites auxiliares condicionais;
  não afirmar receita canônica exata, significância integral ou inferência de catálogo.
- Requisitos institucionais/datas não confirmadas não devem ser inventados. Não
  confundir versão completa para revisão com documento homologado para depósito.


## Publicação e idioma (02/11/2026, D-024)

- O pesquisador autorizou organizar e publicar esta consolidação no GitHub.
  Preservar a visibilidade privada existente e verificar o remoto após push.
- Novos commits, comentários e documentação devem ser escritos em português.
  Preservar os bytes de códigos/protocolos selados e o histórico já publicado;
  não traduzir APIs/colunas ou reescrever commits por estética.
- Usar scripts/30_auditar_publicacao_git.py antes de publicar. Dados individuais,
  letras, dump, modelos, embeddings e credenciais ficam locais. Remoções do índice
  preservam o arquivo local; não apagar experimentos/resultados como limpeza.
