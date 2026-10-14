# Auditoria da matriz comum v0.5

```json
{
  "development_rows": 7648,
  "holdout_rows": 2592,
  "development_artists": 3749,
  "holdout_artists": 1308,
  "overlap_counts": {
    "composition_key": 0,
    "artist_group_id": 0,
    "lyrics_sha256": 0
  },
  "row_multiplication": 0,
  "missing_embeddings": 0,
  "representatives_verified": true,
  "joins": "1:1 por composição, track_id e spotify_row_id",
  "feature_dimensions": {
    "baseline": 23,
    "lfm": 196,
    "embedding": 384
  },
  "holdout_target_loaded": false,
  "holdout_target_columns": [],
  "missing_by_feature_development": {
    "lfm_structure_chorus_repetitions": 3089,
    "lfm_structure_number_of_sections": 3089,
    "lfm_structure_number_of_verses": 3089,
    "lfm_structure_pattern_two_verses_at_least_one_chorus": 3089,
    "lfm_structure_pattern_verse_chorus_alternating": 3089,
    "lfm_structure_ratio_chorus_sections": 3089,
    "lfm_structure_ratio_verses_sections": 3089,
    "lfm_structure_starts_with_chorus": 3089
  },
  "missing_by_feature_holdout": {
    "lfm_structure_chorus_repetitions": 1061,
    "lfm_structure_number_of_sections": 1061,
    "lfm_structure_number_of_verses": 1061,
    "lfm_structure_pattern_two_verses_at_least_one_chorus": 1061,
    "lfm_structure_pattern_verse_chorus_alternating": 1061,
    "lfm_structure_ratio_chorus_sections": 1061,
    "lfm_structure_ratio_verses_sections": 1061,
    "lfm_structure_starts_with_chorus": 1061
  }
}
```

Hashes completos das matrizes e folds no selo agregado da execução. Joins usam chaves congeladas, sem mudar representantes. Ausências documentadas são tratadas no treino.
