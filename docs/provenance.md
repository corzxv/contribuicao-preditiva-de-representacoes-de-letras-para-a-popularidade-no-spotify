# Proveniência

## Relatório no template — 02/11/2026 (D-023)

Template_Relatório_TCC.zip e relatorio_tcc_ana.zip fornecidos pelo pesquisador,
somente inspecionados como fontes editoriais; nenhum comando deles foi executado.
Emblema UnB do template copiado para o novo projeto. BDM consultada em três TCCs
de Estatística (10483/41348, 36446, 34267), incluindo bibliografias/passagens e
inspeção visual de páginas. Referências originais conferidas nas editoras/autores;
27 itens no .bib, sem referências a TCCs. Livro Izbicki/Santos original consultado.

Projeto reports/monografia_template_200k_v2, PDF TeX 34 páginas e ZIP; 57 páginas
anteriores preservadas. Script 29 apenas resume JSONs públicos concluídos e
reutiliza tabelas/figuras: duas figuras/uma tabela novas. Hashes de entradas e
gerados em proveniencia_figuras.json; verificação de arquivos/fontes/compilação
em reports/verificacao_monografia_template_200k_v2.json. Sem dados individuais,
dump, encoder, treinamento ou novas previsões. Grafia Leandro Tavares Correia
confirmada explicitamente pelo pesquisador. Revisão descrita em relatório próprio.

## Fechamento metodológico após o PDF — 02/11/2026

Parecer em reports/parecer_fechamento_metodologico_200k_v1.md; novos agregados em
reports/fechamento_metodologico_200k_v1/. Solicitação explícita do pesquisador:
inferência pareada, representações, cauda/clipping e monografia, preservando
resultados e execução manual de tarefas pesadas.

25 concluiu diagnóstico leve em 0,264 s, ligando previsões/perdas aos hashes do
resumo 23 e reproduzindo as perdas por componente. Code/protocol/input hashes
em resumo_fechamento.json. Nenhum treino, leitura de letras, modelo ou encoder.
Limites auxiliares por fold/grupo, família Bonferroni 2×5 por ponderação; não
IC integral da CV. Modelos/folds/previsões originais não foram substituídos.

26 conferiu selos de descritores/encoder e arquivos pequenos do snapshot; oito
textos/168 valores reproduzidos, diferença máxima zero. Primeiro orçamento de
arquivo inteiro bloqueou leitura; passou-se à projeção de 10.154.023 bytes
comprimidos sem elevar o limite. Hash integral de descritores não foi refeito;
evidência anterior é o selo 21. Comparação de tokenizer real revelou token de
espaço ID 6 adicional ao tokenizar prefixo à parte, em 11 frases artificiais e
oito textos. auditoria_representacoes.json registra resultado e escopo, 20,461 s.

27 foi motivado por esse achado concreto: quatro frases artificiais em quatro
idiomas, oito forwards unitários, sequências ≤64 tokens, CPU/duas threads. Hashes
do snapshot completo/pesos novamente conferidos. Cosseno entre receitas 0,996643
a 0,999434; não há medida de impacto no MAE. 20,702 s incluindo carregamento;
zero textos do corpus codificados, zero vetores exportados/cache alterado, zero
modelos treinados. Distinguem-se esses vetores artificiais temporários de novos
embeddings do corpus. Código/protocolos 19–23 preservados; descrição da variante
precisa incorporar o desvio, sem afirmar reprodução exata da receita oficial.

PDF parcial SHA-256 683c55e6f4200ebade2a95574da7e39e98f2158601316759df31df3339063d7d;
ZIP SHA-256 aacc1acf58420f8a1ad8157c273727f2dc7703a3fe36b143624d5bef2d1497c3.
Verificados antes/depois e preservados. Fontes pequenas/hashes/configs e resultados
auxiliares em verificacao_fechamento.json. Testes 17 específicos aprovados, Ruff
check/format e diff --check. Novos comandos são diagnósticos leves, não tarefas
pesadas pendentes; guia execucao_fechamento_metodologico_200k_v1.md.

## Diagnósticos verificados e trecho de monografia — 02/11/2026

Pesquisador concluiu 23 em 0,607611 s: 77.535 faixas, 30 partes/métricas/contrastes
reproduzidos, 21.893 componentes; 116 células publicadas/77 com métricas omitidas.
Código/protocolo 23 e SHA da tabela privada de perdas por componente conferidos
pelo agente, sem repetir análise integral. Foi lido somente o conjunto pequeno
de agregados para interpretação: ganho Combinado/Baseline nos cinco folds,
estabilidade condicional por componente, alto erro em 80-100 e exceções de idioma/gênero.

Script 24 executado pelo agente apenas sobre agregados públicos: 696 linhas,
quatro figuras PNG/SVG, seis tabelas e trecho parcial de métodos/resultados/discussão.
Novo projeto criado com create_latex_project, main.tex compilado duas vezes com
sucesso pelo editor integrado. ZIP 28 arquivos com CRC/proveniência conferidos,
sem modelos, letras, bases ou previsões individuais. Pacote histórico preservado.

PDF de leitura criado com ReportLab do runtime fornecido, sem instalar dependências
no venv. Sete páginas finais renderizadas por Poppler e visualmente inspecionadas;
ajustados espaçamento das tabelas e legenda para eliminar parágrafo órfão/sobreposição.
Esse PDF não é exportação da compilação TeX, distinção explícita no pacote.
Fonte compartilhada em manuscrito.json; verificação/hashes em
reports/verificacao_publicacao_200k_v1.json. Referências primárias JMLR consultadas,
sem alterar estimando/grade/pesos/folds ou calcular IC. Caminho da monografia
completa solicitado para integração; encontrados no repositório apenas pacotes parciais.

## Conclusão Ridge e preparação dos diagnósticos — 02/11/2026

Pesquisador concluiu 22 all: completed=true, 20 partes Ridge, dez referências,
zero pendências, 77.535 previsões por variante, seis variantes e cinco contrastes.
Última retomada 651,372291 s, 19 partes novas/uma reutilizada. Agregados lidos
e conferidos, sem refit: 360 metadados de ajustes internos com assinatura válida,
máximo 352 iterações, zero avisos. Trinta modelos/arquivos de previsões verificados
por hash/footer, 15.507 linhas por parte; arquivo global 77.535 linhas/hash
4e9bc8839ceb76bef0248e328217dc362c5ee894479731e43de401fb0ffaf448.
Não foram desserializados modelos ou repetidas predições pelo agente.

Código/protocolo/utilitários e assinatura 34e5e6e0b46462ec2bafe4aa9e05769c254c1bf00792debdc07170e3ee3682b9
preservados. MAEs 8,352484/8,295691/8,128523/8,115122; ganho conjunto 2,842%,
ponderado 2,781%, mesma ordenação. Texto inicial interpretativo escrito em
reports/interpretacao_modelagem_200k_v1.md; sem afirmações de significância.

Preparado 23 para auditoria de todos os vínculos/partes/valores e diagnósticos
condicionais às previsões fixas: folds, subgrupos e influência de componentes.
Sem treino/retuning/encoder/IC/p-valores; novo protocolo depois da leitura das
métricas globais, antes dos erros de subgrupos. Escopo exploratório explícito,
status histórico desconhecido preservado. Execução real reservada ao pesquisador.
Código/protocolo 19–22 não foram editados. Fonte primária de cautela sobre variância
de CV consultada em 02/11: Bengio/Grandvalet (2004), link no protocolo 23.
Verificação da preparação: dez testes aprovados (4 resultados/6 regressão),
Ruff check/format, diff --check e help de 23. Fixtures de 40 observações sintéticas;
sem modelos desserializados/ajustados no diagnóstico e sem tocar fontes reais.
Controle de histórico desconhecido e componentes expostos distinto da ausência
de detecção. Diagnóstico real continua pendente de execução manual.

## Primeiro lote de produção Ridge e retomada — 01/11/2026

Pesquisador executou 22 all --limit-outer-blocks 1: completed=false por limite,
1/20 partes Ridge concluída, 19 pendentes, 67,774910 s. Combinado externo 0,
treino 62.028/avaliação 15.507, 18 ajustes internos e refit; duas referências
também salvas. Resumo/relatório lidos, sem métricas globais parciais disponíveis.

Inspeção limitada do agente: 18 metadados de ajustes confirmados no SQLite,
assinaturas válidas, máximo 352 iterações e zero avisos de fit/predição internos.
Hashes/footers dos três modelos/arquivos de previsões conferidos, 15.507 linhas
por parte; sem desserializar modelos ou carregar matrizes reais para treino.
Código/protocolo/utilitários e gate preservam assinatura anterior
34e5e6e0b46462ec2bafe4aa9e05769c254c1bf00792debdc07170e3ee3682b9.

Próximo comando manual: 22 all sem limite para completar 19 partes, reutilizando
o lote. Extrapolação condicional: 19 × 67,774910 / 60 = 21,462 min se o custo por
parte se mantivesse. Diferentes blocos/folds/carga podem mudar duração; não é
limite garantido nem intervalo estatístico. Nenhuma escolha por desempenho
externo/sensibilidade ou alteração dos selos, grade, pesos e folds nesta revisão.
Dois testes leves de métricas/isolamento do alvo externo aprovados com fixtures
sintéticas; Ruff e diff --check aprovados. Nenhum treino real pelo agente.

## Smoke Ridge real aprovado e primeiro lote preparado — 01/11/2026

Pesquisador executou 22 smoke. Agregados: completed=true, used_rows=318, quatro
partes Ridge e duas referências, 1,842557 s, reload_max_abs_difference=0,0,
global_metrics_available=false. Treino externo do smoke 251/avaliação 67.
Checkpoint possui 18 ajustes por bloco (72 internos), máximo 109 iterações,
zero avisos de fit/predição internos. Modelos/previsões dos seis artefatos
conferidos por SHA/footers; nenhum modelo foi desserializado pelo agente.

Assinatura 34e5e6e0b46462ec2bafe4aa9e05769c254c1bf00792debdc07170e3ee3682b9;
gate verified=true e código/protocolo/utilitários selados conferidos inalterados.
Não houve novo treino ou inferência pelo agente; inspeção limitada a agregados,
72 metadados de ajustes, manifests/hashes pequenos e footers das previsões.
Não interpretar tempo/erros do smoke como desempenho/duração integral. Próximo
comando manual: 22 all --limit-outer-blocks 1, Combinado externo 0, para custo
na coorte real; permanece parte definitiva com checkpoint, sem alterar grade,
pesos ou folds. Produção ainda não iniciada na conferência.
Revisão: seis testes de regressão com fixtures sintéticas aprovados novamente;
Ruff check/format --check e diff --check aprovados. Nenhum arquivo selado de
código/protocolo foi editado para atualizar este status.

## Base/folds reais e preparação Ridge — 01/11/2026

Script 21 executado manualmente e concluído: 8,323 s, 77.535 faixas, 77.051 vetores
auditados em dimensão/finitude/hash/norma; erro máximo L2 5,96e-8. 21.893 componentes,
maior 186, 15 campos Baseline e 21 descritores, zero células inválidas/ausentes.
Cinco testes externos de 15.507/treinos 62.028; quinze avaliações internas de
20.676/treinos 41.352. Auditorias de separação e pesos aprovadas. Modelos ainda
não treinados. Resumo/CSV/relatório lidos pelo agente; footers de base/folds
77.535, rejeitados 0, código/protocolo 21 conferidos inalterados. Não reexecutou
montagem, auditoria vetorial integral ou grupos reais.

Preparado script 22 para Ridge pareada com CV já fixada, quatro blocos e duas
referências. Grade/protocolo documentados antes de resultados externos recentes;
reuso de fit_checked/predict_checked da infraestrutura anterior sem executar
modelos históricos. Checkpoints por ajuste interno e parte externa; smoke
separado com reprodução, depois custo de Combinado externo 0 e escala manual.
Saídas privadas novas e fonte 21 imutável; nenhum encoder, vetor novo ou treino
real executado pelo agente. Decisão D-018 e guia execucao_regressao_200k_v1.md.
Verificação: 29 testes aprovados (6 regressão, 7 base/folds, 8 encoder sintético,
4 descritores, 4 consolidação), Ruff check/format, diff --check e help de 22.
Fixtures de regressão têm 40 observações sintéticas; testes verificam isolamento
do alvo externo, aprendizado só no treino, pesos apenas na avaliação, cobertura
comum, cache/reprodução, interrupção e corrupção de artefato. 21 continua com
código/protocolo inalterados; outputs reais apenas inspecionados por metadados.

## Embeddings integrais e preparação da base/folds — 01/11/2026

Execução manual do script 20 concluída após pausa/retomada: resumo integral
completed=true, 77.051 inputs/vetores, 77.535 referências, dimensão 384, zero
pendências, 91.156 janelas, máximo 512 tokens. Última retomada: 27.352 novos e
49.699 reutilizados, 4.914,388 s (não tempo total acumulado). Selo anterior
b8650aeb590949b648f2ddd223d5f16493bafbcb6038af542b9473c0addd3914 preservado.

Agente leu agregados, metadados dos três Parquets e contagem/flags do SQLite:
77.051 vetores, smoke_verified=true, código/protocolo e utilitários com mesmos
hashes. Amostra técnica limitada a oito vetores: dimensão/finitude/hash/norma
aprovados, maior erro L2 5,96e-8; oito vínculos índice/coorte concordantes. Isso
não é auditoria independente integral nem certificação semântica/preditiva.
Não foram lidas letras, carregados pesos do encoder ou repetidas inferências.

Ponderação aprovada explicitamente pelo pesquisador em D-017, seis condições;
texto para monografia em metodologia_modelagem_200k_v1.md. Implementado script
21 para auditoria completa dos vetores/vínculos existentes, base preservando
originais, resposta/15 model_* novos e folds agrupados comuns 5×3 sem usar alvo.
Manifesto explicita quatro blocos e política de pesos; nenhum ajuste estatístico
ou treino nesta preparação. Novo protocolo separado dos selos de 19/20.
Execução real do script 21 aguarda pesquisador; testes só com fixtures pequenas.
Verificação: 23 testes aprovados (7 base/folds, 8 encoder sintético, 4 descritores,
4 consolidação), incluindo preservação de originais, invariância à ordem/alvo,
teste externo fora da CV interna, colisões de identidade, corrupção vetorial,
índice desalinhado e bloqueio de protocolo divergente. Ruff check/format,
diff --check e help do script 21 aprovados. Selos 19/20 conferidos inalterados.

## Primeiro lote real de embeddings e retomada — 01/11/2026

Pesquisador executou script 20 all --limit-texts 1000. Resumo de integral/ lido:
completed=false por limite, 1.000 novos, 24 reutilizados, 296,253 s; 76.027 inputs
pendentes dos 77.051. Exportação parcial: 1.055 referências de faixas, dimensão
384, 1.246 janelas acumuladas, max_input_tokens=512; sem erro registrado. Não
confundir as 1.055 faixas com os 1.024 textos/vetores únicos. Nenhum fold/treino.

Inspeção limitada, somente leitura, do checkpoint confirmou 1.024 vetores sob o
mesmo selo b8650aeb590949b648f2ddd223d5f16493bafbcb6038af542b9473c0addd3914,
smoke_verified=true e hashes dos quatro arquivos de código/protocolo preservados.
Não foram lidos corpos de letras/vetores nem pesos carregados pelo agente.
Extrapolação operacional: 76.027 × 296,253 / 1.000 / 3.600 = 6,256 h restantes.
Reserva sugerida 6–8 h nas mesmas condições; não é intervalo estatístico nem
garantia. Lote segue a ordem da fonte, não amostragem probabilística. Continuação
manual preparada via all sem limite, reutilizando todo o checkpoint.
Revisão com oito testes específicos em fixtures/encoder sintético aprovada;
Ruff e diff --check aprovados. Nenhuma geração real foi executada pelo agente.

## Smoke real multilingue — 01/11/2026

Pesquisador executou o script 20 smoke após download manual. Agregados em
`reports/embeddings_multilingues_200k_v1/smoke/`: completed=true, 24 vetores novos,
dimensão 384, 68 janelas, 55,261 s, max_input_tokens=512, diferença máxima de
reprodução=0,0. Selo b8650aeb590949b648f2ddd223d5f16493bafbcb6038af542b9473c0addd3914.
Leitura limitada dos 24 metadados do SQLite confirmou cobertura dos tokens em
todas as janelas e máximo de 9.193 tokens de conteúdo por texto. Não foram lidas
letras/vetores nem carregados pesos pelo agente nesta revisão.

O aviso de sequência longa veio da tokenização integral antes das janelas;
entradas efetivas respeitaram 512. A nota do tokenizer fast é informativa.
Código, protocolo e configurações selados permanecem preservados para retomada.
Próxima execução manual proposta: all --limit-texts 1000, parte da geração
definitiva, para medir custo antes da continuação integral. Não extrapolar precisão
semântica/preditiva nem duração total a partir deste teste dirigido a extremos.

Revisão do agente: smoke_verified=true no checkpoint; hashes dos quatro arquivos
do selo (implementação, protocolo e dois utilitários) conferem, sem alterações.
Oito testes específicos aprovados com encoder sintético; Ruff e diff --check
aprovados. Testes usaram diretório temporário novo dentro do projeto após o
temporário padrão do sandbox recusar criação; não houve inferência real pelo agente.

## Descritores reais e preparação do encoder — 01/11/2026

Resumo manual do script 19 lido e reconciliado com agregados: completed=true,
77.535 faixas, 77.051 inputs únicos, 484 reusos, 21 descritores, 21.893 componentes,
maior 186, chaves não resolvidas=0, campos/pesos preservados, 361,667 s. Nenhum
embedding/split/modelo foi gerado nessa execução. Fonte em
`reports/descritores_textuais_200k_v1/`; não reexecutada pelo agente.

Script 20 preparado para download explícito e inferência local E5 small multilingue,
commit 614241f622f53c4eeff9890bdc4f31cfecc418b3 verificado na página oficial do
repositório. Manifesto de arquivos/hashes será produzido no download manual, sem
transferir letras. Não se afirma ter baixado/carregado/testado pesos reais nesta
preparação; testes usam arquivos e encoder sintéticos. Configuração e limites em
`docs/protocolo_embeddings_multilingues_200k_v1.md`, decisão D-016.

O contrato textual/código do script 19 permanecem congelados com seus hashes
originais. A nova etapa usa protocolo separado e cache privado novo, reaproveita
normalização/janelas/agregação e integridade vetorial, preservando os artefatos
antigos. Qualidade do matching e ganho preditivo ainda não são medidos pelo smoke.

## Auditoria real 17 e preparação dos descritores — 01/11/2026

Execução manual confirmada em `reports/prontidao_dados_200k_v1/`: completed=true,
77.535 textos/referências verificados, 18,787 s, sem alvos históricos/modelos/SSD.
Foram lidos os agregados e quatro metadados de exceção (artista `!!!`), sem
reprocessar o corpus pelo agente. 484 registros excedentes compartilham texto
estrito; 16 textos ligam artistas operacionais diferentes; 421 IDs, 438 composições
e 7.162 artistas operacionais colidem com o teste v0.6. Categorias se sobrepõem.

Desenho CV agrupada aninhada 5×3 aprovado pelo pesquisador, D-015; folds ainda
não produzidos. Preparado script 19 para descritores do próprio texto e componentes,
usando normalização textual e infraestrutura existentes. Originais mantidos, cache
por hash normalizado e selos de fonte/código/contrato. Nenhum vetor ou modelo novo
foi gerado. Candidato de encoder multilingue documentado com fonte oficial; sem
download, revisão congelada ou validação de desempenho em letras nesta rodada.

## Consolidação e continuidade — 01/11/2026

Reconciliados resumos existentes, schemas/footers e poucos metadados de fontes,
índices, experimentos e LaTeX. Não reexecutados matching, testes estatísticos reais,
descritores, embeddings ou treino. Estado Git pessoal preservado. Nenhum movimento,
exclusão, cópia de base/dump, commit ou push. Inventário limitado de metadados em
`reports/inventario_projeto_20261101.json`; autoridade de classificação e dependências
em `docs/MAPA_ARTEFATOS.md`. Contexto científico consolidado em `CONTEXTO_TCC.md`;
decisão aprovada sobre domínio observado em D-014 (`decisions.md`).

Confirmações: v2 77.535/200.000, diagnóstico v3 de 1.000 sem aplicação integral;
parecer v2 completo; v0.6 status complete, teste aberto 14/10/2026, n=2.592;
coorte antiga de 58.633 stage verified, 50 modelos externos e reprodução exata
segundo verification.json. Essas evidências foram lidas, não recalculadas.
Modelos binários não foram desserializados e alvos históricos não foram carregados.

Script 17 prepara auditoria manual de integridade/linhagem da base recente, ainda
pendente em dados reais. Não importa descritores LFM2b/vetores por ID, congela
população ou define novo teste. Entradas são locais C:, com hashes e checkpoint;
alvos históricos excluídos das projeções Parquet. Análise por idioma continua
estimativa do detector, sem exclusão automática. Próximo comando e critérios em
`PLANO_EXECUCAO.md`. Nenhuma alegação de suficiência preditiva pelo tamanho.

## Preparação v3 e parecer estatístico — 01/11/2026

Inspecionados resumo/schema/código v2 e agregados do catálogo/amostra; não executada
recuperação ou análise real. V2 completa disponível em
`data/derived/private_sample_lyrics_200k_v2/resultados_faixas_200k.parquet`;
comparação auditada `reports/amostra_spotify_200k_20261031/comparacao_catalogo_amostra_200k.csv`,
com hash no resumo amostral. Este agregado fornece referências populacionais sem
reler catálogo bruto ou abrir SSD. Ano é reconstruído da distribuição de contagens
anuais; bandas 80–89/90–100 da distribuição de popularidade inteira.

Novos scripts 15/16 e módulos lyrics_evaluation/lyrics_statistical_opinion usam
infraestrutura anterior sem alterar fontes. Novos resultados/pareceres têm selos,
diretórios e escopos distintos. A avaliação diagnóstica registra probabilidades
próprias, sem mudar pesos do estudo. Referências verificadas em fontes primárias
ou páginas institucionais/editoriais; links e princípios nos dois protocolos v3.
Não se implementa modelo probabilístico Fellegi–Sunter nem se atribuem margens
locais à literatura. Sem afirmações de ganho, precisão ou adequação real antes
da execução manual.

## Preparação da recuperação local v2 — 31/10/2026

Resumo real v1 localizado em `reports/busca_local_200k_20261031/`, concluído em
31/10/2026: 77.391 aceitas, 25.775 ambíguas, 88.049 não encontradas, 8.748
instrumentais, 10 sem texto e 27 insuficientes, sem erros/pendências. Estado
`data/derived/private_sample_lyrics_200k_v1/state.sqlite`: 6.203.969.536 bytes,
WAL ausente na inspeção. Schemas confirmados: meta/queries/tracks/evidence/lyrics/runs;
Parquets com 200.000 faixas e 77.391 consultas aceitas. SHA-256 da amostra no resumo:
`cbaf98e2771067ab70538068d85b029ce77fbcdfb86e8b35f34a2a7abf46faff`.

Foram lidos os módulos efetivamente usados de normalização, consulta, diagnóstico,
fingerprint/representante, protocolo e desenho, além de poucos metadados de
créditos/títulos. Não foram processadas as 200 mil faixas, reconstruídos índices,
varrido o dump ou consultadas letras remotas. O diagnóstico completo das perdas
e os ganhos v2 serão produzidos na execução manual, não inferidos dos exemplos.

Novo script 14 reutiliza validação/estado/exportação/comparações v1 e infraestrutura
SQLite local. Estado novo `data/derived/private_sample_lyrics_200k_v2/`, índice
`D:\TCC_LRCLIB\tcc_lookup_sample_200k_v2/`, agregados
`reports/recuperacao_letras_200k_v2/`. Dump, índices e estado/resultados v1 não
recebem escrita. O selo v2 registra hashes de entradas/código/protocolo, hash e
metadados do estado anterior, fonte, detector e destinos. Proveniência privada
distingue herança v1, reavaliação de cache e consulta local nova, incluindo
representações originais e texto derivado de sincronização validada.

Regras e produtos em `docs/protocolo_recuperacao_letras_200k_v2.md` e
`docs/execucao_recuperacao_letras_200k_v2.md`. Nenhuma contagem de recuperação ou
tempo v2 real é afirmada nesta preparação.

## Preparação da busca local da amostra 200k — 31/10/2026

Entradas confirmadas: amostra/resumo/alocação em
`reports/amostra_spotify_200k_20261031/`; dump
`D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`; índice
`D:\TCC_LRCLIB\tcc_lookup_v1\lookup.sqlite`; manifesto antigo
`data/derived/private_local_lyrics_v1/state.sqlite`. Foram lidos código, schema,
metadados/checkpoints e footer da amostra; nenhuma consulta de letra real ou
varredura do dump foi executada nesta preparação.

Dump: 261.755.867.136 bytes; SHA-256 registrado na preparação anterior
`e8682b6f1807ca0671e6ae8206dd60f0363f70ca67d352a4ddecbe896500c0d3`.
Checkpoint pronto com CRC e quick-check aprovados. O selo do índice referencia
esse dump; progresso completo em 28/10/2026: 33.714.178 percorridos e 12.757.266
indexados. A diferença decorre do filtro por artistas normalizados do manifesto
antigo, sem filtro de idioma/presença de texto. Não garante cobertura universal.

A nova CLI validará hashes da amostra/alocação, selos de fonte e conjunto de
artistas; o suplemento será `D:\TCC_LRCLIB\tcc_lookup_sample_200k_v1/`.
Estado/textos novos: `data/derived/private_sample_lyrics_200k_v1/`, ignorados pelo
Git. Agregados: `reports/busca_local_200k_20261031/`. Cache antigo não fornece
aceitações; resultados desta execução têm consulta, fonte, IDs/revisão LRCLIB,
regras, evidência, hashes de texto e representante registrados privadamente.

Detector `langid` 1.1.6 disponível localmente, modelo embutido com SHA-256
`e2d675b6d0f511cbb5317b4770c9289754b7338dec97fce660ff09c91b3d95a7`;
nenhum download. O resumo da execução registra versão/hash efetivos ou ausência
do detector. Protocolos: `docs/protocolo_busca_local_200k.md` e
`docs/execucao_busca_local_200k.md`. Cobertura e tempo reais ainda não observados.

## Preparação da amostra 200k — 31/10/2026

Referência localizada nos três produtos em
`reports/auditoria_catalogo_spotify_20261031/`: Markdown, resumo JSON e CSV longo.
O JSON registra execução com status concluído, iniciada em
`2026-10-31T15:16:02.720898+00:00`, CSV `data/raw/spotify/spotify_data.csv`, 175.822.041 bytes,
SHA-256 `42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897`,
1.159.764 linhas/IDs distintos, 499 faixas ≥80, gêneros em 82 células distintas
e anos 2000–2023. São resultados da auditoria existente, não recontagem feita
na preparação da amostragem. O código manual verificará o hash e reconciliará
as contagens antes de sortear; nenhuma amostra real foi gerada nesta preparação.

`scripts/12_sortear_amostra_spotify_200k.py` produz novo Parquet com originais
textuais e campos adicionais de desenho, alocação e agregados. O JSON de execução
registra hashes de entrada, auditoria, código, protocolo, regras e saídas, versões,
seed e hash dos IDs selecionados. Dados individuais continuam locais e ignorados
pelo Git; não há aquisição externa ou leitura do LRCLIB. Protocolos e convenções
estão em `docs/plano_amostral_200k.md` e `docs/execucao_amostra_spotify_200k.md`.

## Spotify_1Million_Tracks

- Página: https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks
- Slug: `amitanshjoshi/spotify-1million-tracks`
- Arquivo observado: `spotify_data.csv`
- Tamanho: 175.822.041 bytes
- SHA-256: `42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897`
- Aquisição: API pública Kaggle, ZIP `spotify-1million-tracks.zip`, em 2026-08-18 UTC
- Licença observada na API/página oficial: “Database: Open Database, Contents: © Original Authors”
- Última atualização informada pela API: 2023-06-21T12:27:55.677Z

## LFM2b Lyrics Descriptor Analyses

- Registro: https://zenodo.org/records/10938615
- DOI: `10.5281/zenodo.10938615`
- Arquivo: `full_dataset.json.gz`
- Tamanho: 690.455.174 bytes
- SHA-256: `0a7c3d52584c4f726fb4e06e62ce36f00ff1b428811561409e6941df8428d106`
- MD5 publicado pelo Zenodo: `9c2aab67c8228a6238a7c2c030d6bef1`
- Aquisição: link de conteúdo oficial Zenodo em 2026-08-18 UTC
- Licença confirmada pela API Zenodo: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

O registro oficial descreve `popularity` como visualizações da letra no Genius e `lfm_playcount` como eventos de escuta LFM-2b. O arquivo oferece descritores derivados das letras; esta pipeline não afirma que contenha letra integral.

O manifesto legível por máquina fica em `data/raw/manifest.json` e não é versionado porque pertence à camada de dados local.

## Revisão documental — auditoria do catálogo original, 31/10/2026

O arquivo anterior ao matching foi localizado em
`data/raw/spotify/spotify_data.csv` (175.822.041 bytes; somente cabeçalho e
metadados inspecionados nesta preparação). Os 1.159.764 registros são uma
contagem histórica documentada, ainda não recontada no CSV nesta etapa.

**Ressalva à data de aquisição acima:** o manifesto registra
`obtained_or_verified_at: 2026-08-18T01:54:30.425097+00:00` e método
`reused_existing_configured_file`. Isso comprova registro de verificação/reuso;
a data efetiva do download é **não confirmado**. Número de versão Kaggle, data
de coleta da popularidade e significado preciso de `year`: **não confirmado**.
Última atualização da API não é data de coleta. Licença e hash acima são
evidências históricas locais, sem nova consulta remota ou hashing do dado bruto
nesta preparação.

`scripts/11_auditar_catalogo_spotify.py` lê exclusivamente o CSV indicado por
`--input`, preserva originais e cria apenas agregados/temporários na pasta nova.
Não usa a interseção LFM2b nem abre LRCLIB. A execução manual registrará hash,
contagens observadas, regras e hashes do código/configuração em JSON. Detalhes,
transformações implementadas em etapas anteriores e limitações em
`docs/auditoria_catalogo_spotify.md`.

## Derivados locais — Base v0.1.1

- Fonte imutável: `data/processed/modeling_base_lfm_v0_1.parquet`
- SHA-256 da fonte antes e depois da execução: `7a0c15c905081fb7fe672478513d706c40fbd709d2af4077173803484a02ab59`
- `data/processed/modeling_base_lfm_v0_1_1.parquet`: 69.544.162 bytes; SHA-256 `1c28f31e9b466b76d7e0180b769ba7ac51c46d2590ad7b1ba1ed21eaebdd1c5c`
- `data/processed/split_assignments_v0_1_1.parquet`: 11.322.914 bytes; SHA-256 `4b0ff5a0e9be21af15607b9bbced423c99247c7d1aaa9615635baf134b86856b`
- `data/processed/matching_audit_v0_1_1.parquet`: 14.614.968 bytes; SHA-256 `3b7b9a2145b91ce7c47ac85ef61c17784b7a371633e494b6bac34fb85b54c346`
- `reports/feature_manifest_v0_1_1.csv`: 159.893 bytes; SHA-256 `f2dd09defb9bbe383e3c189b65f836a5ba4906e090b472e2604cba388a243d42`
- `reports/match_review_sample_v0_1_1.xlsx`: 77.540 bytes; SHA-256 `d7cef88b58cb9c0707f04146b88307bacfc8c1395786f3e7fd2400bd7f039953`

Os Parquets v0.1.1 e demais derivados volumosos continuam ignorados pelo Git conforme as regras do projeto. A configuração executável está em `configs/modeling_v0_1_1.yaml`; o resumo de execução e os detalhes de ambiente estão em `reports/run_summary_v0_1_1.json`.
