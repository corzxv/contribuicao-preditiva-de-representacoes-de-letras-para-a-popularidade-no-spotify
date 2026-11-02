# Mapa de artefatos e consumidores

Consolidação de 01/11/2026. Caminhos relativos à raiz do projeto; D: é SSD externo.
Classificação é lógica: nenhum arquivo foi movido ou apagado. Resultados históricos
continuam disponíveis nos mesmos caminhos. Não usar números de universos distintos
na mesma tabela de comparação preditiva.

**ATIVO** participa da linha recente aprovada; **REUTILIZÁVEL** oferece implementação
ou material com compatibilidade a verificar; **HISTÓRICO** é evidência de etapa
anterior preservada; **PENDENTE** ainda não foi validado/concluído para uso atual.
O inventário individual gerado está em `../reports/inventario_projeto_20261101.json`:
nomes/tamanhos/categorias provisórias, sem ler corpos de bases/modelos, sem SSD e
com profundidade limitada nos dados. A existência no inventário não prova execução;
este mapa traz dependências e evidências científicas.

## Arquivos da publicação — D-024

README.md, requirements-cientificos.txt, .gitattributes/.gitignore, guias públicos
REPRODUCAO/HISTORICO_METODOLOGICO/PUBLICACAO_GITHUB, script 30 e git_publication.py
são entradas de consulta/publicação. Os códigos históricos com consumidores
permanecem. Oito arquivos de prévias/roteiros retirados do índice ficam locais,
assim como dados/modelos/cache/demonstrador/prévias pessoais. O mapa anterior
registra sua existência local e histórica, não inclusão automática no GitHub.

## Entrada acadêmica atual — D-023

ATIVO: reports/monografia_template_200k_v2/main.tex, ZIP correspondente e
output/pdf/monografia_template_200k_v2.pdf (34 páginas, 27 fontes originais).
Consumidor: Overleaf/revisão com Leandro Tavares Correia. Script 29 gera só duas
figuras/uma tabela novas de agregados e reutiliza artefatos editoriais compatíveis,
sem dados individuais/dump/modelos. Relatório de revisão e verificação em reports/;
guia docs/execucao_monografia_template_200k_v2.md. ZIPs Template_Relatório_TCC.zip
e relatorio_tcc_ana.zip preservados. TCCs BDM consultados, sem redistribuição no
pacote. Projeto anterior de 57 páginas passa a HISTÓRICO.

## Fontes e linha recente (inclui histórico)

Entrada acadêmica anterior (D-022): reports/monografia_consolidada_200k_v1/main.tex,
ZIP de mesmo nome e output/pdf/monografia_consolidada_200k_v1.pdf. Versão completa
para revisão: 57 páginas, 11 capítulos/quatro apêndices, 14 tabelas, oito figuras,
19 referências. Script 28/monograph_assets.py gera só tabelas/figuras de agregados;
nenhum dado individual/modelo. Inventário de 195 materiais/135 textos e manifesto
de 154 artefatos anteriores preservados no pacote. Relatório de consolidação e
verificação de compilação em reports/. Modelagem principal encerrada, sem nova
geração de dados/modelos autorizada automaticamente por pendências de escrita.

Adendo ativo de 02/11: `reports/parecer_fechamento_metodologico_200k_v1.md`,
`reports/fechamento_metodologico_200k_v1/`, `closure_diagnostics.py`, scripts
25/26/27 e `resumir_cauda_auxiliar.py`. Diagnósticos leves concluídos; somente
agregados públicos, sem novos modelos/vetores do corpus. 26 reproduz oito textos
e audita tokenização; 27 mede o desvio do espaço extra em quatro frases artificiais.
Consumidores: revisão escrita e decisões D-021. Não são substitutos dos artefatos
19–24. Guia `execucao_fechamento_metodologico_200k_v1.md`.

| Classe | Artefato/local | Finalidade, dependências e evidência |
| --- | --- | --- |
| ATIVO | `data/raw/spotify/spotify_data.csv`; `data/raw/manifest.json` | Fonte imutável; hash documentado. Não reimportar para reorganizar |
| ATIVO | `reports/auditoria_catalogo_spotify_20261031/`; `catalog_audit.py`; script 11 | Catálogo auditado 1.159.764; resumo concluído e agregados. Alimenta amostra/parecer |
| ATIVO | `reports/amostra_spotify_200k_20261031/`; `catalog_sampling.py`; script 12 | Parquet/footer 200.000, alocação, hash, seed e pesos; sorteio já executado |
| ATIVO | `D:/TCC_LRCLIB/lrclib-db-dump-20261012T090639Z.sqlite3` | Snapshot textual; checkpoint ready histórico. Não mover/duplicar/revarrer |
| ATIVO | `D:/TCC_LRCLIB/tcc_lookup_v1/`, `tcc_lookup_sample_200k_v1/`, `tcc_lookup_sample_200k_v2/` | Índices por artista; progressos completos, respectivamente 12.757.266/4.455.510/5.726.985. Somente reuso quando necessário |
| HISTÓRICO | `data/derived/private_sample_lyrics_200k_v1/`; `reports/busca_local_200k_20261031/`; script 13 | Primeira busca recente concluída, 77.391 aceitas; origem da v2. Não sobrescrever |
| ATIVO | `data/derived/private_sample_lyrics_200k_v2/`; `reports/recuperacao_letras_200k_v2/`; script 14 | Resultado candidato principal: 200.000 linhas, 77.535 aceitas; tabela de textos 77.535 consultas. V2 já executada; script de reprodução, não próxima tarefa |
| ATIVO | `reports/parecer_letras_v2/`; script 16; `lyrics_statistical_opinion.py` | Parecer completo incompatível com margens observadas de equivalência ao catálogo; informa alcance, não proíbe estudar o domínio observado |
| PENDENTE | `private_sample_lyrics_200k_v3/`, `reports/avaliacao_letras_200k_v3/`; script 15 | Avaliação de 1.000 concluída. Aplicação integral NÃO executada (pasta de relatório integral ausente); revisão humana de propostas não concluída |
| ATIVO | script 17; `data_readiness.py`; `reports/prontidao_dados_200k_v1/` | Auditoria de pré-fechamento executada pelo pesquisador: 77.535 textos/vínculos verificados. Não gera preditores/splits; não repetir para continuar |
| ATIVO | script 19; `text_descriptors.py`; `private_text_descriptors_200k_v1/`; `reports/descritores_textuais_200k_v1/` | Geração concluída pelo pesquisador: 77.535 linhas, 77.051 textos normalizados, 21 descritores e 21.893 componentes. Não repetir; contrato selado |
| ATIVO | script 20; `multilingual_embeddings.py`; `private_embeddings_200k_v1/`; `reports/embeddings_multilingues_200k_v1/{smoke,integral}/`; protocolo/guia | Integral concluída pelo pesquisador: 77.051 vetores, 77.535 faixas, zero pendências, 91.156 janelas até 512. Footers/checkpoint e amostra técnica de 8 vetores/vínculos conferidos pelo agente; não repetir |
| ATIVO | script 21; `observed_modeling_data.py`; `private_modeling_200k_v1/`; `reports/base_modelagem_200k_v1/`; protocolo/guia/metodologia | Concluído pelo pesquisador em 8,323 s: 77.535 faixas e 77.051 vetores auditados, 21.893 componentes, zero metadados inválidos/ausentes. Folds reais 5×3 e alinhamento/separação aprovados; código/protocolo selados |
| ATIVO | script 22; `observed_regression.py`; protocolo/guia; `private_regression_200k_v1/{smoke,integral}/`; `reports/modelagem_200k_v1/{smoke,integral}/` | Integral concluída: 20 partes Ridge + dez referências, 77.535 previsões por variante, 360 ajustes internos sem avisos. Hashes de 30 partes/arquivo global e selos conferidos; não repetir ou retunar após resultados |
| ATIVO | `reports/interpretacao_modelagem_200k_v1.md`; script 23; `observed_results.py`; `private_results_diagnostics_200k_v1/`; `reports/diagnosticos_modelagem_200k_v1/` | 23 concluído em 0,608 s: 30 partes/métricas reproduzidas, 21.893 componentes, 116 células publicadas/77 omitidas. Ganhos estáveis condicionalmente, exceções por subgrupo; sem IC/refit |
| ATIVO | script 24; `publication_results.py`; renderizador PDF; `reports/overleaf_dominio_observado_200k_v1/` e ZIP; `output/pdf/resultados_dominio_observado_200k_v1.pdf` | Trecho parcial recente: seis tabelas/quatro figuras PNG/SVG, 28 arquivos no ZIP, TeX compilado; PDF ReportLab de sete páginas revisado. Somente agregados públicos, sem dados individuais/modelos; preserva pacote histórico |
| ATIVO | script 18; `project_inventory.py` | Inventário limitado de metadados, pode ser atualizado sem ler dados/modelos |
| ATIVO | `AGENTS.md`, `CONTEXTO_TCC.md`, `ESTADO_ATUAL.md`, `PLANO_EXECUCAO.md`, `decisions.md` | Pontos de continuidade canônicos |
| ATIVO | `data_dictionary.md`, `provenance.md`, protocolos amostra/parecer/busca recentes | Schema/proveniência/regras; preservar histórico com datas |

## Integração e experimentos anteriores

| Classe | Artefato/local | Finalidade, dependências e evidência |
| --- | --- | --- |
| HISTÓRICO | `data/raw/lfm2b/`, configuração `data_sources.example.yaml` e manifesto | Fonte de descritores, não requisito da amostra recente; confirmar arquivo exato pelo manifesto, não adivinhar novo download |
| HISTÓRICO | `data/processed/spotify_tracks.parquet`, `lfm2b_tracks.parquet`, `spotify_lfm_*.parquet`, DuckDB | Camadas da integração antiga. Footers Spotify 1.159.764/LFM2b 582.759; joins de então, não nova coorte |
| HISTÓRICO | `modeling_base_lfm_v0_1*.parquet`, `split_assignments_v0_1_1.parquet`, `matching_audit_v0_1_1.parquet` | 111.758 linhas; atribuições/grupos e auditoria histórica. IDs/partições são consumidores do script 17; não carregar alvos para linhagem |
| REUTILIZÁVEL | `acquisition.py`, `spotify.py`, `lfm2b.py`, `matching.py`, `revision_v011.py`, `validation_v011.py`, CLI base | Infraestrutura de ingestão/auditoria antiga; não executar `all` por padrão |
| HISTÓRICO | pilotos `lyrics_pilot*`, resultados `lyrics_pilot_*`, relatórios `lyrics_*v0_1*` | Seleção, API/cache e ambiguidades antigas. Regras/protocolos não são silenciosamente os da v2 recente |
| REUTILIZÁVEL | `normalization.py`, `lyrics_ambiguity_v011.py`, `manual_lyrics.py`, `local_lyrics.py` | Normalização/fingerprints/locks/exportação; composição é operacional e não universal |
| HISTÓRICO | `private_manual_lyrics_v1/`, `private_local_lyrics_v1/`, auditoria `private_local_lyrics_audit/`; scripts 01–08 | Universo antigo Spotify–LFM2b, consultas aceitas 78.323 segundo resumo histórico. Distinto das 77.535 recentes |
| REUTILIZÁVEL | `lyrics_embeddings_v020.py`, `manual_embeddings.py`, `embeddings_scale_v040.py`, configs do encoder | Funções de normalização, trechos, índice e checkpoints. Dependem de revisão/modelo/texto e schema antigos |
| HISTÓRICO | `data/derived/private_embeddings/`, `private_final_study/`; relatórios v0.2/v0.4 | Vetores antigos e índices; não copiar por track_id. Reconciliador v0.4 confirma 7.648/2.592, dimensão 384 e finitude nesse universo |
| HISTÓRICO | `private_modeling/`, pilotos v0.3/v0.3.1 | Regressão/PCA/transformações exploratórias; parâmetros/resultados não justificam escolha pela métrica atual |
| HISTÓRICO | `private_final_development_v0_5/`, `private_final_holdout_v0_6/` | Matrizes 7.648/2.592 e 9 modelos finais antigos. Summary v0.6 complete; teste aberto em 14/10/2026. Preservar opening_record e predições |
| HISTÓRICO | `private_diagnostics_v0_7/`, `private_statistical_revision_v0_8/`, `private_training_expansion_v0_9/`; relatórios/configs respectivos | Revisões pós-teste, ampliaram diagnóstico/treinos, não confirmação independente |
| HISTÓRICO | `private_statistical_cohort_v1/`; scripts 09/10; `cohort_statistics.py`, `cohort_regression.py` | 58.633 no desenvolvimento; 50 modelos de folds verificados, somente dois blocos. Inputs e alvos históricos preservados; reprodução 0,0 |
| REUTILIZÁVEL | `cohort_regression.py`, `final_development_v050.py`, `modeling_*`, testes correspondentes | CV agrupada/aninhada, pré-processamento interno ao treino e métricas pareadas. Adaptar ao contrato de quatro blocos recente, sem treinar agora |
| HISTÓRICO | `apps/`, `.streamlit/`, `local_demo*`, requisitos do demonstrador | Interface/modelos de estudo antigo; não alterar nem tomar como autoridade científica da nova coorte |
| REUTILIZÁVEL | `reports/overleaf_resultados_coorte_aceita_v1/`, ZIP, figuras/legendas v0.6 | Manuscrito parcial e material histórico; reaproveitar estrutura/referências, não números como se fossem atuais |
| PENDENTE | `base_preview.xlsx`, `reports/base_preview.xlsx`, `exp_base.py`, `preview_*`, handoffs soltos | Materiais auxiliares existentes; não são autoridade metodológica. Sem inspeção de todas as células/corpos nesta rodada |
| PENDENTE | revisão acadêmica da monografia consolidada; adequação institucional, datas/proveniência não confirmadas e avaliação humana de matching | main.tex único já criado e parecer integrado, sem sobrescrever trechos anteriores. Limites condicionais mantidos como auxiliares; modelagem congelada. Apêndice D indica confirmação específica e pontos para o orientador |

## Organização e dependências preservadas

Nenhum movimento físico: scripts antigos têm caminhos congelados em configs,
manifests, selos e documentos LaTeX. Uma mudança de diretórios quebraria consumidores
e invalidaria retomadas. Nesta rodada a organização é feita por README, classificação
e pontos de entrada. Arquivamento físico futuro exige mapa de consumidores,
migração reversível e autorização para partes incompatíveis.

Dados, letras, modelos e caches permanecem ignorados pelo Git. O estado inicial
tinha alterações pessoais e muitos arquivos não rastreados; não foram descartados
ou adicionados automaticamente. Inventário não contém corpos de dados, textos,
credenciais, predições ou parâmetros binários de modelos.
