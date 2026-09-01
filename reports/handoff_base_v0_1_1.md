# Handoff — Base v0.1.1

Gerado em `2026-09-01T00:10:37.202464+00:00`. Nenhuma coleta de letras, scraping, embedding, PCA definitivo, treinamento ou tuning foi realizado.

## 1. Contagens antes e depois

- Base v0.1: **111,758 linhas × 310 colunas**.
- Base v0.1.1 controlada: **111,758 linhas × 228 colunas**.
- Linhas removidas: **0**.
- Split e auditoria preservam os **111,758** pares aceitos.

## 2. Número final de linhas e colunas

O arquivo `modeling_base_lfm_v0_1_1.parquet` possui **111,758 × 228**.

## 3. Número confirmado de descritores

Foram confirmados **209 descritores líricos**. A contagem 231 do inventário preliminar incluía indevidamente 22 campos de normalização, versão e chaves; as 242 colunas LFM2b no integrado se dividem em 209 descritores e 33 não descritores.

## 4. Variáveis constantes removidas

Foram removidas **12** preditoras constantes: `lfm_affective_liwc_numerals`, `lfm_affective_nrcaffectintensity_anticipation`, `lfm_affective_nrcaffectintensity_disgust`, `lfm_affective_nrcaffectintensity_negative`, `lfm_affective_nrcaffectintensity_positive`, `lfm_affective_nrcaffectintensity_surprise`, `lfm_affective_nrcaffectintensity_trust`, `lfm_affective_nrchashtagemotion_negative`, `lfm_affective_nrchashtagemotion_positive`, `lfm_structure_ends_with_two_chorus_repetitions`, `lfm_structure_pattern_two_choruses_at_least_one_verse`, `lfm_uncommon_words_ratio`.

## 5. Tratamento proposto para ausências

Ausências não foram substituídas por zero. O plano é criar indicador de ausência, ajustar imputação somente em `development_train`, executar análise de sensibilidade e avaliar o bloco estrutural separadamente. Nenhuma estatística de imputação ou escala foi calculada antes do split.

## 6. Inconsistências encontradas

- Divergências nas contagens centrais entre Parquet, `run_summary`, auditorias, matching e Excel: **0**.
- Divergência semântica resolvida: 231 campos do inventário preliminar versus 209 descritores confirmados.
- O Excel anterior recomendava 222 preditoras por uma classificação exploratória; a v0.1.1 usa protocolo explícito, inclui metadados baseline autorizados e remove constantes somente com base em `development_train`.

## 7. Auditoria temporal

- Média/mediana/desvio-padrão da diferença absoluta: **2.092718 / 0.000000 / 20.626956** anos.
- Mínimo/máximo: **0 / 2018**.
- Quantis: `{"0.01": 0.0, "0.05": 0.0, "0.25": 0.0, "0.5": 0.0, "0.75": 0.0, "0.95": 13.0, "0.99": 38.0}`.
- Faixas: `[{"temporal_band": "diferença 0", "len": 90094, "percent": 80.61525796810966}, {"temporal_band": "1–2 anos", "len": 9690, "percent": 8.670520231213873}, {"temporal_band": "3–5 anos", "len": 2605, "percent": 2.3309293294439772}, {"temporal_band": "6–10 anos", "len": 2624, "percent": 2.3479303495051806}, {"temporal_band": "11–20 anos", "len": 3128, "percent": 2.7989047763918466}, {"temporal_band": "mais de 20 anos", "len": 3617, "percent": 3.236457345335457}]`.
- Ano ausente para o cálculo: **0 (0.000000%)**.
- Diferença temporal não foi classificada automaticamente como erro.

## 8. Auditoria de versões

`{"original_no_version_flag": {"count": 105638, "percent": 94.52388195923335}, "remaster": {"count": 571, "percent": 0.5109253923656472}, "remix": {"count": 1843, "percent": 1.6490989459367562}, "live": {"count": 2624, "percent": 2.3479303495051806}, "acoustic": {"count": 460, "percent": 0.41160364358703627}, "radio_edit": {"count": 191, "percent": 0.17090499114157376}, "mono_stereo": {"count": 69, "percent": 0.06174054653805544}, "instrumental": {"count": 177, "percent": 0.15837792372805526}, "demo": {"count": 295, "percent": 0.26396320621342545}}`

## 9. Casos sem chave de composição

Confirmados **22** casos sem `composition_key` Spotify e **22** sem chave LFM correspondente. Foram preservados com fallback determinístico por `track_id`.

## 10. Composição do treino e teste

- `development_train`: **83,817** linhas.
- `holdout_test`: **27,941** linhas.
- Grupos: `{"artist_group_id": 13901, "composition_group_id": 111444, "split_group_id": 13901}`.

## 11. Percentual real destinado ao teste

**25.001342%**.

## 12. Ausência de sobreposição

Sobreposição observada: `{"artist_group_id": 0, "composition_group_id": 0, "split_group_id": 0}`. Todos os valores são zero.

## 13. Variáveis permitidas nos quatro modelos

- Baseline (23): `year`, `genre`, `remaster`, `remix`, `live`, `acoustic`, `radio_edit`, `mono_stereo`, `instrumental`, `demo`, `danceability`, `energy`, `key`, `loudness`, `mode`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo`, `duration_ms`, `time_signature`.
- Tradicional (220): baseline + 197 descritores tradicionais não constantes.
- Profundo: baseline + embeddings futuros; ainda indisponível.
- Combinado: baseline + descritores tradicionais + embeddings futuros; ainda indisponível.

Os quatro modelos usarão a mesma amostra comum e os mesmos splits.

## 14. Variáveis proibidas

Proibições explícitas e classes proibidas: `acceptance_reason`, `artist_collaborators_json`, `artist_conservative`, `artist_name`, `artist_name_raw`, `artist_primary`, `artist_strict`, `artist_unicode`, `composition_key`, `genius_lyrics_views`, `lfm_artist_collaborators_json`, `lfm_artist_conservative`, `lfm_artist_name_raw`, `lfm_artist_primary`, `lfm_artist_strict`, `lfm_artist_unicode`, `lfm_composition_key`, `lfm_playcount`, `lfm_record_key`, `lfm_source_row_number`, `lfm_title_base`, `lfm_title_conservative`, `lfm_title_strict`, `lfm_title_unicode`, `lfm_track_name_raw`, `match_method`, `match_score`, `match_status`, `matching_version`, `spotify_row_id`, `temporal_compatible`, `title_base`, `title_conservative`, `title_strict`, `title_unicode`, `track_id`, `track_name`, `track_name_raw`, `version_compatible`. Além delas, IDs, nomes, títulos, chaves técnicas e qualquer coluna com “modelo em que poderá entrar = nenhum” no manifesto não podem compor o vetor de preditores.

## 15. Decisões pendentes de revisão humana

- Rotular 225 linhas em `match_review_sample_v0_1_1.xlsx`.
- Revisar especialmente incompatibilidades temporais, chaves ausentes, `mono_stereo`, `demo`, ambiguidades e fuzzy.
- Definir, no treino, a estratégia final para ausência estrutural e transformações.

## 16. Resultado real dos testes

Status: **aprovado**.

| comando | código de saída | resultado |
| --- | --- | --- |
| .\.venv\Scripts\python.exe -m tcc_music_popularity.cli prepare-v011 | 0 | segunda execução completa; quatro hashes reprodutíveis e Base v0.1 imutável |
| .\.venv\Scripts\python.exe -m pytest -q | 0 | 14 testes aprovados |
| .\.venv\Scripts\python.exe -m ruff check . | 1 | B018 apenas em exp_base.py:8, arquivo exploratório pré-existente e não versionado; preservado sem alteração |
| .\.venv\Scripts\python.exe -m ruff check . --exclude exp_base.py | 0 | pipeline, testes e demais arquivos aprovados |
| .\.venv\Scripts\python.exe -m ruff format --check . | 0 | 36 arquivos já formatados |
| verificação ZIP/OOXML somente leitura de reports/match_review_sample_v0_1_1.xlsx | 0 | ZIP íntegro; filtro e painel congelado presentes; duas validações de lista presentes; 225 rótulos humanos em branco |

## 17. Comandos executados e códigos de saída

Os comandos e códigos reais aparecem na tabela acima e em `run_summary_v0_1_1.json`.

## 18. Problemas conhecidos

- 225 classificações humanas permanecem vazias.
- 16 pares têm flag de ano LFM implausível e foram preservados.
- O bloco estrutural tem ausência estrutural; imputação e sensibilidade ficam para o treino.
- Modelos profundo e combinado aguardam letras integrais e embeddings.
- A população inferencial é o subconjunto Spotify–LFM2b matched, não todo o Spotify.
- O Ruff completo encontra B018 em exp_base.py:8; esse arquivo exploratório pré-existente e não versionado foi preservado, enquanto pipeline e testes passam no Ruff.

## 19. Classificação

**PRONTA COM RESSALVAS.** A base, o manifesto e o split estão tecnicamente preparados para o próximo piloto, mas a revisão humana de matching e as decisões de ausência/representação ainda precisam ser concluídas antes dos modelos finais.
