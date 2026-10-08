# Blocos de variáveis — Modelagem piloto v0.3

As listas abaixo foram reconciliadas com `feature_manifest_v0_1_1_revision.csv` antes do treinamento.
As contagens são anteriores a imputação, indicadores de ausência, one-hot encoding e remoção de variância zero.

## Contagens

| Bloco | Baseline | LFM2b | MiniLM | Total |
|---|---|---|---|---|
| Baseline | 23 | 0 | 0 | 23 |
| Tradicional | 23 | 196 | 0 | 219 |
| Profundo | 23 | 0 | 384 | 407 |
| Combinado | 23 | 196 | 384 | 603 |

## Baseline — 23 variáveis

`year`, `genre`, `danceability`, `energy`, `key`, `loudness`, `mode`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo`, `duration_ms`, `time_signature`, `remaster`, `remix`, `live`, `acoustic`, `radio_edit`, `mono_stereo`, `instrumental`, `demo`

## Descritores tradicionais autorizados — 196 variáveis

### afetivo/emocional — 125

`lfm_affective_afinn_negativescore`, `lfm_affective_afinn_positivescore`, `lfm_affective_bingliu_negative`, `lfm_affective_bingliu_positive`, `lfm_affective_labmt_happiness`, `lfm_affective_liwc_achieve`, `lfm_affective_liwc_adverb`, `lfm_affective_liwc_affect`, `lfm_affective_liwc_anger`, `lfm_affective_liwc_anx`, `lfm_affective_liwc_apostro`, `lfm_affective_liwc_article`, `lfm_affective_liwc_assent`, `lfm_affective_liwc_auxverb`, `lfm_affective_liwc_avg_sentence_length`, `lfm_affective_liwc_bio`, `lfm_affective_liwc_body`, `lfm_affective_liwc_cause`, `lfm_affective_liwc_certain`, `lfm_affective_liwc_cogmech`, `lfm_affective_liwc_colon`, `lfm_affective_liwc_comma`, `lfm_affective_liwc_conj`, `lfm_affective_liwc_dash`, `lfm_affective_liwc_death`, `lfm_affective_liwc_dictionary_words`, `lfm_affective_liwc_discrep`, `lfm_affective_liwc_excl`, `lfm_affective_liwc_exclam`, `lfm_affective_liwc_family`, `lfm_affective_liwc_feel`, `lfm_affective_liwc_filler`, `lfm_affective_liwc_friend`, `lfm_affective_liwc_funct`, `lfm_affective_liwc_future`, `lfm_affective_liwc_health`, `lfm_affective_liwc_hear`, `lfm_affective_liwc_home`, `lfm_affective_liwc_humans`, `lfm_affective_liwc_i`, `lfm_affective_liwc_incl`, `lfm_affective_liwc_ingest`, `lfm_affective_liwc_inhib`, `lfm_affective_liwc_insight`, `lfm_affective_liwc_ipron`, `lfm_affective_liwc_leisure`, `lfm_affective_liwc_money`, `lfm_affective_liwc_motion`, `lfm_affective_liwc_negate`, `lfm_affective_liwc_negemo`, `lfm_affective_liwc_nonfl`, `lfm_affective_liwc_number`, `lfm_affective_liwc_otherp`, `lfm_affective_liwc_parenth`, `lfm_affective_liwc_past`, `lfm_affective_liwc_percept`, `lfm_affective_liwc_period`, `lfm_affective_liwc_posemo`, `lfm_affective_liwc_ppron`, `lfm_affective_liwc_preps`, `lfm_affective_liwc_present`, `lfm_affective_liwc_pronoun`, `lfm_affective_liwc_qmark`, `lfm_affective_liwc_quant`, `lfm_affective_liwc_quote`, `lfm_affective_liwc_relativ`, `lfm_affective_liwc_relig`, `lfm_affective_liwc_sad`, `lfm_affective_liwc_see`, `lfm_affective_liwc_semic`, `lfm_affective_liwc_sexual`, `lfm_affective_liwc_shehe`, `lfm_affective_liwc_six_letter_words`, `lfm_affective_liwc_social`, `lfm_affective_liwc_space`, `lfm_affective_liwc_swear`, `lfm_affective_liwc_tentat`, `lfm_affective_liwc_they`, `lfm_affective_liwc_time`, `lfm_affective_liwc_total_word_count`, `lfm_affective_liwc_verb`, `lfm_affective_liwc_we`, `lfm_affective_liwc_work`, `lfm_affective_liwc_you`, `lfm_affective_mpqa_negative`, `lfm_affective_mpqa_positive`, `lfm_affective_negation_count`, `lfm_affective_nrcaffectintensity_anger`, `lfm_affective_nrcaffectintensity_fear`, `lfm_affective_nrcaffectintensity_joy`, `lfm_affective_nrcaffectintensity_sadness`, `lfm_affective_nrcemotionwordlevel_anger`, `lfm_affective_nrcemotionwordlevel_anticipation`, `lfm_affective_nrcemotionwordlevel_disgust`, `lfm_affective_nrcemotionwordlevel_fear`, `lfm_affective_nrcemotionwordlevel_joy`, `lfm_affective_nrcemotionwordlevel_negative`, `lfm_affective_nrcemotionwordlevel_positive`, `lfm_affective_nrcemotionwordlevel_sadness`, `lfm_affective_nrcemotionwordlevel_surprise`, `lfm_affective_nrcemotionwordlevel_trust`, `lfm_affective_nrcexpandedemotion_anger`, `lfm_affective_nrcexpandedemotion_anticipation`, `lfm_affective_nrcexpandedemotion_disgust`, `lfm_affective_nrcexpandedemotion_fear`, `lfm_affective_nrcexpandedemotion_joy`, `lfm_affective_nrcexpandedemotion_negative`, `lfm_affective_nrcexpandedemotion_positive`, `lfm_affective_nrcexpandedemotion_sadness`, `lfm_affective_nrcexpandedemotion_surprise`, `lfm_affective_nrcexpandedemotion_trust`, `lfm_affective_nrchashtagemotion_anger`, `lfm_affective_nrchashtagemotion_anticipation`, `lfm_affective_nrchashtagemotion_disgust`, `lfm_affective_nrchashtagemotion_fear`, `lfm_affective_nrchashtagemotion_joy`, `lfm_affective_nrchashtagemotion_sadness`, `lfm_affective_nrchashtagemotion_surprise`, `lfm_affective_nrchashtagemotion_trust`, `lfm_affective_nrchashtagsentiment_negativescore`, `lfm_affective_nrchashtagsentiment_positivescore`, `lfm_affective_sentiment140_negativescore`, `lfm_affective_sentiment140_positivescore`, `lfm_affective_sentiwordnet_negativescore`, `lfm_affective_sentiwordnet_positivescore`

### diversidade — 15

`lfm_compression_ratio`, `lfm_lexical_dis_legomenon_ratio`, `lfm_lexical_dugast`, `lfm_lexical_hapax_legomenon_ratio`, `lfm_lexical_herdan`, `lfm_lexical_maas`, `lfm_lexical_mtld`, `lfm_lexical_repeated_line_ratio`, `lfm_lexical_repeated_token_ratio`, `lfm_lexical_summer`, `lfm_lexical_tris_legomenon_ratio`, `lfm_lexical_unique_bigram_ratio`, `lfm_lexical_unique_line_count`, `lfm_lexical_unique_tokens_per_line`, `lfm_lexical_unique_trigram_ratio`

### estrutura — 9

`lfm_structure_chorus_repetitions`, `lfm_structure_number_of_sections`, `lfm_structure_number_of_verses`, `lfm_structure_pattern_two_verses_at_least_one_chorus`, `lfm_structure_pattern_verse_chorus_alternating`, `lfm_structure_ratio_chorus_sections`, `lfm_structure_ratio_verses_sections`, `lfm_structure_starts_with_chorus`, `lfm_structure_title_occurrences`

### legibilidade — 13

`lfm_readability_automated_readability_index`, `lfm_readability_coleman_liau_index`, `lfm_readability_crawford`, `lfm_readability_dale_chall_readability_score`, `lfm_readability_difficult_words`, `lfm_readability_fernandez_huerta`, `lfm_readability_flesch_kincaid_grade`, `lfm_readability_flesch_reading_ease`, `lfm_readability_gunning_fog`, `lfm_readability_gutierrez_polini`, `lfm_readability_linsear_write_formula`, `lfm_readability_smog`, `lfm_readability_szigriszt_pazos`

### lexical — 25

`lfm_lexical_average_token_length`, `lfm_lexical_average_tokens_per_line`, `lfm_lexical_blank_line_count`, `lfm_lexical_blank_line_ratio`, `lfm_lexical_character_count`, `lfm_lexical_colon_count`, `lfm_lexical_comma_count`, `lfm_lexical_digit_count`, `lfm_lexical_digit_ratio`, `lfm_lexical_dot_count`, `lfm_lexical_exclamation_mark_count`, `lfm_lexical_hyphen_count`, `lfm_lexical_line_count`, `lfm_lexical_parens_count`, `lfm_lexical_past_tense_ratio`, `lfm_lexical_pronoun_frequency`, `lfm_lexical_punctuation_count`, `lfm_lexical_punctuation_ratio`, `lfm_lexical_question_mark_count`, `lfm_lexical_quote_count`, `lfm_lexical_semicolon_count`, `lfm_lexical_stop_word_count`, `lfm_lexical_stop_word_ratio`, `lfm_lexical_stop_words_per_line`, `lfm_lexical_token_count`

### rima — 9

`lfm_rhyme_alliterations_len_2`, `lfm_rhyme_alliterations_len_3`, `lfm_rhyme_alliterations_len_4_plus`, `lfm_rhyme_num_alternating`, `lfm_rhyme_num_clerihews`, `lfm_rhyme_num_couplets`, `lfm_rhyme_num_nested`, `lfm_rhyme_rhyme_percent`, `lfm_rhyme_unique_rhyme_words`

## Embeddings MiniLM — 384 variáveis

Dimensões `embedding_000` a `embedding_383`, derivadas exclusivamente das letras aceitas na v0.2.

## Exclusões e papéis auxiliares

`spotify_popularity` é somente o alvo. `artist_group_id` é somente a chave de agrupamento. `composition_key`, `track_id`, `composition_group_id` e `split_group_id` são somente auditoria. `detected_language` e `language_status` são somente sensibilidade. `lfm_entropy`, `genius_lyrics_views`, `lfm_playcount`, textos, hashes, IDs LRCLIB e campos de matching/coleta não entram como preditores.
