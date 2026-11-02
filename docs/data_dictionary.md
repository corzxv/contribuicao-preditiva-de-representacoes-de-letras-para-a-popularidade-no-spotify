# Dicionário de dados — Base v0.1

## Adendo: fechamento auxiliar 25–27 (02/11/2026)

Nenhum schema de coorte/folds/embeddings/previsões foi alterado. Somente novos
agregados em reports/fechamento_metodologico_200k_v1/:

- `intervalos_condicionais_por_fold.csv`: weighting/contrast/outer_fold,
  delta_mae (pontos de popularity), se_cluster_conditional, denominator
  (n de faixas ou soma dos pesos), components, max_component_share;
  limites normais nominais e Bonferroni (família de dez por ponderação).
- `intervalos_condicionais_combinados.csv`: delta e extremos ponderados dos
  limites Bonferroni. full_training_uncertainty=false; não é IC da pipeline CV.
- `metrics_and_clipping.csv`: model/scope/n, MAE/RMSE original e clip[0,100],
  sensibilidade com pesos originais, contagens <0/>100. Não substitui saída 22.
- `tail_residuals.csv`: cauda y≥80, componentes, quantis de resíduo, médias/DP,
  somas/participações de erros. Resíduo=previsão−observado; negativo=subestimação.
  Quantis lineares NumPy; DP descritivo divisor n; share_global_absolute_error
  é fração [0,1], contribution_to_global_mae mantém denominador global.
- `tail_residual_histogram.csv`: intervalos [esquerda,direita), último inclui
  extremo direito; `negative_predictions.csv`, `tail_counts_by_fold.csv` e
  `complemento_cauda.json`: apenas estatísticas/contagens, sem identificadores.
- `auditoria_representacoes.json`: hashes de código/configuração, critérios,
  oito textos/21 descritores e onze frases artificiais. Diferenças de tokenização
  contêm só frases artificiais; nenhum texto/hash/ID individual do corpus público.
- `desvio_prefixo_sintetico.json`: quatro frases artificiais, cosseno/distância
  entre receitas de prefixo; não contém vetores e não mede impacto no MAE.

Clipping é sensibilidade exploratória fixa, não normalização de coluna original
nem treino alternativo. Limites auxiliares pressupõem independência de componentes
e regularidade não demonstradas pelo desenho de faixas com letras aceitas.

## Adendo: diagnósticos das previsões fixas (02/11/2026)

Script 23 executado e concluído: métricas/30 partes reproduzidas, 116 células
publicadas/77 com métricas omitidas. Não altera previsões, modelos,
resposta, pesos ou folds. perdas_componentes.parquet privado: text_component_id,
outer_fold, n, weight_sum, abs_* (soma de erros absolutos) e weighted_abs_*
(soma de peso original × erro absoluto) para seis variantes. Não contém letras.

Agregados públicos: métricas reproduzidas, diagnósticos por dimension/level/model,
n/components e métricas principais/ponderadas. Dimensões: fold, idioma/status,
banda de popularidade/período originais, gênero, evaluation_component_history_status.
Este status é detected_collision se qualquer membro tiver flag v0.6 positiva;
senão unknown_key se houver readiness_unknown_group; senão no_detected_collision.
Não presume independência histórica. Células <100 faixas ou <20 componentes
têm apenas contagens/motivo em celulas_pequenas.csv, sem excluir observações.

Sensibilidade de remoção de componente: deltas global/mínimo/máximo mantendo
previsões e modelos fixos; não é IC ou retreino. Diagnóstico de limites das
previsões inclui n abaixo de zero/acima de 100 e min/max por variante. Protocolo
posterior à leitura das métricas globais, exploratório; nenhum p-valor.

## Adendo: runner Ridge e previsões externas (01/11/2026)

Script 22 integral concluída: 20 partes Ridge/dez referências; 77.535 previsões
externas por variante, zero pendências, métricas globais disponíveis.
Cache privado novo em
private_regression_200k_v1: SQLite tuning(key,payload,sha256) por modo/externo/
bloco/interno/alpha; payload contém n, soma de erro absoluto e diagnósticos do
ajuste. Modelos joblib, previsões Parquet e manifestos por parte externa, com
hashes, signature, detalhes de treino/validação e alpha selecionado internamente.
Smoke/integral separados; smoke_verified.json é gate técnico sob o mesmo selo.

Integral completa produz predicoes_externas.parquet privado: track_id,
text_component_id, spotify_popularity, sampling_weight, outer_fold e prediction_*
para baseline/traditional/deep/combined/mean/median. Uma linha por faixa,
sem misturar smoke. Estratos e originais continuam na coorte 21, relacionáveis
por track_id; nenhuma letra/vetor/ID individual em relatórios públicos.

Públicos: métricas globais (n, mae, rmse, r2, mae_original_weight e contagem de
previsões fora de 0..100), cinco contrastes de delta_mae/delta_mae_original_weight
e alphas por bloco/externo. Pesos iguais no ajuste; ponderação só na avaliação
de sensibilidade. Delta negativo = menor erro do primeiro bloco do contraste.
R² com resposta constante é null, indefinido. Sem intervalo/p-valor nesta etapa.

## Adendo: base comum e folds do domínio observado (01/11/2026)

Script 21 executado e concluído em 8,323 s. coorte_modelagem.parquet preserva
todas as linhas/colunas da coorte de descritores e acrescenta spotify_popularity
(Float64, de popularity inteiro 0..100), model_year/model_danceability/model_energy/
model_loudness/model_speechiness/model_acousticness/model_instrumentalness/
model_liveness/model_valence/model_tempo/model_duration_ms (Float64) e
model_genre/model_key/model_mode/model_time_signature (String categórica).
Originais inalterados. Branco/nulo/inválido fica nulo só no campo model_*; regras
no protocolo_base_modelagem_200k_v1.md. metadados_invalidos.parquet privado:
track_id, source_column, reason; nenhum caso excluído. Resposta inválida interrompe.

folds_5x3.parquet privado: track_id, text_component_id, outer_fold Int8 0..4 e
inner_outer_0..4 Int8 0..2 nos respectivos treinos, -1 no teste externo. Folds
comuns por componentes da etapa 19, sem usar alvo/pesos. blocos.json contém
listas explícitas de 15 entradas de Baseline, 21 descritores, referência ao
armazenamento único de vetores de 384 dimensões e política D-017. Não usa nomes,
IDs, idioma, pesos, matching ou grupos como preditores. Metadados/invalidações,
features e folds são privados. Públicos: resumo/relatório e contagens de folds/
qualidade, sem IDs/textos/vetores. Nada treinado/transformado estatisticamente.

Pesos originais/estratos continuam nas colunas originais. Pesos iguais por faixa
no ajuste/métricas principais futuros; MAE não ponderado primário/seleção, RMSE
e R² complementares. MAE com sampling_weight somente como avaliação de
sensibilidade das mesmas previsões externas. Não constitui correção da seleção.

## Adendo: embeddings multilingues do domínio observado (01/11/2026)

Script 20 executado e integral concluída: 77.051 vetores, zero pendências.
Fontes: 77.535 linhas de
coorte_descritores.parquet e 77.051 inputs textuais normalizados. O schema de
descritores v1 não muda. Vetores privados smoke/integral:
`text_input_sha256` String única, `embedding` FixedSizeList(Float32,384),
`vector_sha256` String para integridade dos bytes float32.

Índice privado smoke/integral: track_id, lyrics_text_ref, text_input_sha256,
text_component_id, text_characters, lyrics_detected_language e
lyrics_language_status. Integral completo requer exatamente 77.535 faixas;
várias faixas podem compartilhar vetor, sem multiplicação no join. Metadados,
hashes/grupos/idioma não são preditores do encoder ou dos modelos finais.

SQLite separado em private_embeddings_200k_v1 reutiliza schema vectors do código
anterior: lyrics_sha256 (aqui o hash do input normalizado), config_sha256, vector,
vector_sha256, metadata e origin. Metadata contém contagens de tokens/chunks,
prefixo, pesos, tempo e recursos, sem tokens/textos. Meta guarda selo e
smoke_verified. Não importar vetores históricos por ID ou por dimensão igual.
Manifesto snapshot.json sela arquivos/revisão local; plano_smoke.json é privado.

Públicos: resumo/relatório em smoke e integral. Não contêm IDs, vetores, texto ou
hashes individuais. Detalhes em protocolo_embeddings_multilingues_200k_v1.md.

## Adendo: descritores/componentes do domínio observado (01/11/2026)

Script 19 executado e concluído: 77.535 linhas, 21 descritores, 21.893 componentes.
Saída privada
`private_text_descriptors_200k_v1/coorte_descritores.parquet`: todas as colunas e
linhas de `private_readiness_200k_v1/linhagem_aceitas.parquet`, mais
`text_input_sha256`, os 21 campos de `text_descriptors.FEATURES` e:

- `text_artist_group_key`: chave conservadora, com fallback literal para símbolos;
- `text_composition_group_key`: composição operacional existente, com fallback
  literal quando artista/título só têm símbolos;
- `text_group_unresolved`: artista/composição operacional não resolvido, sem exclusão;
- `text_component_id`: identificador de componente conexo por artista, composição,
  participação explícita e fingerprint textual estrito. Controle, não preditor/split.

`indice_textos.parquet` liga `lyrics_text_ref` a `text_input_sha256`, sem multiplicar
faixas. SQLite `features(text_hash,payload)` guarda somente números por input
normalizado; a tabela original de letras não muda. Descritores são lexicais e
estruturais operacionais, não equivalentes aos antigos LFM2b. Segmentos Unicode
não são palavras universais. Definições, denominadores zero e limites em
`contrato_representacoes_200k_v1.md`. Saídas públicas apenas agregadas.

## Adendo: pré-fechamento e continuidade (01/11/2026)

Script 17 executado e concluído: 77.535 vínculos auditados. Não cria nova
coorte, preditores ou splits. `private_readiness_200k_v1/linhagem_aceitas.parquet`
preserva todas as colunas/linhas/pesos das aceitas v2 e acrescenta:

| Campo | Regra / limite |
| --- | --- |
| readiness_composition_key / readiness_artist_key | Normalização operacional existente, só para colisões; não identidade universal |
| readiness_old_partition | Atribuição antiga por track_id; nula quando não localizado; não significa alvo avaliado |
| readiness_v06_evaluated_track | ID presente nas features do teste v0.6 efetivamente aberto |
| readiness_v06_composition_collision / readiness_v06_artist_collision | Colisão das chaves operacionais com o teste v0.6; não definem exclusão ou split |
| readiness_old_development_track / readiness_old_cohort_track | ID em matriz antiga v0.5 / coorte de desenvolvimento de 58.633 |
| readiness_unknown_group | Chave operacional ausente; não deve ser tratada como ausência de relação |

Checkpoint SQLite: `meta` (selo de entradas/código), `verified(query_id,raw_hash,
strict_hash)`; única decisão é integridade textual verificada, não reaceitação
semântica. Sumários públicos trazem contagens/idiomas/colisões, sem letras, IDs
ou hashes individuais. Amostra original de 200 mil permanece integral no arquivo
de origem. `project_inventory` só registra caminhos/tamanhos/datas/categorias;
não interpreta a existência de um arquivo como execução verificada.

## Adendo: avaliação v3 e parecer estatístico (01/11/2026)

V1/v2 não mudam. Workspace `private_sample_lyrics_200k_v3` reutiliza schema SQLite
v1; meta sela fontes/regras e registra avaliação concluída. Plano diagnóstico
privado: track_id, diagnostic_group/reason, diagnostic_N/n/probability/seed. A
probabilidade é do diagnóstico, separada de inclusion_probability/sampling_weight
da amostra científica. Resultado evaluate/apply privado guarda before/after,
reason, gain_stage, proposals e seconds. Evidências registram concordâncias
separadas de artista/título, duração, versão, colaboração e alternativas.

Saída integral: originais/desenho, bloco lyrics_* v3 e v2_lyrics_status. Aceitações
antigas podem mudar, com transições explícitas; nenhuma faixa removida. Letras:
accepted_text separado de plain_text_source/synced_text_source originais; hashes
de texto efetivo, fingerprint estrito, representação de comparação e proveniência.
Pares privados de revisão têm review_label/notes; não alimentam aceite automático.

Parecer, só agregados: diagnostico_equivalencia.csv informa group/weighted,
variable/kind/category, estimate/catalog_estimate, n/denominator, se/df,
variance_supported, difference/relative_difference/standardized_difference,
margin, IC90/95 e simultâneo, p_tost, conclusion e family_relevant. Sem pesos,
inferência refere-se à população inclinada pela alocação; primários são o domínio
aceito ponderado. Cobertura por estrato preserva n real e totais ponderados com
flags zero_coverage/few_accepted/small_group. Não introduz pesos recalibrados.

## Adendo: recuperação local v2 da amostra 200k (31/10/2026)

Saídas exclusivas em `data/derived/private_sample_lyrics_200k_v2/`; nenhuma mudança
no schema/arquivo v1. `resultados_faixas_200k.parquet` mantém as 200.000 linhas e
todos os campos originais/desenho. Acrescenta cópia de todas as colunas de resultado
anteriores com prefixo `v1_` (por exemplo, `v1_lyrics_status`), o bloco `lyrics_*`
do resultado atual e:

| Campo | Definição |
| --- | --- |
| `recovery_initial_diagnostic` | Motivo inicial: categorias de ambiguidade, crédito/título não localizado no índice v1, campo ausente ou símbolos apagados pela normalização v1. |
| `recovery_rule` | Combinação exclusiva de regras aplicadas à aceitação; `preserved_v1` para decisões protegidas. Não somar componentes sobrepostos como recuperações distintas. |
| `recovery_empty_ignored` | Número de candidatos compatíveis vazios desconsiderados na reavaliação. |
| `recovery_text_origin` | Texto simples original ou `derived_synced`; origem legada mantida na proveniência das aceitações v1. |
| `recovery_typography_sha256` | Fingerprint tipográfico privado adicional; não substitui o estrito. |
| `recovery_operational_limit` | Limite de candidatos/texto; ambiguidade operacional explicitada, não conflito de conteúdo. |
| `recovery_candidate_transformations_json` | Transformações dos candidatos elegíveis; chaves/perfis de recuperação também constam da evidência SQLite. |

Campos são anuláveis quando não avaliados/herdados, como em v1. `lyrics_rules_version`
é a versão efetiva da decisão: v1 nas aceitações/instrumentais preservados e v2
nas novas decisões. `lyrics_query_id` é chave operacional de consulta, não composição.

`letras_aceitas_200k.parquet`: `query_id` único, IDs LRCLIB/revisão, `accepted_text`
(texto efetivamente aceito), `plain_text_source` e `synced_text_source` (originais,
anuláveis), `text_sha256`/`strict_text_sha256` calculados sobre `accepted_text`,
`source_plain_sha256`/`source_synced_sha256` para as representações originais, e
`provenance_json` (fonte, regras, equivalência, representante, extração e vínculo
ao cache v1 quando usado). Quando plain falta, não preencher o original com texto
derivado: usar somente `accepted_text`. Ligação muitos-para-um, sem multiplicar
faixas. O estado usa `plain_text_source` como campo interno do exportador legado;
o Parquet final v2 faz a separação explícita entre original e derivado.

`state.sqlite` reutiliza tabelas v1 e acrescenta `recovery(query_id, old_query_id,
old_status, old_reason, phase)`, com fases cache/lookup/done. `meta.lookup_artists`
congela o universo do índice auxiliar para retomada. A inspeção privada JSON tem
até três consultas por método e campo `human_review: pending`.

Agregados novos: CSV de diagnóstico, transição, perdas, recuperação exclusiva e
instrumentais usam `n_tracks` e `sum_weights` (ou denominador ponderado explícito).
A comparação longa adiciona `phase` before/after aos campos da comparação v1.
Todos os status e rejeitados permanecem no resultado integral. Detalhes em
`docs/protocolo_recuperacao_letras_200k_v2.md`.

## Adendo: busca local da amostra Spotify 200k (31/10/2026)

`data/derived/private_sample_lyrics_200k_v1/resultados_faixas_200k.parquet`
preserva todos os campos/tipos originais da amostra e acrescenta o bloco abaixo.
Uma linha por `track_id`, inclusive não aceitas/pendentes; nenhuma faixa rejeitada
é descartada. Campos de resultado são anuláveis quando não avaliados; contagens
não conhecidas não equivalem a zero. Tipos numéricos/booleanos são inferidos na
exportação; uma coluna totalmente ausente pode ter tipo Parquet Null.

| Campo | Significado |
| --- | --- |
| `lyrics_query_id` | Hash privado da consulta exata de metadados; pode ligar várias faixas. Nulo se metadados insuficientes; não é chave universal de composição. |
| `lyrics_status` | `accepted`, `ambiguous`, `not_found`, `no_text`, `instrumental`, `insufficient_metadata`, `technical_error` ou `pending`. |
| `lyrics_reason`, `lyrics_method`, `lyrics_rules_version` | Motivo, método e versão do protocolo; sem copiar status antigos. |
| `lyrics_candidate_count`, `lyrics_candidate_present` | Número enumerado e existência de candidatos; limite incompleto pode ter existência verdadeira com contagem desconhecida. |
| `lyrics_text_present`, `lyrics_plain_present`, `lyrics_synced_present` | Disponibilidade de algum texto, texto simples ou sincronizado entre candidatos; não significa aceitação. |
| `lyrics_eligible_count`, `lyrics_equivalent_count` | Quantidade compatível e quantidade no conjunto estritamente equivalente aceito. |
| `lyrics_selected_lrclib_id`, `lyrics_selected_lyrics_id` | ID do registro LRCLIB e revisão de letra; instrumental pode ter referência sem texto aceito. |
| `lyrics_text_sha256`, `lyrics_strict_text_sha256` | Hash do texto original e fingerprint estrito, exclusivamente privados. |
| `lyrics_detected_language`, `lyrics_language_confidence`, `lyrics_language_status` | Idioma estimado, score não calibrado e estado do detector; não excluem texto. |
| `lyrics_text_ref` | Referência a `query_id` na tabela de letras; preenchida somente para `accepted`. |

`letras_aceitas_200k.parquet`, no mesmo diretório privado, tem uma linha por
consulta aceita: `query_id` (String única), `plain_text_source` (String original),
`synced_text_source` (String anulável, sem conversão), `lrclib_id` e
`lrclib_lyrics_id` (Int64), `text_sha256`, `strict_text_sha256` e `provenance_json`
(Strings). Proveniência inclui fonte/selo, regras, método, IDs equivalentes e
regra determinística do representante. Join muitos-para-um pela referência;
exportação verifica cardinalidade, hashes e vínculos antes de publicar.

O SQLite privado retém consultas/evidências, tentativas e execuções; a lista
integral de faixas permanece em `tracks`. Relatórios públicos contêm somente
agregados. CSV longo: `scope, section, variable, category, metric, value,
denominator`; escopos completos/aceitos/não aceitos/por status, sem/com pesos.
`n`/`n_observed` são casos reais; `total`/`count` ponderados são somas de pesos;
taxas usam denominadores explicitados. Regras e limitações constam de
`docs/protocolo_busca_local_200k.md`.

## Adendo: amostra Spotify 200k (31/10/2026)

Novo artefato local `amostra_spotify_200k.parquet`; não altera bases existentes.
Todas as colunas do CSV original são preservadas como String, inclusive o índice
de cabeçalho vazio. Derivações e campos de desenho são acrescentados:

| Campo | Tipo | Regra |
| --- | --- | --- |
| `stratum_id` | String | `C\|popularity>=80` ou `S\|` + vetor JSON compacto `[gênero, período, banda]`; ordem Unicode crescente. |
| `N_h`, `n_h` | Int64 | Tamanho populacional e alocação amostral do estrato. |
| `inclusion_probability` | Float64 | n_h/N_h; intervalo (0,1]. |
| `sampling_weight` | Float64 | N_h/n_h; soma na amostra igual a N do catálogo. |
| `certainty_selection` | Boolean | n_h=N_h, incluindo pequenos estratos integrais. |
| `seed` | Int64 | 20261031. |
| `sampling_track_id`, `sampling_genre` | String | Strings aparadas; originais `track_id` e `genre` permanecem intactos. |
| `sampling_period` | String | 2000–2009, 2010–2019, 2020–2023 a partir de `year`, sem afirmar lançamento original. |
| `sampling_popularity_band` | String | 0–19, 20–39, 40–59, 60–69, 70–79, 80–100. |

O CSV de comparação contém `scope` (`catalogo`, `amostra_sem_pesos`,
`amostra_com_pesos`), `section`, `variable`, `category`, `metric`, `value`,
`denominator`. Variáveis de distribuição `_s_pop`, `_s_band`, `_s_genre`,
`_s_year` e `_s_period` significam popularidade Spotify, banda, gênero, ano e
período analíticos, respectivamente. `n_observed` conta casos efetivos;
`count` soma pesos; `fraction` está em 0–1; `weight_observed` soma pesos de
valores válidos. Nos momentos, `denominator` é o total do escopo, enquanto
`weight_observed` é o denominador efetivamente usado. `q50` é a mediana pela
inversa da CDF empírica ponderada. `std_population` usa divisor soma(w), não é
erro-padrão. Contagens distintas de créditos/títulos são observadas, nunca
extrapoladas por soma de pesos.

Alocação inclui `reserved`, `remaining_capacity`, `remainder_numerator` e
`remainder_denominator` para reproduzir maiores restos. Regras e fórmulas em
`docs/plano_amostral_200k.md`; instruções em `docs/execucao_amostra_spotify_200k.md`.

## Adendo: auditoria do catálogo original (31/10/2026)

Sem alteração de schema das bases existentes. A nova CLI escreve apenas
relatórios agregados e usa campos temporários internos, preservando o CSV bruto.
Regras completas em `docs/auditoria_catalogo_spotify.md`.

| Campo/objeto | Tipo | Semântica da auditoria |
| --- | --- | --- |
| `popularity` original | texto CSV | Popularidade Spotify; não combinar com Genius/LFM. |
| `year` original | texto CSV | Ano informado; significado preciso e relação com lançamento original não confirmados. |
| `audit_id`, `audit_artist`, `audit_title`, `audit_genre` | VARCHAR temporário | Trim e tokens de ausência; valores originais preservados em outras colunas. |
| `audit_num_*` | DOUBLE temporário | Conversão tolerante; não finitos e falhas contados separadamente. |
| `audit_pop` | DOUBLE temporário | Popularidade finita inteira 0–100; demais valores NULL para os momentos, sem retirar linhas das contagens. |
| `audit_date_*` | DATE temporário | ISO de precisão variável na forma YYYY, YYYY-MM ou YYYY-MM-DD; anos 1900–2030 segundo regra local. Datas parciais ancoradas em dia/mês 1, sem atribuir precisão inexistente. |
| `audit_period` | VARCHAR temporário | Década de `year`, ou categoria de ausente/inválido. |
| `audit_pop_band` | VARCHAR temporário | 0–9, …, 80–89, 90–100; categorias separadas para ausente/inválido. |
| `audit_flag_*` | BOOLEAN temporário | Regex sobre título; flags de versão heurísticas e sobrepostas. |
| `scope` no CSV longo | texto | `linha`, `track_id_sem_conflito` ou `track_id` nas contagens de conflito por campo. |
| `section`, `dimension_1..3`, `value_1..3` | texto | Família de distribuição e até três dimensões/categorias. Sem nomes de artistas, títulos ou IDs individuais. |
| `metric`, `value`, `denominator` | texto/número/número | Métrica, valor e população da distribuição; denominador vazio quando não aplicável. `n_valid` é o denominador dos momentos, `fraction` varia de 0 a 1. |
| `status`, `completed` no JSON | texto/booleano | `incomplete`/false até terminar todas as saídas; `completed`/true ao concluir. |
| `code_version`, `code_sha256`, `wrapper_sha256`, `quality_rules`, `command_argv` | metadados JSON | Versão/hashes, regras e comando que geraram a auditoria. Git HEAD é complementar porque o código pode não estar commitado. |

As tabelas históricas da Base v0.1 abaixo mantêm sua granularidade original.

Gerado do schema observado. A base de modelagem tem uma linha por par Spotify–LFM2b aceito; campos Spotify e LFM2b preservam suas granularidades de origem.

| variável | origem | tipo | granularidade | semântica |
| --- | --- | --- | --- | --- |
| spotify_row_id | Spotify | UInt32 | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| artist_name | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| track_name | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| track_id | Spotify | String | registro de faixa Spotify | Identificador de faixa fornecido na fonte Spotify. |
| year | Spotify | Int64 | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| genre | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| danceability | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| energy | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| key | Spotify | Int64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| loudness | Spotify | Float64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| mode | Spotify | Int64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| speechiness | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| acousticness | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| instrumentalness | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| liveness | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| valence | Spotify | Float64 | registro de faixa Spotify | Descritor acústico Spotify na faixa esperada [0, 1]. |
| tempo | Spotify | Float64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| duration_ms | Spotify | Int64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| time_signature | Spotify | Int64 | registro de faixa Spotify | Descritor acústico/metadado fornecido pela fonte Spotify. |
| artist_name_raw | Spotify | String | registro de faixa Spotify | Artista original, preservado sem normalização. |
| track_name_raw | Spotify | String | registro de faixa Spotify | Título original, preservado sem normalização. |
| spotify_popularity | Spotify | Float64 | registro de faixa Spotify | Popularidade Spotify observada no snapshot da coleta; escala 0–100. |
| temporal_cohort | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| artist_unicode | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| artist_strict | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| artist_conservative | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| artist_primary | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| artist_collaborators_json | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| title_unicode | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| title_strict | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| title_conservative | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| title_base | Spotify | String | registro de faixa Spotify | Variante normalizada não destrutiva para matching. |
| remaster | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| remix | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| live | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| acoustic | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| radio_edit | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| mono_stereo | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| instrumental | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| demo | Spotify | Boolean | registro de faixa Spotify | Flag de versão inferida do título; informação original preservada. |
| year_mentioned | Spotify | Int64 | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| version_tags | Spotify | List(String) | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| composition_key | Spotify | String | registro de faixa Spotify | Chave operacional artista principal+título-base; não é identificador universal. |
| normalization_version | Spotify | String | registro de faixa Spotify | Campo preservado ou derivado; regra detalhada em docs/methodology_log.md. |
| qf_track_id_invalid | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_spotify_popularity_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_year_implausible | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_duration_nonpositive | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_tempo_nonpositive | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_danceability_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_energy_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_speechiness_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_acousticness_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_instrumentalness_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_liveness_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_valence_out_of_range | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_key_invalid | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_mode_invalid | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_time_signature_invalid | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_any | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| qf_track_id_duplicate | Spotify | Boolean | registro de faixa Spotify | Flag de qualidade; o registro é preservado. |
| artist_name_raw | LFM2b | VARCHAR | registro de descritores LFM2b | Artista original, preservado sem normalização. |
| genius_lyrics_views | LFM2b | BIGINT | registro de descritores LFM2b | Campo original LFM2b `popularity`: visualizações da letra no Genius. |
| lfm_affective_afinn_negativescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_afinn_positivescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_bingliu_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_bingliu_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_labmt_happiness | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_achieve | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_adverb | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_affect | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_anger | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_anx | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_apostro | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_article | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_assent | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_auxverb | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_avg_sentence_length | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_bio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_body | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_cause | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_certain | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_cogmech | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_colon | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_comma | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_conj | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_dash | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_death | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_dictionary_words | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_discrep | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_excl | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_exclam | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_family | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_feel | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_filler | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_friend | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_funct | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_future | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_health | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_hear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_home | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_humans | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_i | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_incl | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_ingest | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_inhib | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_insight | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_ipron | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_leisure | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_money | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_motion | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_negate | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_negemo | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_nonfl | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_number | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_numerals | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_otherp | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_parenth | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_past | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_percept | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_period | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_posemo | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_ppron | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_preps | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_present | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_pronoun | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_qmark | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_quant | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_quote | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_relativ | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_relig | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_sad | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_see | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_semic | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_sexual | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_shehe | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_six_letter_words | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_social | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_space | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_swear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_tentat | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_they | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_time | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_total_word_count | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_verb | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_we | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_work | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_liwc_you | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_mpqa_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_mpqa_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_negation_count | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_anger | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_anticipation | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_disgust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_fear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_joy | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_sadness | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_surprise | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcaffectintensity_trust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_anger | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_anticipation | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_disgust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_fear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_joy | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_sadness | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_surprise | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcemotionwordlevel_trust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_anger | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_anticipation | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_disgust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_fear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_joy | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_sadness | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_surprise | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrcexpandedemotion_trust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_anger | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_anticipation | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_disgust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_fear | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_joy | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_negative | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_positive | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_sadness | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_surprise | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagemotion_trust | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagsentiment_negativescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_nrchashtagsentiment_positivescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_sentiment140_negativescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_sentiment140_positivescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_sentiwordnet_negativescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_affective_sentiwordnet_positivescore | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor afetivo/emocional derivado das letras pelo LFM2b. |
| lfm_compression_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_entropy | LFM2b | DOUBLE | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_genre | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_lexical_average_token_length | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_average_tokens_per_line | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_blank_line_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_blank_line_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_character_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_colon_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_comma_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_digit_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_digit_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_dis_legomenon_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_dot_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_dugast | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_exclamation_mark_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_hapax_legomenon_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_herdan | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_hyphen_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_line_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_maas | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_mtld | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_parens_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_past_tense_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_pronoun_frequency | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_punctuation_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_punctuation_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_question_mark_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_quote_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_repeated_line_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_repeated_token_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_semicolon_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_stop_word_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_stop_word_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_stop_words_per_line | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_summer | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_token_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_tris_legomenon_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_unique_bigram_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_unique_line_count | LFM2b | BIGINT | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_unique_tokens_per_line | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_lexical_unique_trigram_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor lexical derivado das letras pelo LFM2b. |
| lfm_playcount | LFM2b | BIGINT | registro de descritores LFM2b | Número de eventos de escuta na base LFM-2b. |
| lfm_readability_automated_readability_index | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_coleman_liau_index | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_crawford | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_dale_chall_readability_score | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_difficult_words | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_fernandez_huerta | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_flesch_kincaid_grade | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_flesch_reading_ease | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_gunning_fog | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_gutierrez_polini | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_linsear_write_formula | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_smog | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_readability_szigriszt_pazos | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de legibilidade derivado das letras pelo LFM2b. |
| lfm_record_key | LFM2b | VARCHAR | registro de descritores LFM2b | Hash operacional do registro LFM2b; não é identificador universal. |
| lfm_release_date | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_release_date_numberlong | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_release_year | LFM2b | BIGINT | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_rhyme_alliterations_len_2 | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_alliterations_len_3 | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_alliterations_len_4_plus | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_num_alternating | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_num_clerihews | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_num_couplets | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_num_nested | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_rhyme_percent | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_rhyme_unique_rhyme_words | LFM2b | BIGINT | registro de descritores LFM2b | Descritor de rima/aliteração derivado das letras pelo LFM2b. |
| lfm_source_row_number | LFM2b | BIGINT | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_structure_chorus_repetitions | LFM2b | BIGINT | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_ends_with_two_chorus_repetitions | LFM2b | BOOLEAN | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_number_of_sections | LFM2b | BIGINT | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_number_of_verses | LFM2b | BIGINT | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_pattern_two_choruses_at_least_one_verse | LFM2b | BOOLEAN | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_pattern_two_verses_at_least_one_chorus | LFM2b | BOOLEAN | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_pattern_verse_chorus_alternating | LFM2b | BOOLEAN | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_ratio_chorus_sections | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_ratio_verses_sections | LFM2b | DOUBLE | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_starts_with_chorus | LFM2b | BOOLEAN | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_structure_title_occurrences | LFM2b | BIGINT | registro de descritores LFM2b | Descritor estrutural derivado das letras pelo LFM2b. |
| lfm_temporal_cohort | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_uncommon_words_ratio | LFM2b | DOUBLE | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| track_name_raw | LFM2b | VARCHAR | registro de descritores LFM2b | Título original, preservado sem normalização. |
| lfm_artist_unicode | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_artist_strict | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_artist_conservative | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_artist_primary | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_artist_collaborators_json | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_title_unicode | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_title_strict | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_title_conservative | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_title_base | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_remaster | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_remix | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_live | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_acoustic | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_radio_edit | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_mono_stereo | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_instrumental | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_demo | LFM2b | BOOLEAN | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_year_mentioned | LFM2b | BIGINT | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_version_tags | LFM2b | VARCHAR[] | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_composition_key | LFM2b | VARCHAR | registro de descritores LFM2b | Chave operacional artista principal+título-base; não é identificador universal. |
| lfm_normalization_version | LFM2b | VARCHAR | registro de descritores LFM2b | Campo da fonte LFM2b ou variante normalizada documentada pelo nome. |
| lfm_qf_release_year_implausible | LFM2b | BOOLEAN | registro de descritores LFM2b | Flag de qualidade; o registro é preservado. |

`spotify_popularity`, `genius_lyrics_views` e `lfm_playcount` são métricas distintas e não devem ser combinadas como um único desfecho.

## Camada de modelagem v0.1.1

O catálogo completo, gerado do schema real, está em `reports/feature_manifest_v0_1_1.csv`. A matriz `modeling_base_lfm_v0_1_1.parquet` tem 228 colunas:

| bloco | quantidade | observação |
| --- | ---: | --- |
| identificadores de auditoria | 3 | `spotify_row_id`, `track_id`, `lfm_record_key`; nunca preditores |
| agrupamento | 3 | `artist_group_id`, `composition_group_id`, `split_group_id`; somente controle de split |
| atribuição | 1 | `split`: `development_train` ou `holdout_test` |
| alvo | 1 | `spotify_popularity`, snapshot Spotify na escala 0–100 |
| preditoras autorizadas | 220 | 23 metadados/acústicas Spotify e 197 descritores LFM2b não constantes no desenvolvimento |

`artist_group_id` é derivado da normalização operacional do artista. `composition_group_id` identifica a chave operacional de composição, com substituto determinístico quando ela está ausente. `split_group_id` é o componente conexo usado para impedir que ligações por artista ou composição atravessem desenvolvimento e holdout. Nenhuma dessas chaves é um identificador universal.

As 12 colunas constantes removidas e todas as variáveis proibidas por leakage permanecem registradas no manifesto, com justificativa. O manifesto também registra tipo, família, ausências na base completa e no desenvolvimento, cardinalidade e decisão de inclusão.
