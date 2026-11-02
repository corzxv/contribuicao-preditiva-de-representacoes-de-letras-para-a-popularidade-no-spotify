# Auditoria de dados — Base v0.1

Gerado em: `2026-08-18T01:54:42.185317+00:00`.

> Resultados abaixo são observados nos arquivos efetivamente processados. Benchmarks fornecidos são mostrados apenas como referência comparativa.

## Proveniência das entradas

| fonte | arquivo | bytes | sha256 | licença | status |
| --- | --- | --- | --- | --- | --- |
| spotify | data/raw/spotify/spotify_data.csv | 175822041 | 42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897 | Database: Open Database; Contents: © Original Authors | file_present_hash_computed |
| lfm2b | data/raw/lfm2b/full_dataset.json.gz | 690455174 | 0a7c3d52584c4f726fb4e06e62ce36f00ff1b428811561409e6941df8428d106 | CC-BY-4.0 | file_present_hash_computed |

## Spotify

Foram observadas **1,159,764** linhas e **61** colunas; 1,159,764 IDs, 64,158 artistas e anos de 2000 a 2023.

`spotify_popularity`: média 18.3831, mediana 15.0000, zeros 158,391 (13.6572%).

### Coortes observadas

| temporal_cohort | len |
| --- | --- |
| 2010-2019 | 514990 |
| 2000-2009 | 443801 |
| 2020-2023 | 200973 |

### Divergência frente aos benchmarks fornecidos

```json
{
  "rows_difference": 0,
  "track_ids_difference": 0,
  "artists_difference": 0,
  "genres_difference": 0,
  "popularity_zero_percentage_points_difference": -0.0028249999999996334,
  "popularity_mean_difference": 0.003122773253871003,
  "popularity_median_difference": 0.0
}
```

### Flags e problemas

```json
{
  "qf_track_id_invalid": 0,
  "qf_spotify_popularity_out_of_range": 0,
  "qf_year_implausible": 0,
  "qf_duration_nonpositive": 0,
  "qf_tempo_nonpositive": 1199,
  "qf_danceability_out_of_range": 0,
  "qf_energy_out_of_range": 0,
  "qf_speechiness_out_of_range": 0,
  "qf_acousticness_out_of_range": 0,
  "qf_instrumentalness_out_of_range": 0,
  "qf_liveness_out_of_range": 0,
  "qf_valence_out_of_range": 0,
  "qf_key_invalid": 0,
  "qf_mode_invalid": 0,
  "qf_time_signature_invalid": 0,
  "qf_any": 1199,
  "qf_track_id_duplicate": 0
}
```

Sinal heurístico de balanceamento artificial por gênero: **False**. A heurística não comprova o mecanismo de coleta e a base não deve ser descrita como amostra representativa de todo o Spotify.

## LFM2b

Foram observados **582,759** registros, **242** colunas e **209** colunas classificadas como descritores LFM2b.

Excesso de duplicatas da chave operacional: 0; excesso de artista+título: 0.

O campo original `popularity` foi preservado semanticamente como `genius_lyrics_views`; `lfm_playcount` permanece separado. O arquivo contém descritores derivados e não é tratado como corpus de letras integrais.

### Coortes observadas

| cohort | count |
| --- | --- |
| 2010-2019 | 360506 |
| 2000-2009 | 114078 |
| outside_main_period | 97638 |
| 2020-2023 | 10537 |

## Figuras

- [Músicas Spotify por ano](figures/spotify_tracks_by_year.png)
- [Músicas Spotify por coorte](figures/spotify_tracks_by_cohort.png)
- [Popularidade Spotify](figures/spotify_popularity_distribution.png)
- [Popularidade zero por coorte](figures/spotify_zero_popularity_by_cohort.png)
- [Principais gêneros](figures/spotify_top_genres.png)
- [Missingness](figures/spotify_missingness.png)

## Limitações

As métricas são snapshots das respectivas fontes. Não se combinam `spotify_popularity`, `genius_lyrics_views` e `lfm_playcount`. Correlações e comparações são descritivas e não causais.