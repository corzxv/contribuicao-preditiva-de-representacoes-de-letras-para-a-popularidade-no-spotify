# Auditoria temporal revisada — Base v0.1.1

## Escopo e decisão

Esta revisão é incremental e não destrutiva. Os 111.758 pares aceitos foram preservados; nenhum ano Spotify foi alterado e nenhum match foi automaticamente classificado como incorreto. Anos LFM implausíveis continuam registrados no dado e são tratados como ausentes **somente nas estatísticas temporais válidas**.

Critério operacional já implementado em `src/tcc_music_popularity/lfm2b.py`: `lfm_release_year < 1850` ou `lfm_release_year > 2030`. O critério detectou **16** casos no conjunto matched.

## Estatísticas brutas

| métrica | valor |
| --- | --- |
| diferenças válidas | 111758 |
| ausentes para estatística | 0 |
| média | 2.092718 |
| mediana | 0.000000 |
| desvio-padrão amostral | 20.626956 |
| mínimo | 0 |
| máximo | 2018 |
| quantil 0.01 | 0.000000 |
| quantil 0.05 | 0.000000 |
| quantil 0.25 | 0.000000 |
| quantil 0.5 | 0.000000 |
| quantil 0.75 | 0.000000 |
| quantil 0.95 | 13.000000 |
| quantil 0.99 | 38.000000 |

### Faixas brutas

| faixa | n | % de 111.758 |
| --- | --- | --- |
| diferença 0 | 90094 | 80.615258% |
| 1–2 anos | 9690 | 8.670520% |
| 3–5 anos | 2605 | 2.330929% |
| 6–10 anos | 2624 | 2.347930% |
| 11–20 anos | 3128 | 2.798905% |
| mais de 20 anos | 3617 | 3.236457% |

## Estatísticas válidas após desconsiderar anos implausíveis

| métrica | valor |
| --- | --- |
| diferenças válidas | 111742 |
| ausentes para estatística | 16 |
| média | 1.891133 |
| mediana | 0.000000 |
| desvio-padrão amostral | 6.804583 |
| mínimo | 0 |
| máximo | 150 |
| quantil 0.01 | 0.000000 |
| quantil 0.05 | 0.000000 |
| quantil 0.25 | 0.000000 |
| quantil 0.5 | 0.000000 |
| quantil 0.75 | 0.000000 |
| quantil 0.95 | 13.000000 |
| quantil 0.99 | 37.000000 |

### Faixas válidas

| faixa | n | % de 111.758 |
| --- | --- | --- |
| diferença 0 | 90094 | 80.615258% |
| 1–2 anos | 9690 | 8.670520% |
| 3–5 anos | 2605 | 2.330929% |
| 6–10 anos | 2624 | 2.347930% |
| 11–20 anos | 3128 | 2.798905% |
| mais de 20 anos | 3601 | 3.222141% |
| ano ausente ou implausível | 16 | 0.014317% |

## Lista integral dos 16 anos LFM implausíveis

| caso | spotify_row_id | track_id | artista Spotify | faixa Spotify | ano Spotify | lfm_record_key | artista LFM2b | faixa LFM2b | ano LFM | método | status | split |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5025 | 3YL3P9RhprjvHPxtTMxk67 | Black Pistol Fire | Stripes or Keys | 2012 | aa47153084073c9abbbcbbe5644f433637e2fe77e25ddfc45e385f386b3d414b | Black Pistol Fire | Stripes or Keys | 1 | raw_exact | accepted_high_confidence | holdout_test |
| 2 | 16437 | 6lNMCFyfxa8mcivkHSW8QC | Oliver | Dirty Talk - Black Van Remix | 2012 | 0a003038975051ef76941baae213e6c00e28af9fb98bc1365eb57ab3a68aba91 | Oliver | Dirty Talk (Original Mix) | 1773 | base_title_version_compatible | accepted_with_rules | holdout_test |
| 3 | 215227 | 4xIGOBPJVzK3suNYVesLoY | Prince Daddy & the Hyena | I Wish I Could Ctrl+alt+del My Life | 2016 | 5d52ee33150d3924101d3ef261ebe6e29c3cf97a9dda18bcf1520fbf7a7a4791 | Prince Daddy & The Hyena | I Wish I Could Ctrl+Alt+Del My Life | 216 | strict_normalized | accepted_high_confidence | development_train |
| 4 | 226345 | 5pLOxtMAxCpDIdZJ3ZWbEF | Attila | Obsession | 2016 | b0bf2e31adf62a61e7209679c344843e06f8f8de5c01fe084d385ad3ca88f221 | Attila | Obsession | 216 | raw_exact | accepted_high_confidence | development_train |
| 5 | 246701 | 1WpWRN46t4daKep5uUMX4W | Coil | Heaven's Blade | 2016 | 5418ec3d5897d84502e19519503fd56a03daa34e50975bc91ff921b8a590dae6 | Coil | Heaven's Blade | 215 | raw_exact | accepted_high_confidence | development_train |
| 6 | 262054 | 0sByROZZKxBqIawm3p86uy | ALEX | WITCHCRAFT | 2017 | 54aafec6df4ca3e3713fa2ead063740f9e26a6fc313b9b8104ca6a7d2574f533 | Alex | Witchcraft | 1833 | strict_normalized | accepted_high_confidence | holdout_test |
| 7 | 267310 | 1U3nHai9ueJCuEXbf8TvBA | Odd Mob | Lithium | 2017 | 05eb59d1f29476bae549afdd1aec5a3de4ff9760b8d5ff9013ee99c124cea4d0 | Odd Mob | Lithium | 1 | raw_exact | accepted_high_confidence | development_train |
| 8 | 269414 | 0Wcr4pWi1mndpFOiyjzOcC | Kanine | The Shadows | 2017 | d242da13f5ee527b1fdd74834c0147e209a03ec7e4cd6a571feb36259027ec54 | Kanine | The Shadows | 1 | raw_exact | accepted_high_confidence | development_train |
| 9 | 273772 | 6dRKRVyjzxa2efBCXZez6R | Shannon Lay | The Moons Detriment | 2017 | ed23acafd1614e98845a2fb31526d8c9e720e3a7c10b7617c8c914c92cd0241f | Shannon Lay | The Moons Detriment | 1 | raw_exact | accepted_high_confidence | development_train |
| 10 | 374989 | 5QqPMFlmxaTn4Xqmqizcrk | ALEX | AWAKENING | 2019 | 307fed9d147e73260e0f220c121981101b6220212013419f4c63ecb1baf161dd | Alex | awakening | 1816 | strict_normalized | accepted_high_confidence | holdout_test |
| 11 | 375015 | 4DNcvlNoCl4lVFFq8kT2N5 | ALEX | AFFLICTION | 2019 | 7cdb874d39caeed01af7e9ebd352dc90fe4fcf18eb987fde5606e0bf7ccd8ea7 | Alex | Affliction | 1780 | strict_normalized | accepted_high_confidence | holdout_test |
| 12 | 380971 | 45fTrhIQSf3zOAu7V2pj59 | Bou | Veteran | 2019 | dd168fa1369e384f07169d1a9829cda31d5e1a543847b235baed005971714ed8 | Bou | Veteran | 1 | raw_exact | accepted_high_confidence | holdout_test |
| 13 | 386292 | 75GzLKzGuCPSayNucAoSC6 | Adam Melchor | I Don't Wanna See You Cryin' Anymore | 2019 | 32dea5284472f1e5eaed51cf5ab7088754da0ad92bbab08d592a2d784e9e0299 | Adam Melchor | I Don't Wanna See You Cryin' Anymore | 1 | raw_exact | accepted_high_confidence | holdout_test |
| 14 | 389491 | 6oL0iIwhp5PpLU3zVSgpgP | The Red Pears | Dreams | 2019 | 2af345dc58e16bc824bbc1deda4cff7af64dad502aa23a97c73d3fdbb936df7f | The Red Pears | Dreams | 1 | raw_exact | accepted_high_confidence | holdout_test |
| 15 | 405017 | 3jFxcUhzAcjmIoSCFCjvwn | Laura Bretan | Dear Father | 2019 | 84d82a7034e02e20827106bd198e220082fd30cf7d0c09213d9ed33b8a7aa36f | Laura Bretan | Dear Father | 1 | raw_exact | accepted_high_confidence | development_train |
| 16 | 946826 | 0A4FpU40H9T3q6B7WpS3De | Edgar Allan Poe | The Raven | 2007 | 8bfaf55ddbe4fe85dd8be9f7b862bfc34caadcab2c9e306a0d9af0c19dc276c9 | Edgar Allan Poe | The Raven | 1845 | raw_exact | accepted_high_confidence | development_train |

## Interpretação

- Os valores implausíveis são problemas do campo temporal LFM2b, não evidência suficiente de match incorreto.
- `temporal_compatible` e os demais campos históricos foram preservados; a revisão introduz apenas a visão estatística válida.
- A planilha revisada contém estes 16 casos e os 22 casos sem `composition_key`, sem duplicação.
