# Proveniência

## Classificação concluída — D-045

Foram reconciliados os selos da amostra, código e checkpoint, as divisões
agrupadas, os 482 novos vetores e os 240 ajustes internos. As 25 partes
externas incluem quatro modelos e uma referência por divisão. As métricas
publicadas foram reproduzidas das probabilidades das 9.526 faixas.

## Classificação das 9.526 faixas — D-044

57 verifica o hash da candidata v2, do catálogo e dos sete arquivos de texto.
As letras são ligadas pela consulta e hash bruto. Os 9.018 vetores
compatíveis foram localizados pelo hash do texto normalizado e conferidos
com o selo do E5. A preparação real conferiu metadados e componentes com
suporte para a avaliação agrupada. Ajuste validado com dados sintéticos.

## Candidata ampliada — D-043, 13/11/2026

O resultado de 55 foi confrontado com as 22.443 chaves do checkpoint e os
179 textos dos Parquet e do dump LRCLIB. 56 usou as fontes seladas de 52, 53 e
55, além do catálogo selado para os metadados de 53. A candidata v2 registra
os relatórios dos complementos, as fontes textuais, o script e os agregados
com seus hashes em reports/amostra_com_letras_candidata_v2.

## Revalidação histórica e triagem por gênero — D-042, 13/11/2026

53 conferiu os caches indicados pelo estado histórico somente leitura. Os
hashes individuais e os desfechos constam no `decisoes.json` privado. 54
comparou o catálogo original com os IDs já sorteados e as listas seladas
de artistas dos índices LRCLIB. Os resumos em reports/revalidacao_cache_historico_v1
e reports/triagem_generos_deficitarios_v1 registram as fontes e contagens.
55 passou em teste de retomada e a execução real está pendente.

## Candidata completa com letras — D-041, 07/11/2026

52 verificou o Parquet histórico de modelagem, o sorteio inicial e o manifesto
consolidado. Os 682 IDs comuns foram reconciliados pelos 12 metadados numéricos,
gênero e hash da letra. As 9.526 referências sorteadas foram conferidas nos
seis Parquet de textos selados, com rehash dos textos selecionados. Os
agregados, as fontes e os selos estão em reports/amostra_com_letras_candidata_v1.

## Revisão de limites e recuperação consolidadas — D-040, 07/11/2026

50 real concluído pelo pesquisador. O agente reconciliou as 40 consultas e
os desfechos com o estado 43, conferiu os hashes dos dois Parquet e verificou
os 25 originais com leituras pontuais por ID no dump. A etapa 51 confrontou
todos os campos das 9.526 faixas com o sorteio selado, verificou os hashes
dos arquivos de origem e combinou os vínculos disjuntos por faixa e consulta.
O manifesto privado registra apenas referências e hashes textuais. O resumo
de 51 sela o manifesto, os agregados públicos, o código e os resumos de origem.

## Piloto online conferido e revisão de limites preparada — D-039, 07/11/2026

O checkpoint do piloto 49, manifesto, código e resumo foram reconciliados.
As 100 respostas HTTP 200 e os desfechos estão em
reports/piloto_online_nova_amostra_v1/verificacao_resultado_piloto.json. O agente
inspecionou sete casos do limite local por chave, somente metadados. A etapa
50 mantém os vínculos selados e registra os novos em complemento. Oito testes
e fluxo de retomada com consultas simuladas aprovados. Execução real pendente.

## Piloto online preparado — D-038, 07/11/2026

O universo do piloto parte das faixas sem candidato no estado selado de 43
e exclui as nove aceitas da revisão 48 por `track_id`. As 100 seleções estão no
manifesto privado, SHA-256 e98bb4bd33e3db67e31744708a4217237193acfd341cf105eb2d83f698552b9c.
A preparação foi reproduzida duas vezes com o mesmo manifesto. Nove testes
e um fluxo com respostas HTTP simuladas verificaram o checkpoint, a retomada,
os limites e a separação dos desfechos. A coleta real está pendente.

## 47 e 48 reais — D-037, 07/11/2026

47 concluído pelo pesquisador. As 58 aceitações conferem por consulta, faixa,
IDs LRCLIB e hashes dos textos registrados no checkpoint 43. O complemento
de 46 e os campos do sorteio selado foram reconciliados. Em 48, o agente
registrou 13 decisões documentais com as fontes de catálogo e executou nove
consultas pontuais por IDs selecionados. Os quatro casos inconclusivos
permanecem nas pendências. Conferidos os três complementos e o resultado 43.
As fontes documentais individuais ficam na pasta privada de 48. As tabelas
públicas apresentam cobertura e diferenças de metadados agregadas.

## 46 real e preparação de 47 — D-036, 07/11/2026

46 concluído pelo pesquisador. Conferência do agente reconciliou o checkpoint
de 831 decisões, os 130 vínculos adicionais, os hashes dos textos originais,
o estado 43 e todos os campos do sorteio selado. A cobertura foi recalculada
com os status combinados e publicada em cobertura_pos_revisao_caixa_nova_amostra_v1.

47 usa as evidências de 43 para consultar somente por ID as 1.457 referências
dos candidatos elegíveis nas 108 consultas. O diagnóstico de 12 consultas
confirmou cinco aceitações pelo critério em memória. Quinze testes leves dos
módulos 43, 46 e 47 e Ruff passaram. Guia execucao_revisao_caixa_plain_lrc_nova_amostra_v1.md.

## 44/45 reais e preparação de 46 — D-035, 07/11/2026

44 real conferido por resumo, hash e agregações SQLite limitadas. 45 projetou
metadados de 9.526 faixas em 1,56 MB e reconciliou os campos com o sorteio.
Gerou estatísticas de 12 variáveis, cobertura dos 82 gêneros, figura PNG/SVG e
16 fichas privadas para 13 consultas. Origem e hashes em resumo_consolidacao.json.
Conferência pontual de campos dos 16 registros e doze casos textuais no SSD.
Cinco casos coincidiram após uniformização de caixa, espaços e tipografia.
46 preparado com índices existentes e gravação incremental dos textos originais.
As saídas da execução real serão conferidas após o processamento manual.

## 43 real e diagnóstico de metadados — D-034, 06/11/2026

43 concluído pelo pesquisador, 41,7926 s/3.162 consultas: 3.647 aceitas (+2.222),
1.298 ambíguas, 4.164 sem candidato, 416 instrumentais e uma sem texto. Sem
erro, rebuild, amostra nova ou perda de aceitas/instrumentais anteriores.
Hashes privados/públicos e código do resumo conferidos. Agregações SQL leves
reconciliaram motivos/transições; cobertura por gênero/período/popularidade
analisada somente nos agregados. Estado inteiro não foi reavaliado pelo agente.

Inspeções limitadas: doze consultas sem candidato por metadados, oito consultas
com textos concorrentes por acesso pontual. Índices nativos tracks.name_lower,
artist_name_lower e FTS5 verificados por schema/EXPLAIN. FTS usa índice virtual
e PK do registro; nenhum scan de 33 milhões ou rehash do dump. Um exemplo &/and
documentado como indício; nenhum vínculo aceito por ele.

44 preparado/testado em SQLite sintético (três testes), execução real manual
pendente. Metadados/candidatos privados e agregados públicos separados. Não lê
letras ou altera 43; suas categorias são sugestões, não identidades validadas.
Guia execucao_diagnostico_chaves_nova_amostra_v1.md. Sem treino/embedding/PDF/Git.

## 42 real e auditoria dos bloqueios — D-033, 06/11/2026

42 concluído pelo pesquisador em 1.422,90 s, 7.977 consultas novas e 780
negativas completas reaproveitadas. Complemento real para 2.367 artistas.
Contagens finais: 1.425 aceitas, 362 instrumentais, 3.574 ambíguas, 4.164 sem
candidato e uma sem texto, zero erro/pendência. Caches/monografias anteriores
permanecem. Estado 42 inspecionado por SQL agregado e acessos limitados.

Auditoria revelou 2.139 bloqueios de plain/LRC e 1.176 por versões (1.023 com
elegível). Dez consultas determinísticas de plain/LRC inspecionadas por IDs,
hashes contra evidência 42 e igualdade exata após whitespace/tipografia: 10/10,
sem extrapolar proporção ou divulgar letras. Também inspecionados metadados de
quatro conflitos de versão com elegíveis. Sem varredura, API ou novo índice.

43/lyrics_matching_revision.py preparado, quatro testes sintéticos aprovados.
Reavaliação real manual pendente; 3.162 alvos, resultados separados. Plano
explicita duas mudanças e mantém origem, textos e resultados 42 intactos.
Guia revisao_bloqueios_vinculacao_v2.md. Nenhuma aceitação real nova pelo agente.

## Cache real e preparação da busca local — D-032, 06/11/2026

41 concluído pelo pesquisador, resumo real com 9.526 consultas/30,3247 s:
682 aceitas, 87 instrumentais, 8.757 pendentes, zero erros ou metadados
insuficientes. Três Parquets/duas tabelas e fontes/código do resumo conferidos
por hash. Checkpoint novo de 41 tem 12.128.256 bytes. Nenhuma leitura individual
de letra pelo agente para conferir esse resultado.

Metadados do índice v2 no SSD inspecionados: 1.254.682.624 bytes, completo,
33.714.178 registros percorridos/5.726.985 indexados. Lista lookup_artists
402.621 bytes, 24.330 chaves, fingerprint correspondente ao selo. Código v2 e
identidade do dump conferidos, sem rehash do dump/índice ou consulta de candidatos.

42 preparado/testado, execução real manual pendente. Consome 40/41, índice
v2 e, quando demonstrada falta de cobertura de artistas, complemento novo
retomável em D:/TCC_LRCLIB/tcc_lookup_nova_amostra_v1. Protege aceitos e
instrumentais; negativas controladas completas podem ser reutilizadas sob
mesma consulta/snapshot/regras. Sem alterar normalização ou tolerâncias.
Evidência de rejeitados por IDs/hashes; textos aceitos originais/efetivos
mantidos. Quatro testes em dump sintético de nove registros, lint aprovado.
Nenhuma execução 42 real, rede, treino, embedding, PDF ou Git nesta preparação.

## Sorteio real e preparação de reuso — D-031, 06/11/2026

40 executado pelo pesquisador, resumo concluído em 2026-11-06T23:59:55Z.
Parquet privado 687.337 bytes/9.526 linhas/27 campos, SHA-256
c89a77793f278a023601e58af7479ce58067c1aef194f5030463dc8a66976f20.
Hash de plano e comparativos conferidos; totais de seis variáveis categóricas
reconciliados, pesos somam N até 2e-10. Interpretação e duas figuras derivadas
apenas de agregados, com revisão visual. Nenhuma linha individual foi analisada
pelo agente; Parquet inspecionado por hash, schema e metadados do rodapé.

41/sample_cache_reuse.py preparado, seis testes sintéticos/lint aprovados.
Caches históricos inspecionados por stat, sqlite_schema e EXPLAIN QUERY PLAN,
sem texto real: v2=1.041.354.752 bytes e v1=6.203.969.536 bytes, ambos sem WAL
não vazio e com SEARCH por query_id. Execução real continua pendente manual.
O código não copia estados inteiros nem lê o dump/índices externos; importa
somente decisões exatas e textos correspondentes com integridade conferida.
Novos resultados em private_nova_amostra_cache_v1/reaproveitamento_nova_amostra_v1.
Negativas não são ausência demonstrada; aceitação herdada não é revisão humana.

## Preservação e dimensionamento — D-030, 06/11/2026

Pacote local reports/preservacao_monografia_20261106/resultados_e_monografias.zip:
430 arquivos, 16.872.772 bytes; SHA-256
62844c01cfc7f844f16532c232de01e60bda509195a858955ed94cbe06311d19.
Inventário lista membros/tamanhos/hashes e verificação registra CRC/SHA de cada
conteúdo e preservação da fonte no instante da cópia. Documentação de continuidade
capturada antes das atualizações D-030; arquivos originais mantidos. Sem backup
externo, Git ou duplicação de dados individuais/modelos/letras/dump.

Dimensionamento 40 executado pelo agente só nos CSV agregados selados de 39:
perfis_grupos, resumo_numerico e frequencias_categoricas. Momentos por gênero
reconciliados com os globais; BPM válido reconstituído com zeros conhecidos.
12 variáveis, 82 gêneros, N=1.159.764 → n=9.526 sob as metas do novo protocolo.
Plano, cenários, alocação, precisão, hashes de código/fontes em
reports/nova_amostra_catalogo_v1. Quatro testes com populações sintéticas pequenas
e lint aprovados. Nenhuma linha individual real foi lida nesse dimensionamento.

Execução real `40 sortear` permanece pendente manual: deverá conferir bytes/hash
do CSV, produzir Parquet privado novo e comparativos agregados, sem LRCLIB,
encoder, treino ou alteração da amostra anterior. Não inferir execução pelo script.

## Descrição completa do catálogo — conclusão D-029, 06/11/2026

39 real executado pelo pesquisador e conferido: 1.159.764 faixas, 82 gêneros,
vinte campos. Manifesto registra conclusão e hash original esperado. Quarenta
e quatro arquivos por hash, frequências, histogramas, eta² e matriz PCA
conferidos pelo agente somente em agregados; treze figuras reais inspecionadas.
Médias das dez contínuas coincidem com a auditoria anterior até arredondamento.
PCA usa 1.158.565 casos; 1.199 tempos zero ficam fora apenas dessa análise.
Interpretação e verificação em reports/ de mesmo tema. Não houve novo sorteio,
letra, modelo preditivo, PDF ou publicação. Próxima etapa: dimensionamento amostral.

### Registro da preparação anterior

Script 39/catalog_description.py usa data/raw/spotify/spotify_data.csv e
configs/quality_rules.yaml, sem mudar bytes ou transportar representações antigas.
Cabeçalho e metadados do arquivo inspecionados; 175.822.041 bytes. Hash esperado
42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897, já registrado
na auditoria anterior, é conferido pelo script durante a execução manual.

Saídas novas previstas em reports/descritiva_catalogo_completo_v1, somente
agregados/figuras. Variáveis acústicas definidas segundo documentação oficial do
Spotify; PCA descritiva fundamentada em Jolliffe (2002), com unidades/escalas e
casos completos documentados. Não usa encoder/LRCLIB ou dados da coorte textual.
Nenhuma execução real realizada pelo agente: conferência somente em fixture
de 120 faixas, com equivalência numérica da PCA por SVD independente e figuras.
Execução integral aguarda pesquisador. Dimensão/técnica da próxima amostra
ainda não escolhidas. Verificação de preparação em
reports/preparacao_descritiva_catalogo_20261106.json.

## Consolidação acadêmica — 06/11/2026 (D-028)

Nova entrada: reports/monografia_template_200k_v3/main.tex, PDF de 45 páginas e
ZIP autossuficiente para Overleaf. Descende da versão 2, preservada por hash.
Objetivos integrados à introdução; regressão, extensão ordinal/PCA e sensibilidade
posterior da regra mantidas como análises distintas. Nenhum dado individual lido
ou modelo real executado para a redação.

Script 38: quatro tabelas a partir de metricas_externas/metricas_por_classe do
ordinal, metricas_regras/metricas_por_classe da sensibilidade e comparação com
regressão categorizada. Cada entrada CSV tem limite de 512 KiB. Duas figuras
copiadas de diagnósticos concluídos; fontes/hashes em proveniencia_extensao.json.
Textos escritos em TeX; cinco referências originais acrescentadas/conferidas.
Compilação/cache local, ZIP limpo recompilado, 45 páginas revisadas e preservação
documentada em reports/verificacao_monografia_template_200k_v3.json.
Versão 2 e documentos anteriores permanecem nos caminhos históricos.

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

## Publicação GitHub — 02/11/2026 (D-024)

Commit principal 082a9a055d4327e4560a693e33a593189b124366 enviado ao remoto
corzxv/tcc-popularidade-musical, master, privado. Seleção de códigos, protocolos,
testes, agregados e fontes acadêmicas; nenhum novo resultado científico gerado.
394 testes locais e lint aprovados; CI de 9b375a8 aprovada após configurar Polars.
Quinze selos científicos e 154 artefatos anteriores preservados. Oito arquivos
saíram apenas do índice atual, mantendo cópias locais e histórico. Relatório
público agregado em reports/publicacao_github_20261102.json; inventários internos
com hashes do índice em logs/publicacao_git_20261102/, fora da publicação.
# Abertura da nova etapa — 04/11/2026 (D-025)

Conferência em 06/11: execução real de 36 informada pelo pesquisador; métricas
originais reproduzidas e probabilidades/modelos preservados. 37 foi executado
pelo agente em 120 métricas, 1.080 células e 360 registros por classe, mais
inspeção filtrada de 128 faixas ≥80/96 componentes, com limite de retorno 129.
Fonte de probabilidades previamente delimitada a 16 MiB, não se materializou
a coorte completa de probabilidades pelo agente. O backend Parquet pode ler
grupos físicos para aplicar o filtro; escopo analítico é a cauda predefinida.
Sem fit/predict de modelos, dump ou rede. Duas figuras renderizadas e conferidas.
Saídas em analise_sensibilidade_decisao_ordinal_v1; registro em
reports/verificacao_sensibilidade_ordinal_20261106.json.

Atualização D-027: produção ordinal completa (20 partes/480 ajustes/77.535 faixas)
executada pelo pesquisador. Agente conferiu agregados, hashes e footers das 25
partes/arquivo global, não reexecutou inferência/fit ou leitura semântica das
77.535 linhas. 35 usa seis CSVs públicos e parâmetros de três modelos PCA próprios,
pequenos e conferidos por hash; figuras PNG/SVG renderizadas e inspecionadas.
36 preparado/testado com fixtures, real pendente; fonte será o Parquet global
existente. Principal e probabilidades permanecem imutáveis; só decisão é comparada
em análise separada e posterior aos resultados. Verificação:
reports/verificacao_producao_ordinal_20261105.json.

Atualização posterior: 34 smoke real executado pelo pesquisador e conferido pelo
agente em 05/11. 318 faixas, 96 ajustes internos, quatro modelos/uma referência,
recarga exata, sem métricas científicas globais. Código/protocolo/fontes e hashes
das partes conferidos; nenhuma desserialização/refit ou leitura integral da coorte
pelo agente. Registro: reports/verificacao_smoke_ordinal_20261105.json.

Atualização posterior de 05/11/D-026: 32 v1.1 concluído pelo pesquisador, 133
consultas. Resumo/alocação e manifesto privado (790.616 bytes) inspecionados;
triagem 33 realizada pelo agente apenas sobre esses metadados. Nenhuma leitura
nova de dump, cache SQLite ou letras. Agregados em triagem_piloto_vinculacao_200k_v1,
detalhes em private_linkage_triage_200k_v1. Fichas/anotações anteriores preservadas.

Script 34 ordinal preparado/testado em dados sintéticos, real ainda não executado.
Fontes reais futuras: base/folds/vetores já selados de 21/20; nenhum transporte
por track_id sem manifesto textual. Protocolo/config/assinaturas próprios, saídas
separadas da regressão. Verificação em verificacao_classificacao_ordinal_20261105.json.

Atualização em 05/11: pesquisador concluiu 31 previsoes. Agregados e selos foram
conferidos pelo agente, sem repetir leitura integral. 32 falhou antes da seleção:
tipo bruto de popularity é large_string. Correção v1.1 cria coluna derivada
numérica; fonte e pastas incompletas anteriores preservadas. Nova execução manual
pendente nas pastas com sufixo v1_1. Relatório: diagnostico_niveis_e_correcao_piloto_20261105.md.

31 agregados usa somente alocacao_amostra_200k.csv (desenho selado) e
parecer_letras_v2/cobertura_por_estrato.csv, 2.009 linhas agregadas ao todo.
Resumos/selos/manifestos científicos são lidos para conferir preservação; PDFs e
pacotes anteriores recebem hash, sem edição. Não houve leitura integral da
coorte individual pelo agente. Resultados em reports/niveis_popularidade_200k_v1/agregados/.

31 previsoes e 32 estão preparados, com execução real manual pendente. Footers
de previsões/folds/resultados e disponibilidade dos caches v1/v2 foram inspecionados.
Abertura somente leitura/EXPLAIN por chave nos caches conferida, sem ler payloads,
recontar tabelas ou recalcular hash de bancos de GB. Nenhum dump/SSD acessado.

Configuração nova registra limites operacionais antes das métricas categorizadas;
protocolos, versões e hashes nas saídas. Preservar a variante E5 existente sem
alegar receita canônica. Nenhum novo texto, vetor ou modelo real produzido.
Testes/escopo: reports/verificacao_nova_etapa_20261104.json. Amostras/folds antigos
continuam fontes da primeira regressão, não dados criados nesta abertura.
