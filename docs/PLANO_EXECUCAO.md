# Plano de revisão acadêmica e entrega da monografia

Linha principal aprovada em D-014: domínio analítico observado com letras aceitas
da amostra recente, sem generalização automática. Todas as fases pesadas são
executadas manualmente pelo pesquisador. Etapas concluídas não devem ser repetidas.

## Publicação autorizada — D-024

Preparar/auditar o índice, executar testes leves e lint, conferir selos e enviar
commits em português ao remoto privado existente. Confirmar HEAD remoto após o
push e registrar o resultado; não alterar avaliação científica ou modelos.
Guias atuais: REPRODUCAO.md, HISTORICO_METODOLOGICO.md e PUBLICACAO_GITHUB.md.

## Próxima ação vigente — revisão do relatório no template (D-023)

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
