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

## Etapa vigente — repositório organizado para a edição atual, D-049

- ATIVO: `README.md` e `docs/PUBLICACAO_GITHUB.md` orientam o acesso à
  edição e aos códigos em `corzxv/contribuicao-preditiva-de-representacoes-de-letras-para-a-popularidade-no-spotify`.
- ATIVO: fontes, PDF, ZIP e agregados da edição D-048.
- HISTÓRICO: as cópias locais das versões editoriais intermediárias e o
  pacote de preservação têm caminhos registrados e ficam fora da seleção nova.

## Histórico — monografia otimizada para Overleaf, D-048

- ATIVO: reports/monografia_template_overleaf/main.tex, seu ZIP e o PDF
  em output/pdf/monografia_template_overleaf.pdf.
- ATIVO: script 58 gera os contrastes da nova edição. Opção
  `--somente-contrastes` atualiza apenas a tabela CSV e o gráfico.
  Script 59 tem opção `--paineis-compactos` para as figuras 6 e 7.
- Evidência técnica: reports/verificacao_monografia_template_overleaf.json.

## Histórico — monografia revisada, D-047

- ATIVO: reports/monografia_template_revisada/main.tex, suas tabelas e figuras,
  reports/monografia_template_revisada.zip e
  output/pdf/monografia_template_revisada.pdf.
- ATIVO: scripts/59_consolidar_descritivas_monografia.py, que verifica a
  sobreposição dos conjuntos, tabula os formatos e prepara figuras com
  agregados ou as duas seleções seladas de 9.526 faixas.
- Evidência técnica: reports/verificacao_monografia_template_revisada.json.

## Histórico — monografia D-046

- ATIVO: reports/monografia_template_final/main.tex, fontes LaTeX e material
  complementar agregado da descrição, vinculação e avaliação.
- ATIVO: reports/monografia_template_final.zip e
  output/pdf/monografia_template_final.pdf, compilado a partir do ZIP.
- ATIVO: scripts/58_diagnosticar_previsoes_monografia_final.py e
  reports/monografia_template_final/material_complementar/contrastes_condicionais.csv.
  O script usa as probabilidades externas seladas de 57 e só exporta agregados.
- Evidência técnica: reports/verificacao_monografia_template_final.json.
  Monografia v3 e resultados científicos de origem preservados.

## Histórico — classificação concluída, D-045

57 REAL. `reports/classificacao_9526_v1` guarda o resumo, as métricas e
`interpretacao_resultados.md`. Em `data/derived/private_classificacao_9526_v1`
estão as divisões, probabilidades individuais, modelos e checkpoint.

## Histórico — classificação da candidata v2, D-044

57 em scripts/57_classificar_amostra_9526.py e
src/tcc_music_popularity/linked_classification.py. As 9.526 faixas e as
divisões 5×3 foram conferidas na preparação. A execução manual escreve
reports/classificacao_9526_v1 e data/derived/private_classificacao_9526_v1.

## Histórico — candidata ampliada, D-043

55 completo em reports/recuperacao_generos_deficitarios_v1, com checkpoint
e vínculos privados em data/derived/private_recuperacao_generos_deficitarios_v1.
56 usa `scripts/56_atualizar_amostra_com_letras.py` para produzir a candidata
em data/processed/private_amostra_com_letras_candidata_v2/amostra_candidata_9526.parquet
e os agregados em reports/amostra_com_letras_candidata_v2.

## Histórico — recuperação dirigida, D-042

53 revalidou o cache em reports/revalidacao_cache_historico_v1 e gravou os
vínculos e textos em data/derived/private_revalidacao_cache_historico_v1.
54 selou a lista de consultas em data/derived/private_triagem_generos_deficitarios_v1
com resumo em reports/triagem_generos_deficitarios_v1. 55 está preparado
para produzir o checkpoint e vínculos em data/derived/private_recuperacao_generos_deficitarios_v1,
com agregado em reports/recuperacao_generos_deficitarios_v1.

## Histórico — candidata completa com letras, D-041

52 REAL leve usa `scripts/52_preparar_amostra_com_letras.py` e
`src/tcc_music_popularity/linked_sample_design.py`. A candidata privada está em
data/processed/private_amostra_com_letras_candidata_v1/amostra_candidata_9526.parquet.
O Parquet referencia seis arquivos selados com os textos originais. Os
agregados e selos estão em reports/amostra_com_letras_candidata_v1.

## Histórico — revisão local e consolidação reais, D-040

50 REAL em reports/revisao_limites_nova_amostra_v1, com complemento privado
data/derived/private_revisao_limites_nova_amostra_v1 e 25 novos vínculos.
51 REAL usa scripts/51_consolidar_vinculos_nova_amostra.py para combinar 43,
46, 47, 48 e 50. Em data/derived/private_vinculos_consolidados_nova_amostra_v1
o `vinculos_e_status.parquet` referencia os textos por chave e arquivo.
Agregados de cobertura em reports/recuperacao_consolidada_nova_amostra_v1.

## Histórico — piloto online real e revisão local preparada, D-039

49 REAL. O resumo selado e `verificacao_resultado_piloto.json` estão em
reports/piloto_online_nova_amostra_v1. Zero candidatas em 100 consultas.

50 PREPARADO. `scripts/50_revisar_limite_de_candidatos.py` usa o estado 43,
os índices existentes e o dump. A saída prevista é
reports/revisao_limites_nova_amostra_v1 e o complemento privado é
data/derived/private_revisao_limites_nova_amostra_v1.

## Histórico — piloto online preparado, D-038

49 usa scripts/49_pilotar_busca_online_lrclib.py e
src/tcc_music_popularity/lyrics_online_pilot.py. A entrada selada está em
data/derived/private_piloto_online_nova_amostra_v1/manifesto.json. A coleta
manual gravará `state.sqlite` nessa mesma pasta e o resumo agregado em
reports/piloto_online_nova_amostra_v1/resumo_piloto_online.json.

## Histórico — 47 e 48 reais, D-037

47 REAL em reports/revisao_caixa_plain_lrc_nova_amostra_v1 e
data/derived/private_revisao_caixa_plain_lrc_nova_amostra_v1. A cobertura
combinada 43/46/47 está em reports/cobertura_pos_revisao_plain_lrc_nova_amostra_v1.

48 REAL leve em reports/revisao_variantes_artista_nova_amostra_v1. O script
48_registrar_variantes_artista_revisadas.py consome as fichas documentais e o
diagnóstico 44, usando o dump por ID. Em data/derived/private_revisao_variantes_artista_nova_amostra_v1
ficam `revisao_documental.json`, `desfechos.json` e o complemento de vínculos
e letras. Cobertura 43/46/47/48 em reports/cobertura_pos_revisao_variantes_nova_amostra_v1.

## Histórico — 46 real e 47 preparado, D-036

46 REAL concluído. reports/revisao_caixa_nova_amostra_v1 resume os 130 vínculos
novos. As tabelas em reports/cobertura_pos_revisao_caixa_nova_amostra_v1 combinam
43 e 46 apenas para descrever a cobertura das 3.777 aceitas.

47 PREPARADO, scripts/47_revisar_caixa_plain_lrc.py e
src/tcc_music_popularity/lyrics_synced_revision.py. Consome evidências seladas
de 43, vínculos de 46 e textos por ID no dump. Saída pública prevista em
reports/revisao_caixa_plain_lrc_nova_amostra_v1. O complemento privado fica em
data/derived/private_revisao_caixa_plain_lrc_nova_amostra_v1. Consumir junto a
43 e 46 por `query_id` e `track_id` depois da conferência da execução.

## Histórico — diagnóstico e consolidação, D-035

44 REAL: reports/diagnostico_chaves_nova_amostra_v1 e checkpoint privado
correspondente, 4.164 consultas e 13 casos de variação de artista. 45 REAL leve:
reports/consolidacao_dados_nova_amostra_v1 com comparação, cobertura e figura.
Fichas de 16 pares em data/derived/private_consolidacao_nova_amostra_v1.
Interpretação em reports/interpretacao_diagnostico_chaves_e_consolidacao_v1.md.

46 PREPARADO: scripts/46_revisar_caixa_textos_concorrentes.py e
src/tcc_music_popularity/lyrics_case_revision.py. Revisão das 831 consultas por
índices existentes. Resumo previsto em reports/revisao_caixa_nova_amostra_v1 e
complemento privado em data/derived/private_revisao_caixa_nova_amostra_v1.
Consumo futuro: vincular novos textos por query_id a novos vínculos por track_id
e combinar com os produtos de 43. Execução real manual pendente.

## Histórico — 43 real e diagnóstico preparado, D-034

CONCLUÍDO REAL: data/derived/private_nova_amostra_matching_v2 e
reports/revisao_matching_nova_amostra_v2, 3.647 aceitas/1.298 ambíguas/4.164 sem
candidato/416 instrumentais/uma sem texto. Interpretação em
reports/interpretacao_revisao_matching_nova_amostra_v2.md. Não repetir 43.

PREPARADO/SEM EXECUÇÃO REAL: scripts/44_diagnosticar_consultas_sem_candidato.py →
src/tcc_music_popularity/native_lookup_audit.py. Consome consultas 43 e índices
nativos do dump, em modo somente leitura. Saídas previstas:
data/derived/private_diagnostico_chaves_nova_amostra_v1 (metadados candidatos,
métodos e limites) e reports/diagnostico_chaves_nova_amostra_v1 (agregados).
Sem letras ou alteração dos resultados 43. Guia execucao_diagnostico_chaves_nova_amostra_v1.md;
testes test_native_lookup_audit.py. Consumidor seguinte: revisão dirigida dos candidatos.
Evidência: reports/verificacao_revisao_matching_e_preparacao_diagnostico_20261106.json.

## Histórico — 42 real e correção dirigida preparada, D-033

CONCLUÍDO REAL: data/derived/private_nova_amostra_local_v1 e
reports/busca_local_nova_amostra_v1. 1.425 aceitas/362 instrumentais/3.574
ambíguas/4.164 sem candidato/uma sem texto, zero erro/pendência. Não repetir 42.

PREPARADO/SEM EXECUÇÃO REAL: scripts/43_revisar_bloqueios_vinculacao.py →
src/tcc_music_popularity/lyrics_matching_revision.py. Consome 42/amostra 40,
índices v2/complemento existentes e dump em modo somente leitura. Não cria
índice novo. Saídas previstas: data/derived/private_nova_amostra_matching_v2 e
reports/revisao_matching_nova_amostra_v2. Reavalia somente 3.162 bloqueios por
layout plain/LRC ou veto indevido por outra versão com candidato compatível.
Guia revisao_bloqueios_vinculacao_v2.md; testes test_lyrics_matching_revision.py.
Evidência: reports/auditoria_bloqueios_matching_nova_amostra_v1.json; casos
diagnósticos em data/derived/private_auditoria_matching_nova_amostra_v1.

## Histórico — 41 real e busca local preparada, D-032

CONCLUÍDO REAL: data/derived/private_nova_amostra_cache_v1 e
reports/reaproveitamento_nova_amostra_v1. 682 letras/87 instrumentais/8.757
pendentes, 9.526 consultas, zero erros. Interpretação em
reports/interpretacao_reaproveitamento_nova_amostra_v1.md. Não repetir 41.

PREPARADO/SEM EXECUÇÃO REAL: scripts/42_buscar_letras_nova_amostra.py →
src/tcc_music_popularity/new_sample_local.py. Consome amostra 40, resultados 41,
dump D:/TCC_LRCLIB/lrclib-db-dump-20261012T090639Z.sqlite3, índice v2 existente e
lista de artistas selada do estado histórico v2. Complemento novo somente quando
necessário em D:/TCC_LRCLIB/tcc_lookup_nova_amostra_v1. Nunca alterar índice antigo.
Saídas previstas: data/derived/private_nova_amostra_local_v1 e
reports/busca_local_nova_amostra_v1 (resumo/status/cobertura/transições).
Guia execucao_busca_nova_amostra_v1.md; testes tests/test_new_sample_local.py.
Consumidor futuro: diagnóstico de cobertura/seleção e revisão de pendências.
Verificação: reports/verificacao_cache_e_preparacao_busca_nova_amostra_20261106.json.

## Histórico — nova amostra real e reaproveitamento, D-031

CONCLUÍDO REAL: data/processed/nova_amostra_catalogo_v1/amostra_spotify.parquet
(687.337 bytes, 9.526 linhas/27 campos); resumo_sorteio.json e comparativos em
reports/nova_amostra_catalogo_v1. Interpretação em
reports/interpretacao_nova_amostra_catalogo_v1.md; comparacao_medias_dispersoes e
comparacao_periodos (PNG/SVG). Gerador leve: scripts/analisar_comparativo_nova_amostra.py,
somente agregados. Não altera a descrição 39 ou o código selado 40.
Verificação: reports/verificacao_sorteio_nova_amostra_20261106.json.

PREPARADO/SEM EXECUÇÃO REAL: scripts/41_reaproveitar_letras_nova_amostra.py →
src/tcc_music_popularity/sample_cache_reuse.py. Consome nova amostra e consultas
pontuais nos estados private_sample_lyrics_200k_v2/v1, sem varredura, SSD ou rede.
Saídas previstas: data/derived/private_nova_amostra_cache_v1 (estado, resultados,
textos privados e pendências); reports/reaproveitamento_nova_amostra_v1
(resumo/status/cobertura). Guia execucao_reaproveitamento_nova_amostra_v1.md;
testes em tests/test_sample_cache_reuse.py. Consumidor futuro: busca dirigida
para as pendências, ainda não preparada/executada integralmente.

## Histórico — preservação e nova amostra, D-030

CONCLUÍDO: reports/preservacao_monografia_20261106/resultados_e_monografias.zip,
inventario.json e verificacao.json: pacote local de 430 fontes/resultados,
SHA-256/CRC conferidos; inclui retrato dos documentos antes da nova amostragem.
Não substitui os originais ou backups externos. Gerador:
scripts/arquivar_resultados_monografia.py; não repetir para sobrescrever.

DIMENSIONADO/SEM SORTEIO: reports/nova_amostra_catalogo_v1 contém plano JSON,
alocação dos 82 gêneros, precisão das doze médias e cenários. Código:
scripts/40_preparar_nova_amostra.py → src/tcc_music_popularity/sample_redesign.py.
Entrada leve já consumida: perfis_grupos/resumo_numerico/frequencias_categoricas
da descrição 39. N=1.159.764, n=9.526; fonte CSV individual não foi lida pelo
agente. Protocolo/guia: docs/plano_nova_amostra_catalogo_v1.md e
docs/execucao_nova_amostra_catalogo_v1.md. Testes: tests/test_sample_redesign.py.
Verificação: reports/verificacao_nova_amostra_20261106.json.

PENDENTE MANUAL: 40 sortear lê CSV selado e grava
data/processed/nova_amostra_catalogo_v1/amostra_spotify.parquet (privado),
resumo_sorteio.json e comparacao_metadados/categorias.csv (agregados).
Consumidor seguinte: recuperação dirigida das letras, ainda não executada.

## Histórico — descrição do catálogo, D-029

CONCLUÍDO REAL pelo pesquisador/conferido: script 39_descrever_catalogo_completo.py e
catalog_description.py. Fonte: CSV original Spotify, somente leitura. Regras:
configs/quality_rules.yaml. Saídas em reports/descritiva_catalogo_completo_v1:
agregados CSV/JSON, guia e treze figuras PNG/SVG, sem linhas individuais.
Consumidores futuros: descrição inicial da monografia e dimensionamento de nova
amostra menor. Não consome coorte/letras/vetores/modelos ou LRCLIB.
Guia: docs/execucao_descritiva_catalogo_completo_v1.md. Evidências reais:
reports/verificacao_descritiva_catalogo_20261106.json e
reports/interpretacao_descritiva_catalogo_completo_v1.md. Quarenta e quatro
arquivos conferidos; treze figuras inspecionadas. Próximo consumidor é o
dimensionamento de nova amostra menor; não há sorteio novo nesta etapa.

## Arquivos da publicação — D-024

Publicação principal confirmada no commit 082a9a0; relatório agregado em
reports/publicacao_github_20261102.json. CI aprovada no commit 9b375a8.

README.md, requirements-cientificos.txt, .gitattributes/.gitignore, guias públicos
REPRODUCAO/HISTORICO_METODOLOGICO/PUBLICACAO_GITHUB, script 30 e git_publication.py
são entradas de consulta/publicação. Os códigos históricos com consumidores
permanecem. Oito arquivos de prévias/roteiros retirados do índice ficam locais,
assim como dados/modelos/cache/demonstrador/prévias pessoais. O mapa anterior
registra sua existência local e histórica, não inclusão automática no GitHub.

## Nova etapa de níveis — D-025, 04/11/2026

- ATIVO: configs/niveis_popularidade_200k_v1.json, popularity_levels.py, script 31,
  protocolo/guia. Agregados públicos em reports/niveis_popularidade_200k_v1/agregados/.
  Consumidores: diagnóstico de suporte/categorização e futura classificação ordinal.
- CONCLUÍDO em 05/11 pelo pesquisador: 31 previsoes; usa predicoes_externas.parquet e
  folds_5x3.parquet selados. Não abre modelos/vetores/letras ou cria splits.
- CONCLUÍDO pelo pesquisador v1.1: linkage_review_plan.py/script 32; usa resultados
  v2 projetados e até 240 consultas por chave nos caches v1/v2, sem dump/SSD.
  Fichas individuais em data/derived/private_linkage_review_200k_v1_1/; só alocação
  e resumo em reports/piloto_vinculacao_200k_v1_1/. Não altera aceitação existente.
  Pastas v1 contêm apenas selos/resumo incompleto da falha de tipos; preservadas.
- CONCLUÍDO: script 33/linkage_review_audit.py, triagem de 133 fichas; agregados em
  reports/triagem_piloto_vinculacao_200k_v1/, detalhes privados em
  data/derived/private_linkage_triage_200k_v1/. Não é revisão semântica humana.
- PRODUÇÃO REAL CONCLUÍDA/conferida, 20/20 partes: script 34/observed_classification.py,
  ordinal_classifier.py, config/protocolo/guia de classificação ordinal. Fontes:
  base/folds/vetores existentes, resumos 31/32/33. Novos modelos/probabilidades em
  data/derived/private_ordinal_classification_200k_v1/; agregados em
  reports/classificacao_ordinal_200k_v1/. Saídas smoke existentes: quatro modelos,
  uma referência e respectivas probabilidades/selos. Integral: vinte modelos,
  cinco referências, 480 ajustes internos e probabilidades globais 77.535 linhas.
- CONCLUÍDO: script 35/classification_diagnostics.py; só agregados e parâmetros
  de três modelos PCA, três figuras em diagnosticos_classificacao_ordinal_200k_v1/.
  Relatório interpretacao_classificacao_ordinal_200k_v1.md. Sem novo ajuste.
- CONCLUÍDO pelo pesquisador e conferido: script 36/decision_sensitivity.py,
  protocolo/guia de sensibilidade da regra p/pi. Fonte: probabilidades externas
  existentes; agregados novos em reports/sensibilidade_decisao_ordinal_200k_v1/.
  Saídas reais existentes, sem substituir as originais. 120 métricas/1.080 células.
- CONCLUÍDO pelo agente em 06/11: script 37/decision_analysis.py, agregados e
  inspeção delimitada da cauda 128/96; duas figuras em analise_sensibilidade_decisao_ordinal_v1/.
  Relatório interpretacao_sensibilidade_decisao_ordinal_v1.md; sem modelo/treino.
- ATIVO: reports/abertura_nova_etapa_20261104.md e verificacao_nova_etapa_20261104.json.
  Registro da preparação e preservação; não evidenciam novo treinamento.

O congelamento abaixo se refere à primeira comparação; a nova investigação foi
autorizada separadamente. Monografia v2/PDF/ZIP continuam preservados.

## Entrada acadêmica atual — D-028

ATIVO: reports/monografia_template_200k_v3/main.tex, ZIP correspondente e
output/pdf/monografia_template_200k_v3.pdf (45 páginas, 32 referências originais).
Consumidor: Overleaf/revisão com Leandro Tavares Correia. Script 38 prepara quatro
tabelas e copia duas figuras de CSVs/figuras públicos pequenos, sem bases individuais.
Objetivos incorporados à introdução; regressão, extensão ordinal/PCA e sensibilidade
posterior preservadas como etapas distintas. Verificação/revisão em reports/;
guia docs/execucao_monografia_template_200k_v3.md. Sem alteração de código ou
protocolo científicos. Fontes/PDF/ZIP da versão 2 passam a HISTÓRICO, intactos.

## Entrada acadêmica anterior — D-023

HISTÓRICO: reports/monografia_template_200k_v2/main.tex, ZIP correspondente e
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
