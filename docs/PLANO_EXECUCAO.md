# Plano de execução científica e revisão acadêmica

O percurso aprovado na D-029 foi concluído até a modelagem e a monografia
revisada (D-047). As linhas anteriores ficam preservadas como histórico.
Fases pesadas continuam manuais.

## Próxima ação vigente — revisão acadêmica (D-049)

Acompanhar a revisão com o orientador usando a edição D-048 confirmada
no Overleaf. Para novas publicações, auditar o índice com o script 30 e
usar português nos commits e comentários.

## Histórico — edição otimizada para Overleaf (D-048)

1. Importar reports/monografia_template_overleaf.zip como novo projeto,
   selecionar main.tex e XeLaTeX. Usar output/pdf/monografia_template_overleaf.pdf
   como referência visual da compilação local.
2. Depois, revisar o repositório do projeto para publicação. Preservar as
   reproduções seladas e usar português em comentários e commits novos.

## Histórico — revisão acadêmica (D-047)

1. Importar reports/monografia_template_revisada.zip no Overleaf, usar main.tex
   e XeLaTeX. O PDF local está em output/pdf/monografia_template_revisada.pdf.
2. Revisar redação, referências e apresentação com o orientador, usando os
   mesmos resultados científicos e o alcance descrito na monografia.

## Histórico — relato da classificação (D-045)

1. 57 concluído com previsões externas verificadas para 9.526 faixas.
2. A interpretação compara o ganho balanceado e os acertos por classe.
3. Incorporar ao relato do TCC a contribuição preditiva observada das letras
   e o alcance da avaliação nas faixas com letra verificada.

## Histórico — classificação em três níveis (D-044)

1. Base e divisões conferidas com `57_classificar_amostra_9526.py --conferir`.
2. Executar 57 manualmente para completar 482 embeddings e comparar os
   quatro conjuntos de preditores nas mesmas partes externas.
3. Interpretar as métricas reunidas, os resultados por classe e o ganho em
   relação ao Baseline para relatar a contribuição preditiva das letras.

## Histórico — definir o uso da candidata v2 (D-043)

1. 55 executado. Os 179 novos vínculos foram confrontados com o checkpoint,
   os Parquet e o dump original.
2. 56 concluído. A candidata v2 satisfaz 9.526 vínculos e registra os
   desvios por gênero e atributo acústico.
3. Definir com o pesquisador o domínio da avaliação e como registrar a
   sobreposição com a coorte histórica. Depois preparar a modelagem.

## Histórico — busca dirigida por gênero (D-042)

1. As etapas 53 e 54 revalidaram o cache e mediram a cobertura operacional
   dos índices nos três gêneros de interesse.
2. Executar manualmente 55 no SSD D: conforme o guia
   docs/recuperacao_generos_deficitarios_v1.md.
3. Conferir os vínculos e os totais por gênero. Usar o resultado para definir
   o quadro e o alcance da avaliação com o pesquisador.

## Histórico — consolidar a alternativa com 9.526 letras (D-041)

1. A etapa 52 produziu e verificou a candidata de tamanho fixo no quadro
   com 80.722 faixas com letra aceita. O sorteio inicial segue como auditoria
   de cobertura do catálogo.
2. Avaliar ganhos por revalidação dirigida de caches antigos e, com acesso
   autorizado, por fonte complementar nas células de baixa cobertura.
3. Definir com o pesquisador o domínio e a exposição histórica antes de
   transformar a candidata em base de avaliação. Manter os resultados antigos.

## Histórico — definir a avaliação da nova amostra (D-040)

1. 50 real acrescentou 25 letras, com checkpoint e originais conferidos.
2. 51 real consolidou a recuperação em 3.869 de 9.526 faixas. A diferença de
   cobertura por popularidade e gênero segue documentada.
3. Discutir o domínio observado com o pesquisador antes de especificar o
   desenho da avaliação. O sorteio completo e os pesos sustentam a descrição
   e o diagnóstico de cobertura. Uma nova recuperação requer evidência nova.

## Histórico — revisão dirigida de limites locais (D-039)

1. O piloto online foi conferido e a ampliação pelo mesmo protocolo ficou
   sem justificativa empírica, com zero candidatas em 100 consultas.
2. Executar 50 manualmente com SSD D:. A leitura por chaves existentes se
   restringe às 40 consultas limitadas. O comando consta no guia da etapa.
3. Conferir ganho, consolidar cobertura e discutir o domínio da modelagem.

## Histórico — piloto online de 100 faixas (D-038)

1. A seleção está selada, com 100 faixas entre as 4.155 sem candidato.
2. Executar 49 manualmente. O comando e a retomada constam no guia
   execucao_piloto_online_nova_amostra_v1.md.
3. Conferir resultados, distinguir candidatas, limites e falhas operacionais
   e revisar vínculos antes de decidir se a recuperação online deve continuar.

## Histórico — avaliar ganho adicional na recuperação (D-037)

1. A etapa 47 acrescentou 58 aceitas e os complementos foram conferidos.
2. A etapa 48 acrescentou nove aceitas após revisar 13 fichas. Total
   verificado 3.844/9.526. Quatro fichas inconclusivas retidas para evidência
   adicional, em razão de edição ou participações.
3. Planejar um piloto pequeno nas 4.155 sem candidato com uma fonte atual e
   registrar o ganho adicional e a qualidade antes de decidir expansão.

## Histórico — recuperar equivalências plain/LRC (D-036)

1. Concluído: conferência de 46. As 130 aceitações elevaram a cobertura para
   3.777/9.526, com 1.168 ambiguidades restantes.
2. Preparado e testado: 47 para 108 conflitos plain/LRC com leitura pontual por
   ID. Executar com SSD D: segundo execucao_revisao_caixa_plain_lrc_nova_amostra_v1.md.
3. Conferir e combinar apenas os novos vínculos, revisar variantes de artista
   com evidência específica e atualizar o diagnóstico de cobertura antes de
   decidir a modelagem.

## Histórico — recuperar textos equivalentes (D-035)

1. Concluído: diagnóstico 44 de 4.164 consultas e consolidação leve 45 dos
   metadados de catálogo, sorteio e aceitas. Treze consultas em fichas privadas.
2. Decisão do pesquisador: continuar a recuperação antes de definir modelagem.
3. Preparado e testado: 46 revisa caixa em 831 consultas por índices existentes.
   Executar manualmente com SSD D: conforme execucao_revisao_caixa_nova_amostra_v1.md.
4. Conferir o complemento de vínculos e textos, atualizar a cobertura e avaliar
   as fichas com variantes de artista e as demais pendências dirigidas.

## Histórico — diagnóstico de chaves (D-034)

1. Concluído: 43 real; 3.647 aceitas, ganho 2.222, vínculos anteriores preservados.
2. Concluído: conferência de selos/transições e análise das 1.298 ambiguidades;
   oito pares de textos e doze consultas sem candidato inspecionados de forma
   limitada. Sem generalizar os exemplos ou mudar regras por contagem desejada.
3. Preparado/testado: 44, três testes sintéticos. **Pendente manual**, comando
   no guia execucao_diagnostico_chaves_nova_amostra_v1.md. Diagnostica apenas
   metadados dos 4.164, sem aceitação automática, índice novo ou corpo de letra.
4. Interpretar causas/candidatos e justificar recuperação ou revisão posterior.
5. Auditar cobertura/seleção antes de definir modelagem ou alcance de inferência.

## Histórico — revisão dirigida de bloqueios (D-033)

1. Concluído: 42 real, 1.425 aceitas/362 instrumentais/3.574 ambíguas/4.164
   sem candidato/uma sem texto; zero erro/pendência. Preservar resultados.
2. Concluído: auditoria leve de motivos e dez pares plain/LRC, revelando dois
   bloqueios indevidos. Não confundir rejeição de regra com inexistência de letra.
3. Preparado/testado: 43, quatro testes sintéticos, revisão de 3.162 casos
   usando índices prontos, sem reconstrução. **Pendente manual**, um comando
   em revisao_bloqueios_vinculacao_v2.md. Mesmos sorteados e pesos.
4. Conferir transições/ganhos reais; não prometer quantidade de aceitas.
5. Diagnosticar separadamente 4.164 consultas sem candidato e ambiguidades
   remanescentes, com busca dirigida justificada. Modelagem continua a definir.

## Histórico — busca local no SSD (D-032)

1. Concluído: 41 real, 682 aceitas/87 instrumentais/8.757 pendentes/zero erros.
   Selos conferidos; amostra e pesos mantidos. Não interpretar como cobertura final.
2. Concluído: metadados/selos do índice v2 conferidos sem consulta de faixas reais.
   24.330 artistas, 5.726.985 entradas, scan histórico de 33.714.178 registros.
3. Preparado/testado: 42, quatro testes leves em dump sintético. **Pendente manual**:
   um comando no guia execucao_busca_nova_amostra_v1.md, SSD em D:.
4. A execução identifica e indexa somente artistas adicionais, se necessário,
   sem reconstruir índices antigos. Depois busca consultas pendentes com regras
   v2; protege as decisões 41 e reaproveita negativas completas compatíveis.
5. Conferir resultados/cobertura e composição do subconjunto encontrado; revisar
   ambiguidades/perdas, sem substituir faixas. Só depois decidir modelagem.

## Histórico — reaproveitamento exato de caches (D-031)

1. Concluído: sorteio real 40 pelo pesquisador, 9.526 faixas. Conferência de
   selos/contagens/pesos e comparação de metadados favorável, sem ressorteio.
2. Concluído: interpretação e duas figuras agregadas; esquema e metadados dos
   caches inspecionados apenas por consultas SQL limitadas, sem ler textos.
3. Preparado/testado: 41_reaproveitar_letras_nova_amostra.py. **Pendente manual**,
   um comando em execucao_reaproveitamento_nova_amostra_v1.md. Não precisa SSD.
4. Analisar contagens de aceitos/instrumentais/pendentes. Não tratar conclusão
   do cache como conclusão de toda a recuperação ou negativas como falta de letra.
5. Preparar busca dirigida para as pendências, reutilizando índices existentes
   quando compatíveis; execução custosa manual. Não substituir músicas perdidas.
6. Diagnosticar cobertura e só depois decidir domínio/modelagem.

## Histórico — sorteio manual dimensionado (D-030)

1. Concluído: preservação local de 430 arquivos acadêmicos/agregados, com hashes,
   em reports/preservacao_monografia_20261106. Originais mantidos.
2. Concluído em agregados: dimensionamento n=9.526, 82 gêneros, alocação
   proporcional, metas de precisão explícitas; plano/precisão/cenários em
   reports/nova_amostra_catalogo_v1. Quatro verificações sintéticas/lint aprovados.
3. **Pendente manual**: script 40_preparar_nova_amostra.py sortear, comando único
   em execucao_nova_amostra_catalogo_v1.md. Não repetir 39/dimensionar.
4. Conferir os comparativos de metadados e categorias do único sorteio; não
   excluir/ressortear para melhorar médias. Preservar todos os selecionados.
5. Organizar recuperação das letras, começando por vínculos locais compatíveis;
   separar letra aceita, instrumental e não localizada. Não há busca automática.
6. Diagnosticar perdas/cobertura; só então decidir modelagem e alcance de inferência.

## Histórico — descrição e dimensionamento previstos (D-029)

1. Concluído: script 39 real pelo pesquisador, descrição de 1.159.764 faixas.
2. Conferido: agregados/treze figuras e PCA sem releitura integral pelo agente.
3. Interpretação concluída em interpretacao_descritiva_catalogo_completo_v1.md,
   para a parte inicial da monografia. PDF anterior permanece preservado.
4. Próximo: pesquisar e definir dimensionamento/alocação de nova amostra menor
   com literatura, precisão e critérios de composição explícitos. Gênero é
   candidato fundamentado; conferir também BPM e demais metadados, sem depender
   exclusivamente dos dois primeiros componentes.
5. Recuperar letras das faixas sorteadas, reutilizando evidência compatível.
6. Só depois decidir modelagem. Não repetir modelos, embeddings ou cruzamento
   integral por continuidade automática.

Nenhuma amostra nova ou população textual foi criada. Manter resultados/PDFs
anteriores e distinguir código preparado de processamento real concluído.

## Encaminhamento anterior — versão 3 com orientador (D-028)

Concluído em 06/11: PDF de 45 páginas e pacote Overleaf em
reports/monografia_template_200k_v3/ e ZIP de mesmo nome; PDF em output/pdf/.
Integra objetivos à introdução e resultados ordinal/PCA/sensibilidade, preservando
a regressão e distinguindo regra principal da alternativa posterior. Compilação
e inspeção visual concluídas; fontes/resultados anteriores preservados por hash.
Nenhuma execução pesada necessária. Revisar narrativa e custos dos erros com
Leandro Tavares Correia. Não repetir treinos, cruzamento ou embeddings para revisão.
Guia: execucao_monografia_template_200k_v3.md.

## Etapas concluídas — nova investigação de 04/11 (D-025)

1. Concluído: fixar níveis 20/40 e sensibilidade 40/60 antes de calcular métricas
   categorizadas. Diagnóstico agregado confirma 34.069/30.785/12.681 aceitas.
2. Concluído pelo pesquisador e conferido em 05/11: 31 previsoes, alinhamento e
   suporte aprovados; mínimos 2.381 faixas/1.322 componentes por classe/partição.
   São previsões de regressão categorizadas, não classificação treinada.
3. Concluído pelo pesquisador: 32 v1.1 selecionou 133 consultas para revisão de
   metadados nos caches locais; nenhuma busca nova.
   A tentativa v1 falhou antes da seleção por popularidade textual. A v1.1 cria
   coluna numérica nova e grava em pastas novas, sem apagar registros parciais.
4. Triagem técnica 33 concluída nas 133 fichas; nenhum vínculo alterado. Dos
   quarenta aceitos, 35 metadados compatíveis e cinco candidatos não observáveis.
   Preparação de fichas não é qualidade semântica medida. Propor intervenção apenas
   sobre falhas demonstradas antes de justificar cruzamento integral.
5. Preparação/testes de classificação ordinal concluídos (D-026): quatro blocos
   comuns e PCA como alternativa interna. Smoke real concluído/conferido: 318
   faixas, quatro partes, recarga exata. Primeiro lote real conferido: 1/20 partes,
   Combinado externo 0 em 105,42 s, 24 ajustes internos, sem avisos registrados.
   Produção integral agora concluída/conferida: 20 partes e 480 ajustes internos,
   77.535 probabilidades por variante, sem avisos registrados. Não repetir treino.
   Não alterar coorte/cortes para melhorar desempenho externo. Guia específico:
   execucao_classificacao_ordinal_200k_v1.md. 35 diagnóstico agregado/PCA/figuras
   concluído; relatório interpretacao_classificacao_ordinal_200k_v1.md.
6. Concluído (D-027): pesquisador executou 36, métricas originais reproduzidas.
   37 análise de agregados/cauda delimitada/figuras concluído pelo agente. Compromisso:
   maior BA e recuperação de elevadas, menor precisão e acurácia global. Principal
   preservado; sem adoção automática da alternativa ou novo treino.
7. Próximo: integrar resultados e objetivos à introdução em versão acadêmica posterior,
   preservando todos os PDFs e conclusões anteriores como evidência histórica.
   Apresentar ao orientador as duas regras, limites de inferência e utilidade dos
   erros. Não há processamento pesado necessário pendente para essa consolidação.

Guia operacional: execucao_nova_etapa_niveis_v1.md. Primeira regressão permanece
congelada. Amostragem menor, log1p, ponderação por custo e novo cruzamento integral
continuam condicionados a necessidade científica; não são tarefas disparadas.

## Publicação autorizada — D-024

Concluída: publicação principal 082a9a0 confirmada no remoto privado, com
394 testes locais e lint aprovados. CI aprovada em 9b375a8 após ajuste de sua
dependência Polars. Histórico, selos, modelos e avaliação científica preservados.
Próximo trabalho permanece a revisão acadêmica, sem novo processamento pesado.
Guias atuais: REPRODUCAO.md, HISTORICO_METODOLOGICO.md e PUBLICACAO_GITHUB.md.

## Revisão anterior — relatório no template (D-023)

Usar reports/monografia_template_200k_v2/main.tex: 34 páginas, cinco seções e dois
apêndices científicos; ZIP pronto para Overleaf/XeLaTeX. Revisar com Leandro
Tavares Correia, grafia confirmada. Referências originais conferidas a partir
das indicações de três TCCs da BDM/Ana, sem citar TCCs no .bib. Spotify/LRCLIB,
amostragem/integração e fórmulas ampliados de agregados. Não reabrir modelos.
Versão de 57 páginas abaixo é histórica; guia execucao_monografia_template_200k_v2.md.

## Sequência e critérios (histórico de execução)

**D-022: avaliação principal encerrada/congelada pelo pesquisador.** Monografia
completa compilável já consolidada em reports/monografia_consolidada_200k_v1/,
com main.tex, ZIP e PDF compilado de 57 páginas. Próxima ação é revisão com o
orientador Leandro Tavares Correa e confirmação das pendências documentais do
Apêndice D. Sem novos treinos, LRCLIB ou embeddings em massa. Os registros abaixo
preservam a sequência histórica; não são autorização para repetir etapas.

Atualização após o PDF (02/11): diagnósticos leves 25/26/27 concluídos, com parecer
de fechamento. Nenhum novo ciclo de treino é a próxima etapa. Registrar token de
espaço extra no prefixo E5, descritores reproduzidos, limites condicionais (sem
IC integral), cauda integralmente subestimada e clipping separado. Referência:
reports/parecer_fechamento_metodologico_200k_v1.md e D-021. Não modificar execução
congelada para apresentar conformidade canônica que não foi observada.

| Etapa | Estado e dependência | Critério de saída / próxima entrega |
| --- | --- | --- |
| A — Spotify | Auditoria e amostra concluídas; relatórios/estratos/pesos existentes | Reutilizar descrição e qualidade; não refazer sorteio |
| B — LRCLIB | Dump e índices concluídos, schemas/proveniência documentados | Sintetizar limites por metadados/checkpoints; nenhuma nova varredura integral |
| C — Cruzamento | V2 concluída, diagnóstico v3 executado; aplicação v3 adiada | Fechar integridade e qualidade dirigida dos textos da base candidata; não perseguir cobertura |
| D — Seleção/alcance | Parecer v2 executado; domínio observado aprovado | Manter diagnóstico de catálogo/200k/aceitas/demais; não usar conformidade marginal como qualidade do match |
| Pré-fechamento | Script 17 executado e concluído pelo pesquisador | 77.535 vínculos/hashes verificados; idiomas, duplicatas e colisões históricas quantificados; revisão semântica permanece separada |
| E — Representações | Scripts 19/20 concluídos: 77.535 faixas, 21 descritores, 77.051 vetores de 384 dimensões e zero pendências | Reutilizar tudo; código/protocolos selados preservados. Não repetir inferência |
| F — Modelagem | Ridge 22/diagnósticos 23 concluídos; métricas reproduzidas, ganho em cinco folds e retirada condicional, pesos mantêm ordenação | Preservar comparação; resultados descritivos, sem IC/p-valores. Não retunar por métricas conhecidas |
| G — Monografia | Versão única concluída: 11 capítulos, quatro apêndices, 14 tabelas, oito figuras, 19 referências; PDF TeX de 57 páginas revisado e ZIP | Revisar com orientador e confirmar metadados/modelo institucional; preservar resultados. Dois trechos parciais anteriores mantidos |

## Estratégias comparadas e recomendação

| Estratégia | Evidência / custo / implicação |
| --- | --- |
| Repetir recuperação até mais cobertura | V2 adicionou 144 aceitações; diagnóstico v3 teve ganho ampliado zero. Outro índice/crossmatch integral sem benefício demonstrado não é prioridade |
| Retornar somente à integração LFM2b antiga | Reaproveita descritores/vetores existentes, mas muda universo e não responde automaticamente pela nova amostra. Preservar como resultado histórico/sensibilidade, não impor sua interseção às 77.535 |
| Domínio recente v2, representações sobre os mesmos textos | Recomendado e aprovado quanto ao domínio: preserva amostra e trajetória; precisa de auditoria, representações e validação recente. Não exige representar o catálogo inteiro para comparar incremento preditivo dentro do domínio |
| Filtro só inglês / imputar embeddings / reponderar para catálogo | Alteraria elegibilidade ou pressupostos. Não adotado; política multilingue e eventual ampliação de inferência serão justificadas, não usadas para desbloquear resultados convenientes |

Modelo inicial preparado em 22: referências média/mediana e Ridge como comparação
transparente nas quatro configurações, alpha 0,1/1/10/100/1.000/10.000, solver
LSQR e pré-processamento dentro de cada treino. Grade congelada antes de resultados
externos recentes. Os aditivos
e outros algoritmos implementados pertencem à trajetória histórica e não são
próxima tarefa após o encerramento D-022. A escolha executada de alpha usou os
folds internos; não tratar o desenho aprovado como confirmação independente. D-017: treino com
pesos iguais, MAE não ponderado primário/seleção; RMSE e R² complementares. MAE
ponderado pelos pesos originais apenas como sensibilidade nas mesmas previsões
externas, faixas/folds, sem retreinar. Guardar pesos/estratos para descrição/seleção.
Não presumir correção da disponibilidade textual. Metodologia documentada em
metodologia_modelagem_200k_v1.md, para integrar à monografia.

## Registro da ação anterior — monografia consolidada de 57 páginas

Usar a nova entrada principal e o relatório de consolidação. Capítulos científicos
estão escritos e o parecer 25–27 foi integrado; não aguardar localização de outro
arquivo principal para avançar. Revisar título/texto, matching e alcance com o
orientador, confirmar fonte temporal/versão e requisitos institucionais. As lacunas
não serão preenchidas com dados presumidos. Guia de importação/reprodução editorial
em execucao_monografia_consolidada_200k_v1.md. Nenhum novo processamento pesado.

Os parágrafos seguintes descrevem a sequência já executada, não passos pendentes.

Embeddings integrais concluídos e conferidos: 77.051 vetores de dimensão 384,
77.535 referências, zero pendências, 91.156 janelas até 512. Última retomada
27.352 novos + 49.699 reutilizados em 4.914,39 s; não é tempo total da etapa.
Script 21 executado e revisado: 8,323 s; 77.535 faixas, 21.893 componentes,
zero metadados ausentes/inválidos e grupos separados em cinco testes externos
de 15.507. Script 22 smoke concluído/revisado: 318 faixas, 72 ajustes internos,
quatro blocos/duas referências, reprodução exata, zero avisos, 1,843 s. Gate true.
Integral 22 concluída/revisada: 20 partes Ridge, dez referências, 360 ajustes
internos; última retomada 651,372 s, sem avisos. Seis variantes/mesmos 77.535
casos, cinco contrastes. Redução Combinado/Baseline 0,2374 ponto MAE (2,842%);
ganho sobre Profundo 0,0134. Ponderação preserva ordenação; não há inferência de
catálogo ou significância avaliada. Relatório interpretativo já escrito.

23 executado: 0,608 s, 30 partes/métricas reproduzidas; 116 células publicadas,
77 omitidas por limiares, sem exclusão global. Combinado ganha em cinco folds e
na retirada condicional, mas erro da cauda 80-100 é alto (MAE 29,37/n=128).
Idiomas/gêneros têm exceções; inferência de significância permanece não quantificada.

24 gerou texto/tabelas/quatro figuras usando apenas os agregados pequenos, em
operação leve do agente. Projeto e ZIP overleaf_dominio_observado_200k_v1, TeX
compilado no editor integrado. PDF ReportLab com sete páginas renderizadas e
revisadas. Próximo: integrar ao texto completo, cujo caminho foi solicitado;
preservar ambos os projetos parciais. Não há novo comando pesado imediato.
Eventual inferência exige método declarado, não teste t dos cinco folds. Não
repetir 17–23. Diagnósticos após métricas globais são exploratórios, não pré-registro.

A inferência auxiliar agora foi quantificada em 25 por linearização de perdas
pareadas por componente dentro de cada fold e limites Bonferroni. Ela não cobre
variação integral de seleção/treino. A correção do prefixo é recomendação para uma
futura versão; qualquer decisão de reprocessamento exige justificativa e execução
manual, sem substituir resultados atuais. Nenhum trabalho pesado foi julgado
necessário agora. Próxima entrega: incorporar o parecer/errata à escrita e concluir
caracterização de fontes/integração/referências/limites, identificando o TeX principal.

## Registro da execução 19 — concluída

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\19_preparar_descritores_200k.py"
```

Detalhes históricos em `execucao_descritores_200k_v1.md`; contrato selado em
`contrato_representacoes_200k_v1.md`. Concluído em 361,67 s: 77.051 inputs únicos,
componentes até 186 e zero chaves não resolvidas; descritores finitos e originais/
pesos preservados. Não repetir para continuar nem editar seu contrato congelado.

## Registro da execução 17 — concluída

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\17_auditar_prontidao_200k.py"
```

Entradas confirmadas: amostra/resumo/alocação em
`reports/amostra_spotify_200k_20261031/`; resultado e textos v2 em
`data/derived/private_sample_lyrics_200k_v2/`; atribuições antigas em
`data/processed/split_assignments_v0_1_1.parquet`; metadados de desenvolvimento e
teste antigo em `private_final_development_v0_5/development_matrix.parquet` e
`holdout_features.parquet`; IDs da coorte antiga em
`private_statistical_cohort_v1/development.parquet`. Não carrega popularidade
histórica, modelos ou dump. O trabalho percorre a coorte/textos, portanto é
reservado ao pesquisador mesmo que seja menor que indexação/embeddings.

Logs por etapa/lote, textos em streaming e checkpoint por query_id. Interrompeu?
Repita o comando; entradas/código diferentes bloqueiam reuso. `--limit-texts 100`
permite lote textual limitado, mas não limita as validações/hashes iniciais.
Código de saída 0 = auditoria concluída; 2 = lote parcial; erro de integridade
interrompe e exige diagnóstico, nunca exclusão automática. Completion não congela
coorte nem autoriza treino.

Públicos a enviar/analisar:
`reports/prontidao_dados_200k_v1/resumo_prontidao.json` e
`reports/prontidao_dados_200k_v1/relatorio_prontidao.md`.
Privados, não publicar: `data/derived/private_readiness_200k_v1/state.sqlite` e
`linhagem_aceitas.parquet`. Este último conserva linhas/pesos das aceitas e adiciona
indicadores de colisão; não remove as demais faixas do arquivo de 200 mil.

Os dois agregados já foram analisados; contrato e script 19 foram preparados em
seguida. Revisão dirigida de matching permanece; encoder executado e pesos D-017
aprovados posteriormente. Não é necessário novo planejamento geral nem nova busca.

Fundamento técnico para reutilização da validação: documentação oficial de
[validação com grupos](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)
e [prevenção de leakage no pré-processamento](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage),
consultada em 01/11/2026. Grupos devem ser definidos pela identidade/linhagem do
problema; usar GroupKFold não resolve sozinho composições compartilhadas,
duplicações de texto ou exposição histórica.
