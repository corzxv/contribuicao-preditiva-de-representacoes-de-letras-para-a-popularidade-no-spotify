# Decisões técnicas e científicas

Este é o registro canônico equivalente a `DECISOES_METODOLOGICAS.md` solicitado
na consolidação. Não criar outro histórico paralelo. Contexto em
`CONTEXTO_TCC.md`, estado em `ESTADO_ATUAL.md`.

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
