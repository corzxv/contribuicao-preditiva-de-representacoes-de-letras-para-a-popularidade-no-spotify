# Estado atual — 02/11/2026

Leia este arquivo primeiro ao continuar em outro chat. Depois: `CONTEXTO_TCC.md`,
`PLANO_EXECUCAO.md`, `MAPA_ARTEFATOS.md` e `decisions.md`. Não recomeçar o TCC.

## Organização do Git e publicação — D-024

Autorizada publicação em corzxv/tcc-popularidade-musical, master, privado.
Seleção auditada em andamento; README/guia de reprodução/histórico/política de
publicação atualizados. Fontes seladas mantidas e oito prévias/roteiros antigos
retirados apenas do índice, sem apagar arquivos locais. Confirmação remota e
resultado dos testes ficam no relatório de publicação; não inferir push pela
existência dos códigos. A entrada acadêmica atual continua sendo a versão 2.

## Entrada acadêmica atual — template fornecido (D-023, 02/11)

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

## Próxima ação concreta — versão no template

Revisar reports/monografia_template_200k_v2/main.tex com Leandro Tavares Correia;
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
