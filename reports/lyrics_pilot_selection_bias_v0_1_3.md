# Viés de seleção da disponibilidade de letras — v0.1.3

## Objetivo

Esta análise foi executada somente depois de congelar os status de matching. `spotify_popularity` não participou da seleção de candidatos; é usada aqui apenas para descrever a população com letra aceita. Nenhum resultado deve ser interpretado causalmente.

## Popularidade Spotify por grupo

`{"accepted": {"maximum": 85.0, "mean": 25.611381, "median": 24.0, "minimum": 0.0, "n": 1441, "q1": 16.0, "q3": 33.0, "standardized_mean_difference_vs_cohort": -0.102419, "std": 13.282831}, "ambiguous": {"maximum": 78.0, "mean": 34.323661, "median": 35.0, "minimum": 0.0, "n": 448, "q1": 24.0, "q3": 45.0, "standardized_mean_difference_vs_cohort": 0.515042, "std": 14.1046}, "full_cohort": {"maximum": 85.0, "mean": 27.0565, "median": 26.0, "minimum": 0.0, "n": 2000, "q1": 17.0, "q3": 36.0, "standardized_mean_difference_vs_cohort": 0.0, "std": 14.109849}, "instrumental": {"maximum": 47.0, "mean": 29.368421, "median": 31.0, "minimum": 0.0, "n": 19, "q1": 23.0, "q3": 38.5, "standardized_mean_difference_vs_cohort": 0.163852, "std": 13.450364}, "not_found": {"maximum": 44.0, "mean": 13.901099, "median": 11.0, "minimum": 0.0, "n": 91, "q1": 6.5, "q3": 18.5, "standardized_mean_difference_vs_cohort": -0.932356, "std": 9.89282}, "request_error": {"maximum": 7.0, "mean": 7.0, "median": 7.0, "minimum": 7.0, "n": 1, "q1": 7.0, "q3": 7.0, "standardized_mean_difference_vs_cohort": -1.421454, "std": 0.0}}`

O SMD da média das aceitas contra a coorte completa foi -0.102419; magnitude classificada como `small_or_negligible`.

## Período

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| 2000-2005 | 321 | 0.1605 | 227 | 0.707165 | 0.655167 | 0.754263 |
| 2006-2011 | 409 | 0.2045 | 302 | 0.738386 | 0.693713 | 0.778623 |
| 2012-2017 | 811 | 0.4055 | 581 | 0.7164 | 0.684413 | 0.746345 |
| 2018-2023 | 459 | 0.2295 | 331 | 0.721133 | 0.678401 | 0.760194 |

## Método de matching

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| base_title_version_compatible | 12 | 0.006 | 8 | 0.666667 | 0.390618 | 0.861882 |
| conservative_normalized | 118 | 0.059 | 68 | 0.576271 | 0.48609 | 0.661643 |
| raw_exact | 1489 | 0.7445 | 1088 | 0.730692 | 0.707587 | 0.752609 |
| strict_normalized | 381 | 0.1905 | 277 | 0.727034 | 0.680201 | 0.769334 |

## Quintil de popularidade

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | 403 | 0.2015 | 297 | 0.736973 | 0.691894 | 0.777576 |
| Q2 | 419 | 0.2095 | 349 | 0.832936 | 0.794226 | 0.865595 |
| Q3 | 415 | 0.2075 | 328 | 0.790361 | 0.748624 | 0.826773 |
| Q4 | 377 | 0.1885 | 254 | 0.67374 | 0.624867 | 0.719108 |
| Q5 | 386 | 0.193 | 213 | 0.551813 | 0.501933 | 0.600673 |

## Presença de versão especial

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| False | 1988 | 0.994 | 1431 | 0.719819 | 0.699668 | 0.739122 |
| True | 12 | 0.006 | 10 | 0.833333 | 0.551964 | 0.953036 |

## Gênero

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| acoustic | 52 | 0.026 | 39 | 0.75 | 0.617933 | 0.84767 |
| alt-rock | 122 | 0.061 | 73 | 0.598361 | 0.509652 | 0.681064 |
| ambient | 18 | 0.009 | 14 | 0.777778 | 0.54785 | 0.909992 |
| black-metal | 59 | 0.0295 | 50 | 0.847458 | 0.734818 | 0.917616 |
| blues | 48 | 0.024 | 40 | 0.833333 | 0.704219 | 0.913046 |
| chill | 46 | 0.023 | 35 | 0.76087 | 0.620646 | 0.86088 |
| classical | 5 | 0.0025 | 3 | 0.6 | 0.23072 | 0.882382 |
| club | 9 | 0.0045 | 6 | 0.666667 | 0.354197 | 0.879418 |
| comedy | 6 | 0.003 | 5 | 0.833333 | 0.436491 | 0.969947 |
| country | 101 | 0.0505 | 67 | 0.663366 | 0.566725 | 0.748036 |
| dance | 77 | 0.0385 | 43 | 0.558442 | 0.44738 | 0.663948 |
| dancehall | 19 | 0.0095 | 14 | 0.736842 | 0.51208 | 0.881938 |
| death-metal | 94 | 0.047 | 74 | 0.787234 | 0.69408 | 0.857832 |
| deep-house | 10 | 0.005 | 8 | 0.8 | 0.490157 | 0.943319 |
| disco | 26 | 0.013 | 19 | 0.730769 | 0.539166 | 0.862957 |
| drum-and-bass | 6 | 0.003 | 2 | 0.333333 | 0.096769 | 0.700012 |
| dub | 15 | 0.0075 | 7 | 0.466667 | 0.248092 | 0.698834 |
| dubstep | 2 | 0.001 | 0 | 0.0 | 0.0 | 0.657628 |
| edm | 18 | 0.009 | 12 | 0.666667 | 0.437491 | 0.837214 |
| electro | 30 | 0.015 | 15 | 0.5 | 0.331539 | 0.668461 |
| electronic | 15 | 0.0075 | 13 | 0.866667 | 0.621175 | 0.96264 |
| emo | 125 | 0.0625 | 92 | 0.736 | 0.652524 | 0.805403 |
| folk | 72 | 0.036 | 56 | 0.777778 | 0.669088 | 0.858327 |
| french | 12 | 0.006 | 8 | 0.666667 | 0.390618 | 0.861882 |
| funk | 44 | 0.022 | 31 | 0.704545 | 0.557795 | 0.818446 |
| garage | 65 | 0.0325 | 56 | 0.861538 | 0.757317 | 0.92541 |
| german | 13 | 0.0065 | 11 | 0.846154 | 0.577648 | 0.956743 |
| gospel | 10 | 0.005 | 8 | 0.8 | 0.490157 | 0.943319 |
| goth | 42 | 0.021 | 33 | 0.785714 | 0.640599 | 0.882943 |
| grindcore | 16 | 0.008 | 14 | 0.875 | 0.639767 | 0.965023 |
| groove | 18 | 0.009 | 16 | 0.888889 | 0.671998 | 0.968981 |
| hard-rock | 60 | 0.03 | 47 | 0.783333 | 0.663797 | 0.868771 |
| hardcore | 91 | 0.0455 | 64 | 0.703297 | 0.602758 | 0.787366 |
| hardstyle | 4 | 0.002 | 4 | 1.0 | 0.5101 | 1.0 |
| heavy-metal | 11 | 0.0055 | 7 | 0.636364 | 0.353797 | 0.848338 |
| hip-hop | 68 | 0.034 | 40 | 0.588235 | 0.469613 | 0.697422 |
| house | 3 | 0.0015 | 2 | 0.666667 | 0.207655 | 0.93851 |
| indian | 5 | 0.0025 | 4 | 0.8 | 0.375528 | 0.963777 |
| indie-pop | 57 | 0.0285 | 42 | 0.736842 | 0.610232 | 0.833544 |
| industrial | 40 | 0.02 | 29 | 0.725 | 0.571647 | 0.838921 |
| jazz | 18 | 0.009 | 12 | 0.666667 | 0.437491 | 0.837214 |
| k-pop | 16 | 0.008 | 11 | 0.6875 | 0.444039 | 0.858356 |
| metal | 44 | 0.022 | 28 | 0.636364 | 0.488661 | 0.762167 |
| metalcore | 31 | 0.0155 | 27 | 0.870968 | 0.711472 | 0.948658 |
| new-age | 1 | 0.0005 | 1 | 1.0 | 0.206543 | 1.0 |
| opera | 3 | 0.0015 | 3 | 1.0 | 0.438494 | 1.0 |
| piano | 16 | 0.008 | 14 | 0.875 | 0.639767 | 0.965023 |
| pop | 19 | 0.0095 | 12 | 0.631579 | 0.410392 | 0.808507 |
| power-pop | 41 | 0.0205 | 30 | 0.731707 | 0.580662 | 0.843052 |
| progressive-house | 7 | 0.0035 | 7 | 1.0 | 0.645661 | 1.0 |
| psych-rock | 34 | 0.017 | 21 | 0.617647 | 0.450407 | 0.761 |
| punk | 36 | 0.018 | 27 | 0.75 | 0.589292 | 0.862497 |
| punk-rock | 19 | 0.0095 | 14 | 0.736842 | 0.51208 | 0.881938 |
| rock | 15 | 0.0075 | 6 | 0.4 | 0.198242 | 0.642536 |
| rock-n-roll | 6 | 0.003 | 4 | 0.666667 | 0.299988 | 0.903231 |
| sad | 1 | 0.0005 | 1 | 1.0 | 0.206543 | 1.0 |
| show-tunes | 9 | 0.0045 | 7 | 0.777778 | 0.452583 | 0.936776 |
| singer-songwriter | 38 | 0.019 | 33 | 0.868421 | 0.726728 | 0.942462 |
| ska | 30 | 0.015 | 18 | 0.6 | 0.423201 | 0.754096 |
| songwriter | 1 | 0.0005 | 1 | 1.0 | 0.206543 | 1.0 |
| soul | 46 | 0.023 | 35 | 0.76087 | 0.620646 | 0.86088 |
| swedish | 24 | 0.012 | 20 | 0.833333 | 0.641465 | 0.933214 |
| techno | 2 | 0.001 | 1 | 0.5 | 0.094529 | 0.905471 |
| trance | 4 | 0.002 | 1 | 0.25 | 0.045586 | 0.699364 |
| trip-hop | 5 | 0.0025 | 4 | 0.8 | 0.375528 | 0.963777 |

## Ano

| category | n | proportion | accepted_n | acceptance_rate | wilson_95_low | wilson_95_high |
| --- | --- | --- | --- | --- | --- | --- |
| 2000 | 46 | 0.023 | 34 | 0.73913 | 0.597406 | 0.843993 |
| 2001 | 59 | 0.0295 | 36 | 0.610169 | 0.482661 | 0.724208 |
| 2002 | 58 | 0.029 | 41 | 0.706897 | 0.579869 | 0.80822 |
| 2003 | 54 | 0.027 | 39 | 0.722222 | 0.591093 | 0.823833 |
| 2004 | 50 | 0.025 | 41 | 0.82 | 0.692037 | 0.902299 |
| 2005 | 54 | 0.027 | 36 | 0.666667 | 0.533607 | 0.777588 |
| 2006 | 65 | 0.0325 | 37 | 0.569231 | 0.448328 | 0.682407 |
| 2007 | 63 | 0.0315 | 51 | 0.809524 | 0.69593 | 0.887539 |
| 2008 | 56 | 0.028 | 44 | 0.785714 | 0.661803 | 0.872942 |
| 2009 | 77 | 0.0385 | 63 | 0.818182 | 0.717635 | 0.888488 |
| 2010 | 82 | 0.041 | 60 | 0.731707 | 0.627036 | 0.81564 |
| 2011 | 66 | 0.033 | 47 | 0.712121 | 0.593625 | 0.807282 |
| 2012 | 93 | 0.0465 | 62 | 0.666667 | 0.565933 | 0.754178 |
| 2013 | 112 | 0.056 | 85 | 0.758929 | 0.671977 | 0.828706 |
| 2014 | 125 | 0.0625 | 88 | 0.704 | 0.618859 | 0.776976 |
| 2015 | 156 | 0.078 | 113 | 0.724359 | 0.649485 | 0.788449 |
| 2016 | 146 | 0.073 | 103 | 0.705479 | 0.627036 | 0.773387 |
| 2017 | 179 | 0.0895 | 130 | 0.726257 | 0.656698 | 0.786308 |
| 2018 | 203 | 0.1015 | 159 | 0.783251 | 0.721593 | 0.834388 |
| 2019 | 193 | 0.0965 | 134 | 0.694301 | 0.626036 | 0.754981 |
| 2020 | 51 | 0.0255 | 33 | 0.647059 | 0.509858 | 0.763657 |
| 2021 | 7 | 0.0035 | 2 | 0.285714 | 0.082217 | 0.641071 |
| 2022 | 4 | 0.002 | 2 | 0.5 | 0.150036 | 0.849964 |
| 2023 | 1 | 0.0005 | 1 | 1.0 | 0.206543 | 1.0 |

## Disponibilidade técnica

- Plain: `[{"acceptance_rate": 0.0, "accepted_n": 0, "category": "False", "n": 109, "proportion": 0.0545, "wilson_95_high": 0.034044, "wilson_95_low": 0.0}, {"acceptance_rate": 0.762031, "accepted_n": 1441, "category": "True", "n": 1891, "proportion": 0.9455, "wilson_95_high": 0.780681, "wilson_95_low": 0.742318}]`
- Synced: `[{"acceptance_rate": 0.707265, "accepted_n": 331, "category": "False", "n": 468, "proportion": 0.234, "wilson_95_high": 0.746669, "wilson_95_low": 0.664486}, {"acceptance_rate": 0.724543, "accepted_n": 1110, "category": "True", "n": 1532, "proportion": 0.766, "wilson_95_high": 0.746332, "wilson_95_low": 0.701631}]`
- Duração: `{"accepted": {"maximum": 999.976, "mean": 229.644722, "median": 218.884, "minimum": 9.707, "n": 1441, "q1": 185.61, "q3": 260.827, "std": 86.685385}, "ambiguous": {"maximum": 688.0, "mean": 232.405993, "median": 220.589, "minimum": 42.387, "n": 448, "q1": 191.5735, "q3": 260.75925, "std": 77.206019}, "full_cohort": {"maximum": 999.976, "mean": 229.374436, "median": 218.4115, "minimum": 9.707, "n": 2000, "q1": 185.176, "q3": 260.30675, "std": 87.521406}, "instrumental": {"maximum": 479.087, "mean": 234.475895, "median": 225.75, "minimum": 80.284, "n": 19, "q1": 198.724, "q3": 265.314, "std": 86.703438}, "not_found": {"maximum": 983.173, "mean": 208.511286, "median": 187.0, "minimum": 67.473, "n": 91, "q1": 138.0895, "q3": 243.576, "std": 135.180504}, "request_error": {"maximum": 283.373, "mean": 283.373, "median": 283.373, "minimum": 283.373, "n": 1, "q1": 283.373, "q3": 283.373, "std": 0.0}}`

## Diagnóstico

- Faixa de aceitação por período: [0.707165, 0.738386].
- Faixa por gênero com n ≥ 20: [0.5, 0.870968].
- Faixa por método: [0.576271, 0.730692].
- Faixa com/sem versão: [0.719819, 0.833333].

Avaliação descritiva:

- O grupo aceito não favorece músicas mais populares: sua média é ligeiramente inferior à da coorte, com deslocamento padronizado pequeno.
- A aceitação cai no quinto quintil, acompanhado por mais casos ambíguos; isso indica associação entre popularidade e o tipo de desfecho, sem interpretação causal.
- As taxas por período são próximas, sem evidência descritiva de forte concentração temporal da disponibilidade aceita.
- Há heterogeneidade por gênero e método de matching; o método conservador apresenta aceitação menor que raw_exact e strict_normalized.
- O estrato com flag de versão tem somente 12 composições e intervalo amplo; não há base para uma conclusão forte sobre versões especiais.

Associações descritivas de disponibilidade; não sustentam inferência causal. Modelos futuros com letras generalizam primariamente para composições com status aceito.

## Validação final

| command | exit_code | result |
| --- | --- | --- |
| python -c <permissão tmp Windows>; pytest.main([-q, -p no:cacheprovider, --basetemp isolado]) | 0 | 58 passed |
| pytest tests/test_lyrics_pilot_v013.py -q (tmp isolado) | 0 | 8 passed |
| python -m ruff check src tests | 0 | All checks passed |
| python -m ruff format --check . | 0 | 56 files already formatted |
| git diff --check | 0 | sem erros; somente avisos LF/CRLF |
| auditoria de hashes, split, privacidade e cardinalidade | 0 | base/split preservados; 2.000 resultados/caches; 1.441 aceitas; holdout 0; privado tracked/staged 0 |
| python -m ruff check . | 1 | único B018 preexistente em exp_base.py:8; excluído do checkpoint |

Nenhum commit ou push foi realizado depois da coleta.
