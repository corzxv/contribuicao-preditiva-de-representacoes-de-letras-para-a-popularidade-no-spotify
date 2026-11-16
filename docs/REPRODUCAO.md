# Reprodução do TCC

O repositório guarda a implementação e os agregados que sustentam a monografia.
Não inclui as bases individuais necessárias para refazer o treinamento. A
presença de um script não demonstra execução; as evidências estão nos resumos,
protocolos e relatórios de cada etapa. Os resultados principais estão congelados.

## Ambiente e fontes

Prioridade atual D-048. Para compilar a monografia, abrir
reports/monografia_template_overleaf/main.tex com XeLaTeX e BibTeX.
O ZIP de mesmo nome contém os CSVs e as figuras otimizadas para o Overleaf.
Para reproduzir os contrastes editoriais com semente 42, execute 58 com
`--somente-contrastes`. Use `--destino` para escrever em uma pasta separada.
O script 59 escreve agregados na pasta editorial e também gera os painéis
compactos com `--paineis-compactos PASTA`. Novas execuções estocásticas
adotam 42. A reprodução de resultados selados usa os parâmetros registrados.

`57_classificar_amostra_9526.py` foi concluído e
verificado. O protocolo está em protocolo_classificacao_9526_v1.md e a
interpretação em reports/classificacao_9526_v1/interpretacao_resultados.md.
55 foi concluído manualmente e verificado. 56 reuniu
os vínculos em uma candidata v2 com 9.526 faixas. O método e os resultados
estão em recuperacao_generos_deficitarios_v1.md.
A candidata de 9.526 faixas com letra foi gerada
e conferida pelo script 52_preparar_amostra_com_letras.py. Ver
amostra_com_letras_candidata_v1.md. 50 real concluído com 25 novas letras. 51 consolida
os vínculos por referência aos Parquet selados, com o script
51_consolidar_vinculos_nova_amostra.py. As tabelas públicas estão em
reports/recuperacao_consolidada_nova_amostra_v1.
47 real concluído pelo pesquisador, 58 novas aceitas.
48 real leve concluído, nove novas aceitas com revisão de catálogo. O script
48_registrar_variantes_artista_revisadas.py reproduz a exportação a partir das
decisões documentais privadas e do dump selado. Cobertura combinada em
reports/cobertura_pos_revisao_variantes_nova_amostra_v1.
Preservação acadêmica local em reports/preservacao_monografia_20261106 contém
430 arquivos, PDFs/fontes/agregados e hashes verificados. Não é backup externo.

O ambiente observado é Python 3.13 em Windows, com PowerShell. As versões estão
em `requirements-lock.txt` e `requirements-cientificos.txt`; o segundo acrescenta
NumPy/scikit-learn/SciPy, langid e bibliotecas do encoder. O encoder congelado é
`intfloat/multilingual-e5-small`, revisão
`614241f622f53c4eeff9890bdc4f31cfecc418b3`. A representação efetiva usa o prefixo
tokenizado separadamente e pooling de janelas descritos no protocolo; não se
declara reprodução exata da receita canônica.

O catálogo original é `data/raw/spotify/spotify_data.csv`, identificado por
SHA-256 nos relatórios de auditoria. Credenciais/caminhos locais podem ser
configurados em `.env` e `configs/data_sources.yaml`, ambos fora do Git;
`.env.example` e `configs/data_sources.example.yaml` não contêm credenciais.
O dump LRCLIB utilizado é o snapshot de 12/10/2026, em armazenamento externo
conforme `docs/dump_lrclib_ssd.md`. Não foi copiado para o repositório.

Os caminhos privados são saídas locais, e não arquivos faltantes que devam ser
publicados. Em outro computador, a reprodução exige obter as fontes, respeitar
suas condições, configurar os caminhos e executar a sequência manual. Os arquivos
em `data/raw` permanecem imutáveis. Não se transportam vetores entre textos ou
versões apenas por igualdade de ID.

## Sequência científica executada

| Entrada | Evidência de execução | Conteúdo |
| --- | --- | --- |
| 11 | `reports/auditoria_catalogo_spotify_20261031/` | 1.159.764 IDs, estrutura, qualidade e distribuições |
| 12 | `reports/amostra_spotify_200k_20261031/` | 200.000 faixas, 981 estratos, 499 ≥80 incluídas; pesos/alocação |
| 13 | `reports/busca_local_200k_20261031/` | Recuperação inicial no snapshot local |
| 14 | `reports/recuperacao_letras_200k_v2/` | Fonte final: 77.535 aceitas e destinos das demais |
| 15 | `reports/avaliacao_letras_200k_v3/` | Diagnóstico de 1.000 casos; aplicação integral não executada |
| 16 | `reports/parecer_letras_v2/` | Cobertura/seleção e diagnóstico de compatibilidade |
| 17 | `reports/prontidao_dados_200k_v1/` | Vínculos/hashes/linhagem antes das representações |
| 19 | `reports/descritores_textuais_200k_v1/` | 21 descritores, 77.051 textos distintos, componentes |
| 20 | `reports/embeddings_multilingues_200k_v1/` | 77.051 vetores de 384 dimensões, cobertura integral |
| 21 | `reports/base_modelagem_200k_v1/` | 77.535 faixas, 21.893 componentes, folds comuns 5×3 |
| 22 | `reports/modelagem_200k_v1/integral/` | 20 partes Ridge e dez referências; comparação concluída |
| 23 | `reports/diagnosticos_modelagem_200k_v1/` | Métricas reproduzidas e diagnósticos sem refit |
| 25–27 | `reports/fechamento_metodologico_200k_v1/` | Limites condicionais, cauda, clipping e auditoria E5 |

Preparação do dump/índices, coleta anterior e integração Spotify–LFM2b estão nos
scripts 01–10 e seus guias, mantidos como trajetória/dependências. Não são uma
ordem para executar novamente toda a história. O script 18 inventaria metadados.

## Regra de execução

O pesquisador executa manualmente downloads volumosos, varreduras, índices,
recuperação em escala, descritores/embeddings integrais e treinamento. O agente
prepara/revisa código, comandos, testes sintéticos e diagnósticos leves. Não usar
o comando histórico `tcc-music all` para simplesmente conferir o repositório.

Para uma futura reprodução autorizada, consultar o guia específico antes de
executar. Exemplos de entradas existentes, apresentados sem executar:

```powershell
# Auditoria e amostra: arquivos brutos e custo real exigem execução manual.
.\.venv\Scripts\python.exe scripts\11_auditar_catalogo_spotify.py
.\.venv\Scripts\python.exe scripts\12_sortear_amostra_spotify_200k.py

# Demais etapas: seguir os respectivos guias, checkpoints e critérios de retomada.
.\.venv\Scripts\python.exe scripts\21_preparar_base_modelagem_200k.py
.\.venv\Scripts\python.exe scripts\22_modelar_dominio_observado_200k.py --help
```

Os protocolos descrevem argumentos, orçamento, retomada e assinatura de entradas.
Uma instalação nova não deve aproveitar checkpoints incompatíveis ou presumir
que os pesos do desenho corrigem a disponibilidade de letras.

## Reprodução editorial

Scripts 24, 28 e 29 usam somente agregados públicos pequenos para preparar figuras
e tabelas. As dependências editoriais das versões anteriores foram preservadas
nos caminhos originais. O script `render_capitulo_modelagem_pdf.py` pertence ao
PDF parcial histórico e usa ReportLab; a versão atual é compilada de TeX, não por
esse renderizador. Sua dependência opcional pode ser instalada manualmente com
`python -m pip install -e ".[editorial]"`; as fontes Times usadas naquele PDF
histórico dependem do Windows. `resumir_cauda_auxiliar.py` produziu agregados complementares
da cauda sem ajustar modelos.

A versão atual é `reports/monografia_template_200k_v3/main.tex` (D-028, 45 páginas);
a versão 2 permanece intacta. O pacote ZIP
inclui os recursos e compila no Overleaf com XeLaTeX/BibTeX, sem precisar de
letras, bases, encoder ou modelos. Os exemplos de Ana e outros TCCs consultados
não são redistribuídos como se fossem trabalho deste autor.

O script 38 usa somente agregados públicos para quatro tabelas e duas figuras.
Não precisa ser executado para compilar o ZIP. Guia:
docs/execucao_monografia_template_200k_v3.md. Nenhum script científico ou
processamento pesado deve ser repetido para esta revisão acadêmica.

## Testes e bytes dos arquivos

```powershell
.\.venv\Scripts\python.exe -m pytest --ignore=tests/test_local_demo_ui.py
.\.venv\Scripts\python.exe scripts\30_auditar_publicacao_git.py
```

A suíte científica usa dados sintéticos pequenos; alguns testes ajustam modelos
somente nessas fixtures. Não são treinos do corpus real. O teste de interface do
demonstrador antigo fica fora da publicação porque a interface não integra a
análise principal. Helpers ainda importados permanecem disponíveis.

`.gitattributes` desativa conversão de quebras de linha para conservar hashes de
bytes em clones. Verificações de integridade da execução original devem ser
interpretadas junto ao ambiente e aos arquivos privados correspondentes; hashes
evidenciam identidade técnica, não qualidade semântica de correspondências.
# Nova etapa de níveis — 04/11/2026

Atualização D-027: 34 integral concluído/conferido, 35 agregados/PCA/figuras concluído.
Não repetir treino. 36 sensibilidade de decisão real concluído e 37 consolidado
em 06/11; guia execucao_sensibilidade_decisao_ordinal_v1.md. Relatórios atuais em
reports/interpretacao_classificacao_ordinal_200k_v1.md. Primeiros modelos/PDFs preservados.
Sensibilidade interpretada em reports/interpretacao_sensibilidade_decisao_ordinal_v1.md.

Atualização de 05/11/D-026: 31/32 reais concluídos, triagem técnica 33 feita apenas
em 133 fichas. 34 smoke e primeiro lote real concluídos/conferidos; próximo é
34 all sem limite para concluir as dezenove partes restantes. Código/protocolo de classificação ordinal
preparados e testados; nenhum novo ajuste real foi feito pelo agente. Guia atual:
docs/execucao_classificacao_ordinal_200k_v1.md. A primeira regressão permanece.

O guia docs/execucao_nova_etapa_niveis_v1.md reúne os comandos 31/32. A primeira
regressão permanece selada. Apenas `31 ... agregados` foi executado pelo agente
sobre tabelas públicas; os modos com tabelas individuais ficam para execução
manual. Não executar scripts antigos de busca/treino para continuar esta etapa.

Testes de preparação: test_popularity_levels.py e test_linkage_review_plan.py,
somente fixtures; lint/formatação e verificação em
reports/verificacao_nova_etapa_20261104.json. Referência metodológica em D-025.
