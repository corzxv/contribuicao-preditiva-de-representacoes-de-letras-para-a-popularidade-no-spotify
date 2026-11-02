# Base analítica ampliada — V0.9

Matriz exclusivamente de development_train original. Alvos do holdout não foram carregados, nem dos registros que ficaram fora da V0.6. Rodada exploratória, sem confirmação independente. Identificadores, alvos e detalhes por artista permanecem privados.

## Granularidade, elegibilidade e preservação

Faixas Spotify: 83,817; representantes por composição: 83,559; matriz comum: 7,648; composições adicionais: 75,911. Cada target é unido à própria faixa por IDs; não transferido para outra versão. Track_id é faixa da fonte; composition_key é agrupamento operacional; flags são indícios de versão. Nenhuma linha é removida por popularidade ou erro e nenhum alvo é imputado.

Sem chave de composição: 8 faixas, preservadas na matriz por track_id; sem participação na visão por composição. Linhas adicionais colapsadas pela regra antiga de representante: 250. IDs de faixa duplicados: 0; alvo ausente: 0; alvo não finito: 0; fora da escala nominal: 0 (não excluídos por valor).

A regra V0.4 de representante foi reutilizada sem alvo, letra ou embedding. Os representantes da coorte/reserva V0.4 e os 7.648 comuns V0.5 foram reconciliados; grupos, inputs e alvos dos comuns coincidem. Indicadores de coleta/qualidade/matching não são preditores. Year é somente o ano informado pela fonte, não lançamento original certificado; genre não recebe semântica inferida.

## Cobertura e faixas altas de popularidade

| Etapa | n | Composições | Artistas | ≥60 | ≥70 | ≥80 | Média | Máximo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| integrated_development_tracks | 83817 | 83559 | 10301 | 1667 | 327 | 46 | 27.13288 | 91.00000 |
| eligible_development_compositions | 83559 | 83559 | 10301 | 1663 | 327 | 46 | 27.12713 | 91.00000 |
| v04_main_selected | 10500 | 10500 | 4481 | 196 | 40 | 6 | 26.98200 | 91.00000 |
| v04_reserve_available | 1500 | 1500 | 1225 | 32 | 7 | 2 | 26.99533 | 83.00000 |
| v04_actually_queried | 11250 | 11250 | 4643 | 212 | 45 | 7 | 26.99298 | 91.00000 |
| v04_lyrics_accepted | 7648 | 7648 | 3749 | 125 | 27 | 1 | 25.99202 | 80.00000 |
| common_v05 | 7648 | 7648 | 3749 | 125 | 27 | 1 | 25.99202 | 80.00000 |
| additional_compositions | 75911 | 75911 | 9994 | 1538 | 300 | 45 | 27.24149 | 91.00000 |


Etapas não são parcelas aditivas: reserva disponível inclui registros não ativados; a consulta efetiva inclui principal e apenas reserva ativada. Limiares ≥60/≥70/≥80 se sobrepõem. O CSV contém faixas, gênero, cada ano, flags, status e tamanhos de grupo de artista, sempre com denominador. Distribuições por grupo individual estão em arquivo privado; nenhuma diferença é interpretada como causal.

Perda por não seleção/consulta na V0.4: 72,309 composições elegíveis. Entre as 11,250 consultadas, status abaixo. Ambiguidade não é ausência de letra; request_error é falha técnica, não rejeição científica da música.

Decomposição: 71.559 composições não selecionadas para principal/reserva e 750 da reserva não ativada somam as 72.309 não consultadas. Das 11.250 consultadas, 3.602 não chegaram à matriz comum: 2.522 ambiguidades (2.451 letras distintas + 71 conflitos de metadados), 492 `not_found`, 83 instrumentais e 505 falhas técnicas `request_error`. Todas essas composições continuam elegíveis para os blocos Baseline/Tradicional, sujeitos às exclusões de grupos de cada fold; não dependem de nova letra integral.

| Status V0.4 | n |
| --- | --- |
| accepted_exact_equivalent | 5305 |
| accepted_exact_unique | 2343 |
| ambiguous_distinct_lyrics | 2451 |
| ambiguous_metadata_conflict | 71 |
| instrumental | 83 |
| not_found | 492 |
| request_error | 505 |


## Ausências e qualidade

| Identificador | Ausentes | Distintos | Repetições |
| --- | --- | --- | --- |
| track_id | 0 | 83817 | 0 |
| spotify_row_id | 0 | 83817 | 0 |
| lfm_record_key | 0 | 83817 | 0 |


Registros LFM ligados a mais de uma faixa Spotify: 0; composições ligadas a mais de um grupo de artista: 0. Reutilização de um registro LFM não equivale automaticamente a duplicação de track_id; a visão experimental mantém um representante por composição operacional.

| Campo preditor | Ausentes nas faixas de desenvolvimento |
| --- | --- |
| lfm_structure_chorus_repetitions | 31534 |
| lfm_structure_number_of_sections | 31534 |
| lfm_structure_number_of_verses | 31534 |
| lfm_structure_pattern_two_verses_at_least_one_chorus | 31534 |
| lfm_structure_pattern_verse_chorus_alternating | 31534 |
| lfm_structure_ratio_chorus_sections | 31534 |
| lfm_structure_ratio_verses_sections | 31534 |
| lfm_structure_starts_with_chorus | 31534 |


Total de preditores com não finitos: 0. Grupos ausentes: {'artist_group_id': 0, 'composition_key': 8, 'composition_group_id': 0, 'split_group_id': 0}. Multiplicidade máxima observada de faixas por composition_key: 3. Imputação não ocorre na matriz; será aprendida em cada treino. Zero novas letras ou embeddings foram produzidos.

## Partições ampliadas auditadas antes dos ajustes

| Fold | Validação fixa | Treino comum original | Máximo ampliado | Linhas com hash conhecido |
| --- | --- | --- | --- | --- |
| 0 | 1529 | 6119 | 71519 | 7164 |
| 1 | 1529 | 6119 | 71258 | 7171 |
| 2 | 1528 | 6120 | 71112 | 7178 |
| 3 | 1529 | 6119 | 71052 | 7161 |
| 4 | 1533 | 6115 | 71135 | 7163 |


Artistas, composition_key, composition_group_id, split_group_id e hashes documentados foram excluídos do treino quando presentes na validação ou holdout original. Os máximos contêm integralmente o treino comum original. A auditoria por hash usa fontes históricas, sem abrir letras/vetores e sem recalcular hashes. Hash desconhecido não significa texto distinto: contaminação textual não observável continua limitação.

## Dicionário e proveniência dos novos artefatos privados

`tracks.parquet`: uma linha por track_id; IDs de origem, grupos/split originais, alvo da faixa, 23+196 inputs congelados, metadados de origem, matching e qualidade. `composition_key_available`, `is_operational_representative` e `in_common_v05` indicam elegibilidade/representação/presença anterior. `sampling_role`, `reserve_batch`, `final_status`, `lyrics_accepted_v04` documentam seleção/coleta; `not_selected` e `not_queried` distinguem ausência de participação de fracasso de consulta. `known_hash_count` conta pares tipo/hash conhecidos, não quantidade de letras independentes. Nenhum desses indicadores documentais entra em X.

`representatives.parquet`: subconjunto com representante anterior de cada composição, mesma popularidade da faixa selecionada. `common.parquet`: somente inputs Baseline/Tradicional, chaves, alvo já autorizado e folds V0.5, sem embeddings. `hash_catalog.parquet`: relações track/composição/tipo/hash/fonte/split, apenas metadados; namespaces não são intercambiáveis. `partition_plan.json`: índices privados, sementes, tamanhos, assinaturas e exclusões. `coverage_artist_groups.parquet`: estatísticas por artista, privadas. Predições/checkpoints serão escritos somente no diretório novo V0.9.

Nenhuma normalização ou correção de year/genre/flags foi aplicada. Preservam-se imperfeições de identidade e possibilidade de descritores/textos representarem versões diferentes. A inclusão ampliada não depende de disponibilidade de letra integral.
