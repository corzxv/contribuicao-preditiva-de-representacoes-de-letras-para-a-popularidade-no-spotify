# Dicionário de dados — Base v0.1

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