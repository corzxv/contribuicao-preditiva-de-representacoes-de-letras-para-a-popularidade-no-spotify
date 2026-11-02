# Contexto permanente do TCC

Atualização: 02/11/2026. TCC de Estatística/UnB, Felipe Macedo Cordeiro. Python,
PowerShell; projeto em `C:\Users\Concursos Felipe\Documents\UnB\TCC`.
Este documento reúne o contexto; números detalhados continuam nos artefatos originais.

## Revisão acadêmica vigente (D-023)

Template e exemplo de Ana fornecidos; BDM e referências originais de TCCs de
Estatística consultados por solicitação do pesquisador. Entrada atual:
reports/monografia_template_200k_v2/main.tex, ZIP e PDF de 34 páginas. Cinco seções,
dois apêndices científicos, 27 referências; fórmulas e trajetória descritiva dos
dados ampliadas. **Leandro Tavares Correia** é a grafia posteriormente confirmada,
superando Correa abaixo. Versão de 57 páginas preservada; D-022 mantém o
congelamento científico. Guia execucao_monografia_template_200k_v2.md.

## Pergunta e decisão aprovada (histórico)

Situação mais recente: modelagem principal congelada por instrução explícita do
pesquisador; D-022. Monografia única concluída para revisão em
reports/monografia_consolidada_200k_v1/main.tex, com ZIP e PDF TeX compilado de
57 páginas, 11 capítulos, quatro apêndices, 14 tabelas, oito figuras e 19 referências.
Orientador Leandro Tavares Correa confirmado; título definido com autorização.
O texto incorpora parecer/limites sem promover intervalos auxiliares a IC integral.
Pendências reais são documentais/institucionais e de revisão acadêmica. Não há
busca, treino ou embeddings em escala a executar para continuar a escrita.

Fechamento metodológico de 02/11 após leitura do PDF: parecer em
reports/parecer_fechamento_metodologico_200k_v1.md e D-021. Há desvio real do E5:
token de espaço adicional ao prefixar tokens separados; confirmado no tokenizer
e em quatro frases artificiais (vetores próximos, diferentes). Não foi medido
efeito no MAE. Preservar execução atual como variante operacional documentada;
não editar fontes seladas nem regenerar corpus automaticamente. Oito textos
reproduziram os 21 descritores sem diferença. Limites auxiliares por fold/grupo
são condicionais e exploratórios: Combinado−Baseline [−0,3140; −0,1607],
Combinado−Profundo [−0,0303; +0,0035], 95% nominais sob hipóteses não verificadas
de componentes independentes; não IC da pipeline integral. Cauda: 128/128
subestimadas, mas apenas 0,5975% do erro absoluto total. Clipping não altera a
cauda; MAE global Combinado cai a 8,0970 só na sensibilidade. PDF/ZIP preservados.

Avaliar ganho preditivo incremental de letras para popularidade Spotify observada
no snapshot: Baseline (metadados/acústicas), Tradicional (+descritores linguísticos),
Profundo (+embeddings), Combinado (+ambos). Mesmas linhas e divisões; MAE/RMSE,
referências simples e validação agrupada. Não causalidade nem promessa de sucesso
futuro. Escala, época e origem da resposta devem constar da monografia.

Em 01/11, o pesquisador aprovou priorizar o **domínio analítico observado com
letras aceitas na amostra de 200 mil**. Não presume representatividade de todas
as músicas com letras nem do catálogo. Preservar amostra/pesos para descrição,
cobertura e seleção; ampliar inferência é investigação futura, não bloqueio para
concluir. Não reiniciar recuperação sem necessidade concreta. D-014 em `decisions.md`.

## Universos que não podem ser confundidos

| Universo | Evidência verificada | Situação |
| --- | --- | --- |
| Catálogo Spotify original | auditoria concluída, 1.159.764 IDs; fonte/hash em `reports/auditoria_catalogo_spotify_20261031/resumo_catalogo_spotify.json` | Referência descritiva; não todo o Spotify |
| Amostra recente | 200.000 linhas no footer, resumo concluído, seed 20261031; 499 ≥80 incluídas integralmente | Preservada; pesos para descrição/seleção |
| LRCLIB recente v1 | 77.391 aceitas, resumo concluído | Histórico imediato preservado |
| LRCLIB recente v2 | 77.535 aceitas; 86.610 não encontradas; 27.085 ambíguas; 8.759 instrumentais; 9 sem texto; 2 insuficientes; sem erro/pendência | Fonte textual principal; matriz de modelagem 21 concluída e comparação congelada |
| Diagnóstico v3 | 1.000 casos, 31 novas aceitações por classificador, 0 pela busca ampliada, 2 regressões inconclusivas | Somente diagnóstico; não houve aplicação integral |
| Integração Spotify–LFM2b antiga | 111.758 pares; footer da matriz v0.1.1: 111.758 × 228 | Outro universo, não requisito de elegibilidade recente |
| Experimento v0.5/v0.6 | 7.648 desenvolvimento; 2.592 teste; quatro blocos | Resultado histórico concluído; teste exposto |
| Coorte aceita antiga ampliada | 58.633 no desenvolvimento, 50 modelos externos de folds verificados; somente Baseline/Tradicional | Resultado exploratório histórico, não as 77.535 recentes |

V2: `reports/recuperacao_letras_200k_v2/resumo_recuperacao_letras_200k.json`;
schemas/footers e metadados inspecionados, sem reprocessar a amostra nesta rodada.
V3: `reports/avaliacao_letras_200k_v3/resumo.json`. As 31 recuperações não foram
incorporadas silenciosamente às 77.535. O catálogo conserva 499 ≥80; isso não
implica 499 letras aceitas nem desempenho comprovado em hits.

## Evidências de seleção e alcance

`reports/parecer_letras_v2/`: sorteio consistente com registros do desenho;
aceitas incompatíveis com margens observadas de equivalência ao catálogo. Popularidade
média ponderada: catálogo 18,383; amostra 18,390; aceitas 23,748. Entre 104 critérios
primários: 21 equivalentes, 74 diferenças individuais e 9 inconclusivos; 72 diferenças
apoiadas após controle familiar. 102 estratos sem aceitas, 348 com menos de cinco.
Isso limita generalização; não demonstra insuficiência para estudar o domínio
observado nem suficiência preditiva. A qualidade dos matches é questão separada.

## Histórico científico preservado

- v0.1/v0.1.1: integração LFM2b, metadados/acústicas e descritores herdados;
  splits agrupados de 83.817/27.941 na integração inteira.
- Pilotos v0.1.x/v0.2/v0.3: coleta, equivalência, idioma, MiniLM de 384 dimensões,
  experiências iniciais de regressão/PCA. Resultados não são da nova amostra.
- v0.4–v0.6: 10.240 composições com quatro blocos; teste aberto em
  `2026-10-14T16:12:27.567600+00:00`. `reports/final_holdout_metrics_v0_6.csv`:
  Elastic Net MAE Baseline 7,2029, Tradicional 7,1831, Profundo 7,2990,
  Combinado 7,2679 (n=2.592). Não prometem superioridade de embeddings.
- v0.7/v0.8/v0.9: diagnósticos, splines/boosting, ampliação de treinos; exploratórios
  após conhecimento do teste. Nenhum resultado é nova confirmação independente.
- Coorte estatística antiga: `private_statistical_cohort_v1/verification.json`,
  stage verified, n=58.633, 50 modelos, diferença de reprodução 0,0, entradas
  preservadas e alvos históricos não carregados nessa rodada. Ganho aditivo
  tradicional pequeno (MAE 6,9546→6,8906) conforme resultados salvos.

## Fonte textual e representações

Dump LRCLIB: `D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`,
261.755.867.136 bytes segundo checkpoint anterior, preservado. Índices concluídos:
antigo 12.757.266, suplemento v1 4.455.510, auxiliar v2 5.726.985 registros.
Não são contagens de letras da amostra; têm filtros de artista documentados.
Não repetir varredura para simples descrição. Checkpoints não são assinatura
independente do publicador.

V2 tem tabela privada de textos com `accepted_text`, representações originais,
hashes, query_id e proveniência. Idioma estimado nos agregados: 56.908 en,
6.345 es, 3.686 pt, entre outros; não houve restrição da base ao inglês.
Snapshot MiniLM antigo disponível localmente: revisão
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 dimensões, trechos de 256 tokens
com sobreposição 32. Presença do modelo não comprova adequação ao corpus atual
nem vetores compatíveis já calculados. Preservação de todos os idiomas mantida;
encoder novo E5 small multilingue/revisão congelados em D-016; smoke real concluído
com 24 vetores, cobertura integral e entradas efetivas até 512 tokens. Isso verifica
o funcionamento técnico, sem demonstrar adequação semântica ou ganho preditivo.
Auditoria 17 posterior confirmou 56.908
inglesas, 20.447 não inglesas e 180 incertas, sem filtros.

LFM2b fornece descritores de outro processamento textual; não reconstruir letras
dele, não preencher as demais faixas com descritores ausentes, não transportar por
track_id sem compatibilidade de gravação/texto. Priorizar descritores transparentes
sobre o mesmo texto que alimentar o embedding; definições serão congeladas antes
de gerar em escala. Não imputar embeddings sintéticos como pressuposto.

## Validação, monografia e modo de trabalho

Script 19 executado: 77.535 linhas preservadas, 77.051 inputs normalizados,
21 descritores, 21.893 componentes, maior 186, zero chaves não resolvidas. Saídas
privadas em `private_text_descriptors_200k_v1`; agregados em
`reports/descritores_textuais_200k_v1/`. Estes são descritores do próprio texto,
não os 196 LFM2b. Download/smoke do script 20 concluídos pelo pesquisador em 55,26 s
no teste: 68 janelas e reprodução exata do controle. Primeiro lote manual concluído:
1.000 novos vetores em 296,25 s. Integral agora concluída após pausa/retomada:
77.051 vetores para 77.535 faixas, zero pendências, 91.156 janelas até 512 tokens.
Última execução 4.914,39 s, 27.352 novos + 49.699 reutilizados; isso não é tempo
total acumulado. Script 21 agora concluído em 8,323 s: vetores integralmente
auditados, base/folds comuns e zero metadados inválidos/ausentes. Próxima ação
de escrita: integração do trecho recente; 22/23 agora concluídos, sem novo treino necessário.
Não repetir etapas concluídas nem iniciar processamento real pelo agente.

Agrupar artista, composição operacional, versões e textos iguais; auditar relação
com grupos/avaliações antigos. Novo split não apaga exposição. CV aninhada agrupada
5×3 aprovada em 01/11/2026 após auditoria 17; folds gerados/auditados em 21: testes
externos de 15.507 faixas, treinos de 62.028; avaliações internas de 20.676.
Comparação
pareada e transformações
aprendidas dentro de treino. Ponderação aprovada em D-017: pesos iguais por faixa
no ajuste/métricas principais, seleção/primária por MAE; RMSE e R² complementares.
Estimar desempenho médio na distribuição empírica observada sob CV agrupada.
Sensibilidade com MAE ponderado original nas mesmas observações/previsões externas/
folds, sem retreinar/selecionar pelo resultado ponderado. Pesos/estratos preservados
para descrição e diagnóstico; não são correção automática de seleção textual.
Texto para monografia em metodologia_modelagem_200k_v1.md. Script 21 concluído;
runner 22 preparado para Ridge nos quatro blocos, referências média/mediana,
seis alphas e checkpoints. Smoke real concluído em 318 faixas/1,843 s: quatro
blocos + duas referências, reprodução exata e zero avisos nos ajustes internos.
Smoke não é avaliação científica. Integral 22 agora concluída: 20 partes Ridge,
dez referências, 77.535 previsões por variante; 360 ajustes internos sem avisos.
MAE principal Baseline 8,3525, Tradicional 8,2957, Profundo 8,1285, Combinado
8,1151. Redução Combinado/Baseline 2,842% (ponderada 2,781%); mesma ordenação.
Combinado melhora só 0,0134 ponto frente ao Profundo. Sem IC/p-valores; alcance
restrito ao domínio observado e procedimento Ridge. Relatório inicial em
reports/interpretacao_modelagem_200k_v1.md. Script 23 concluído em 0,608 s, métricas
reproduzidas: Combinado melhor em todos os folds e sinais preservados na retirada
condicional de um componente. Sem IC/refit. Faixa 80-100 tem MAE 29,37 (n=128);
idioma incerto piora (n=180). Resultados de subgrupos são exploratórios, não universais.

Manuscrito histórico: `reports/overleaf_resultados_coorte_aceita_v1/` e ZIP. É pacote
parcial de metodologia/resultados/discussão da coorte antiga; não monografia completa
da amostra recente. Preservar e reaproveitar estrutura/referências, com revisão de
números/universos. Novo trecho parcial recente em overleaf_dominio_observado_200k_v1
e ZIP: seis tabelas/quatro figuras, fonte TeX compilada no editor integrado. PDF
de leitura ReportLab de sete páginas em output/pdf/resultados_dominio_observado_200k_v1.pdf,
visualmente revisado, sem afirmar paginação idêntica ao TeX ou monografia completa.
Gerador 24 opera só em agregados públicos, não em bases/modelos. Essa pendência
histórica de texto completo foi resolvida criando a monografia única nova, sem
sobrescrever os trechos. Script 28 gera seus artefatos editoriais leves; capítulos
e bibliografia são fontes editáveis. Novo guia execucao_monografia_consolidada_200k_v1.md.

Agente implementa, testa em pequeno e mantém contexto; pesquisador executa pesados
manualmente. Próxima ação e comando em `PLANO_EXECUCAO.md`; evidências em
`MAPA_ARTEFATOS.md`; estado operacional em `ESTADO_ATUAL.md`.
