# Diagnóstico da amostra e dos modelos — V0.7

## Escopo e conclusão

Diagnóstico exploratório, posterior à abertura da V0.6. A primeira avaliação permanece encerrada e inalterada. Não houve ajuste, seleção de modelos, calibração, nova coleta, alteração de split nem mudança da interface. Tradicional continua sendo o candidato predefinido. O objetivo é estimar a popularidade observada no snapshot da fonte para a faixa representante de uma composição operacional; não popularidade universal da composição, causalidade ou sucesso comercial futuro.

A conferência dos três casos não encontrou defeito de interface nem troca de linhas/chaves/alvos. Encontrou erro preditivo real em um caso e limitações documentais de versão/ano nos outros. A correspondência entre gravações e entre textos líricos de fontes diferentes não está certificada. Detalhes individuais, IDs, previsões completas, alternativas e contribuições estão exclusivamente no artefato privado `data/derived/private_diagnostics_v0_7/casos_relatados.md` e nos JSONs associados.

## Preservação e acesso ao alvo

Git: branch `master`, HEAD `a37946ae2ddb211abe85d67a9b69fc7e88a71b86`. Estado inicial, stage e hashes dos arquivos pessoais estão em `data/derived/private_diagnostics_v0_7/preservation_before.json`. Foram conferidos 52 artefatos científicos selados e 188 arquivos preexistentes rastreados/não ignorados; hashes preservados. Nenhum commit, push, reset ou staging.

Somente os alvos das 7.648 composições de desenvolvimento já autorizadas e das 2.592 do holdout aberto foram desserializados. Cobertura, reserva, catálogo original e candidatos futuros usam projeções explícitas sem popularidade, contagens de sucesso ou quintis. Ler bytes para SHA-256 não desserializa os alvos. A lista de projeções e hashes está no run summary. Não foram lidos caches nem textos de letras. Vetores congelados foram usados apenas internamente na inferência; não exportados.

## 1. Cobertura: denominadores e perdas

Fonte Spotify: 1,159,764 linhas e track_ids únicos; 1,075,469 chaves operacionais não nulas; 63,988 nomes normalizados. Matching aceito: 111.758 / 1.159.764 = 9.6363%. As contagens abaixo de artistas são grupos operacionais, não identidades universais.

| Status Spotify após matching | Faixas |
|---|---|
| accepted_high_confidence | 99418 |
| accepted_with_rules | 12340 |
| ambiguous | 8178 |
| candidate_for_review | 3024 |
| unmatched | 1036804 |

| Etapa | Faixas/linhas | Composições | Artistas | ≥1 flag de versão |
|---|---|---|---|---|
| integrated | 111758 | 111422 | 13901 | 6120 |
| eligible_representatives | 111422 | 111422 | 13899 | 5809 |
| main_selected | 14000 | 14000 | 6017 | 728 |
| reserve_available | 2000 | 2000 | 1646 | 106 |
| queried_main_and_reserve | 15000 | 15000 | 6248 | 783 |
| lyrics_accepted | 10240 | 10240 | 5057 | 482 |
| final_matrix | 10240 | 10240 | 5057 | 482 |
| demo_catalog | 2592 | 2592 | 1308 | 98 |

| Etapa | Development | Holdout |
|---|---|---|
| integrated | 83817 | 27941 |
| eligible_representatives | 83559 | 27863 |
| main_selected | 10500 | 3500 |
| reserve_available | 1500 | 500 |
| queried_main_and_reserve | 11250 | 3750 |
| lyrics_accepted | 7648 | 2592 |
| final_matrix | 7648 | 2592 |
| demo_catalog | 0 | 2592 |

A passagem de 111.758 pares para 111.422 representantes deixa 22 registros sem chave e colapsa 314 linhas adicionais de chaves repetidas; não elimina 336 composições válidas. O total de chaves não nulas já era 111.422. A reserva de 2.000 não é uma etapa aditiva posterior aos 15.000: só os dois primeiros lotes, 1.000 registros, foram ativados; 1.000 permaneceram inativos.

Maior redução desde a base integrada: a amostragem por hash, de 111.422 elegíveis para 15.000 efetivamente consultados (13,4623%; 96.422 não consultados). Desses 15.000, 10.240 foram aceitos (68,2667%) e 4.760 não foram. Da fonte original, a maior perda antecede isso: 1.048.006 faixas não têm matching aceito. São razões diferentes: cobertura/matching, orçamento amostral e aceite da letra. Não há perda adicional entre letra aceita e matriz final, nem entre as 2.592 linhas do holdout e catálogo da aplicação.

| Status de coleta | Development | Holdout | Total |
|---|---|---|---|
| accepted_exact_equivalent | 5305 | 1821 | 7126 |
| accepted_exact_unique | 2343 | 771 | 3114 |
| ambiguous_distinct_lyrics | 2451 | 792 | 3243 |
| ambiguous_metadata_conflict | 71 | 35 | 106 |
| ambiguous_search_truncated | 0 | 1 | 1 |
| instrumental | 83 | 26 | 109 |
| not_found | 492 | 152 | 644 |
| request_error | 505 | 152 | 657 |

`request_error` soma 657 casos (4,38% das 15.000 consultas), diferente de `not_found` (644), instrumental (109) ou ambiguidades (3.350). Não interpretar erro HTTP como ausência de letra. A reconciliação V0.4 já distinguia 0 exceções de transporte de 657 resultados HTTP/consulta sem êxito.

### Perdas estratificadas

Taxa de aceite = final / efetivamente consultado no estrato. Não é efeito causal do gênero, método ou flag. Todas as contagens, incluindo split e as oito flags separadas, estão em `coverage.strata` no run summary.

| Dimensão | Grupo | Elegíveis | Consultados | Finais | Aceite (0–1) |
|---|---|---|---|---|---|
| any_version | False | 105613 | 14217 | 9758 | 0.6864 |
| any_version | True | 5809 | 783 | 482 | 0.6156 |
| artist_size_bin | 1 | 4489 | 617 | 410 | 0.6645 |
| artist_size_bin | 2-5 | 13365 | 1756 | 1212 | 0.6902 |
| artist_size_bin | 21+ | 55098 | 7355 | 4989 | 0.6783 |
| artist_size_bin | 6-20 | 38470 | 5272 | 3629 | 0.6884 |
| match_method | base_title_version_compatible | 3242 | 454 | 272 | 0.5991 |
| match_method | conservative_normalized | 8972 | 1190 | 731 | 0.6143 |
| match_method | raw_exact | 79559 | 10703 | 7399 | 0.6913 |
| match_method | strict_normalized | 19649 | 2653 | 1838 | 0.6928 |
| period_diag | 2000-2009 | 31869 | 4263 | 2800 | 0.6568 |
| period_diag | 2010-2019 | 75784 | 10206 | 7114 | 0.6970 |
| period_diag | 2020-2023 | 3769 | 531 | 326 | 0.6139 |

`artist_size_bin` conta composições elegíveis por artista (não quantidade de faixas nem popularidade). As composições são as unidades amostradas; artistas de catálogo maior podem aparecer com mais composições.

| Gênero | Elegíveis | Consultados | Finais | Aceite (0–1) |
|---|---|---|---|---|
| acoustic | 2930 | 392 | 313 | 0.7985 |
| afrobeat | 65 | 8 | 2 | 0.2500 |
| alt-rock | 6637 | 887 | 527 | 0.5941 |
| ambient | 821 | 107 | 76 | 0.7103 |
| black-metal | 3407 | 453 | 319 | 0.7042 |
| blues | 2590 | 360 | 265 | 0.7361 |
| breakbeat | 103 | 12 | 7 | 0.5833 |
| cantopop | 15 | 2 | 1 | 0.5000 |
| chicago-house | 12 | 0 | 0 | — |
| chill | 2553 | 341 | 239 | 0.7009 |
| classical | 450 | 58 | 30 | 0.5172 |
| club | 710 | 90 | 52 | 0.5778 |
| comedy | 369 | 56 | 37 | 0.6607 |
| country | 5488 | 739 | 501 | 0.6779 |
| dance | 4201 | 555 | 294 | 0.5297 |
| dancehall | 1030 | 140 | 100 | 0.7143 |
| death-metal | 5045 | 665 | 481 | 0.7233 |
| deep-house | 652 | 102 | 78 | 0.7647 |
| detroit-techno | 5 | 0 | 0 | — |
| disco | 1182 | 151 | 98 | 0.6490 |
| drum-and-bass | 484 | 61 | 28 | 0.4590 |
| dub | 984 | 113 | 76 | 0.6726 |
| dubstep | 84 | 10 | 3 | 0.3000 |
| edm | 1221 | 183 | 117 | 0.6393 |
| electro | 1921 | 241 | 148 | 0.6141 |
| electronic | 899 | 129 | 98 | 0.7597 |
| emo | 6511 | 893 | 663 | 0.7424 |
| folk | 3996 | 541 | 387 | 0.7153 |
| french | 751 | 85 | 53 | 0.6235 |
| funk | 2204 | 289 | 188 | 0.6505 |
| garage | 3400 | 465 | 358 | 0.7699 |
| german | 857 | 129 | 86 | 0.6667 |
| gospel | 585 | 81 | 64 | 0.7901 |
| goth | 2322 | 356 | 254 | 0.7135 |
| grindcore | 892 | 156 | 82 | 0.5256 |
| groove | 1089 | 153 | 113 | 0.7386 |
| guitar | 47 | 5 | 1 | 0.2000 |
| hard-rock | 3210 | 428 | 290 | 0.6776 |
| hardcore | 4703 | 623 | 446 | 0.7159 |
| hardstyle | 221 | 24 | 16 | 0.6667 |
| heavy-metal | 492 | 63 | 34 | 0.5397 |
| hip-hop | 3767 | 487 | 285 | 0.5852 |
| house | 410 | 53 | 35 | 0.6604 |
| indian | 222 | 28 | 21 | 0.7500 |
| indie-pop | 3235 | 458 | 300 | 0.6550 |
| industrial | 2026 | 262 | 194 | 0.7405 |
| jazz | 880 | 126 | 95 | 0.7540 |
| k-pop | 870 | 132 | 88 | 0.6667 |
| metal | 2308 | 310 | 150 | 0.4839 |
| metalcore | 1620 | 207 | 169 | 0.8164 |
| minimal-techno | 84 | 15 | 6 | 0.4000 |
| new-age | 104 | 16 | 9 | 0.5625 |
| opera | 245 | 35 | 26 | 0.7429 |
| party | 15 | 0 | 0 | — |
| piano | 955 | 119 | 89 | 0.7479 |
| pop | 1189 | 171 | 92 | 0.5380 |
| pop-film | 11 | 0 | 0 | — |
| power-pop | 2429 | 305 | 212 | 0.6951 |
| progressive-house | 497 | 66 | 48 | 0.7273 |
| psych-rock | 1673 | 220 | 167 | 0.7591 |
| punk | 1944 | 252 | 163 | 0.6468 |
| punk-rock | 1204 | 160 | 127 | 0.7937 |
| rock | 782 | 96 | 52 | 0.5417 |
| rock-n-roll | 327 | 44 | 27 | 0.6136 |
| sad | 159 | 26 | 21 | 0.8077 |
| salsa | 4 | 2 | 1 | 0.5000 |
| samba | 25 | 4 | 4 | 1.0000 |
| sertanejo | 4 | 0 | 0 | — |
| show-tunes | 655 | 77 | 51 | 0.6623 |
| singer-songwriter | 2276 | 291 | 225 | 0.7732 |
| ska | 1620 | 216 | 171 | 0.7917 |
| sleep | 1 | 0 | 0 | — |
| songwriter | 49 | 7 | 7 | 1.0000 |
| soul | 2599 | 374 | 266 | 0.7112 |
| spanish | 125 | 17 | 7 | 0.4118 |
| swedish | 1235 | 178 | 144 | 0.8090 |
| techno | 117 | 21 | 12 | 0.5714 |
| trance | 301 | 37 | 26 | 0.7027 |
| trip-hop | 317 | 42 | 25 | 0.5952 |

### Múltiplas versões e matching 1:1

As contagens seguintes são faixas Spotify, agrupadas pelo número de registros que compartilham a chave operacional na fonte. Chaves normalizadas não garantem mesma obra/gravação. A regra 1:1 penaliza ambiguidades: candidatos determinísticos são contados antes de aceitar o par; não se escolhe arbitrariamente uma versão entre muitos candidatos. Matching temporal não é requisito de aceitação. Fuzzy é somente revisão, limitado no código, não evidência de ausência em toda a fonte LFM2b.

| Versões/chave na fonte | Faixas | Aceitas | Taxa | Ambíguas | Taxa ambígua |
|---|---|---|---|---|---|
| 1 | 1019090 | 103996 | 0.1020 | 422 | 0.0004 |
| 2-5 | 126302 | 7674 | 0.0608 | 5236 | 0.0415 |
| 6+ | 14372 | 88 | 0.0061 | 2520 | 0.1753 |

A queda da taxa de aceite com multiplicidade é associação observada, não estimativa causal. Representantes são escolhidos somente entre matches aceitos: preferência por ausência de live/remix/acoustic/karaoke; depois status, método, score, completude, menor spotify_row_id e track_id. Uma gravação de estúdio disponível no Spotify, mas sem match aceito, não concorre nessa escolha.

## 2. Artistas, versões, anos e flags

| Artista | Etapa | Faixas | Composições | Grupos artista |
|---|---|---|---|---|
| adele | source | 51 | 47 | 1 |
| adele | integrated | 13 | 13 | 1 |
| adele | eligible_representatives | 13 | 13 | 1 |
| adele | main_selected | 3 | 3 | 1 |
| adele | reserve_available | 0 | 0 | 0 |
| adele | queried_main_and_reserve | 3 | 3 | 1 |
| adele | lyrics_accepted | 1 | 1 | 1 |
| adele | final_matrix | 1 | 1 | 1 |
| adele | demo_catalog | 1 | 1 | 1 |
| alice in chains | source | 78 | 66 | 1 |
| alice in chains | integrated | 37 | 35 | 1 |
| alice in chains | eligible_representatives | 35 | 35 | 1 |
| alice in chains | main_selected | 5 | 5 | 1 |
| alice in chains | reserve_available | 0 | 0 | 0 |
| alice in chains | queried_main_and_reserve | 5 | 5 | 1 |
| alice in chains | lyrics_accepted | 3 | 3 | 1 |
| alice in chains | final_matrix | 3 | 3 | 1 |
| alice in chains | demo_catalog | 3 | 3 | 1 |
| guns n roses | source | 103 | 72 | 1 |
| guns n roses | integrated | 12 | 12 | 1 |
| guns n roses | eligible_representatives | 12 | 12 | 1 |
| guns n roses | main_selected | 1 | 1 | 1 |
| guns n roses | reserve_available | 0 | 0 | 0 |
| guns n roses | queried_main_and_reserve | 1 | 1 | 1 |
| guns n roses | lyrics_accepted | 1 | 1 | 1 |
| guns n roses | final_matrix | 1 | 1 | 1 |
| guns n roses | demo_catalog | 1 | 1 | 1 |

Foram rastreadas todas as 232 faixas locais desses três artistas: 103 + 51 + 78. A lista privada `artist_track_trace.json` contém cada título e a primeira etapa responsável pela exclusão, preservando também flags e indicadores de presença. `matching_candidates_artists.json`, `matched_artists_audio_lfm.json`, `artist_composition_version_groups.json` e `artists_lrclib_metadata.json` detalham candidatos, chaves, alternativas e coleta. Não houve seleção por acerto/erro nem inferência de quais músicas deveriam ser os maiores sucessos.

| Nome observado Spotify | Grupos artista | Splits | Split |
|---|---|---|---|
| Guns N' Roses | 1 | 1 | holdout_test |
| Alice In Chains | 1 | 1 | holdout_test |
| Adele | 1 | 1 | holdout_test |

As variações de caixa/pontuação observadas (inclusive Alice In Chains versus Alice in Chains nas fontes e apóstrofo em Guns N’ Roses) convergem na normalização conservadora. Não apareceu fragmentação desses três nomes entre os grupos aceitos. Globalmente, cruzamentos de artist_group_id, composition_key e split_group_id entre splits: zero. Isso não certifica aliases desconhecidos; não existe catálogo externo de identidades para resolver todo pseudônimo/colaboração.

O CSV Spotify original e o normalizado têm a mesma contagem. O ano bruto está entre 2000 e 2023; 0 linhas fora do intervalo. O código apenas rotula coortes temporais, não remove aqui faixas fora do intervalo. Assim, a ausência de gravações antigas pode estar no recorte da fonte, não em uma exclusão adicional comprovada da pipeline. Relançamentos/versões podem trazer datas posteriores, mas `year` não tem semântica documentada suficiente para afirmar se é lançamento original, álbum ou versão. Um ano no título é evidência textual, não confirmação documental da primeira gravação. `genre` é o rótulo da fonte, cujo método de curadoria não está documentado.

### Auditoria das flags

| Etapa | Sinal textual | n | Sinal presente | Sinal sem flag | Flag sem contexto específico |
|---|---|---|---|---|---|
| source | live_context | 1159764 | 32864 | 0 | 3187 |
| source | remaster_context | 1159764 | 15278 | 0 | 0 |
| source | remix_context | 1159764 | 37672 | 0 | 32843 |
| integrated | live_context | 111758 | 2257 | 0 | 367 |
| integrated | remaster_context | 111758 | 571 | 0 | 0 |
| integrated | remix_context | 111758 | 1341 | 0 | 502 |
| eligible_representatives | live_context | 111422 | 2176 | 0 | 359 |
| eligible_representatives | remaster_context | 111422 | 566 | 0 | 0 |
| eligible_representatives | remix_context | 111422 | 1216 | 0 | 465 |
| queried_main_and_reserve | live_context | 15000 | 304 | 0 | 54 |
| queried_main_and_reserve | remaster_context | 15000 | 78 | 0 | 0 |
| queried_main_and_reserve | remix_context | 15000 | 162 | 0 | 67 |
| final_matrix | live_context | 10240 | 214 | 0 | 39 |
| final_matrix | remaster_context | 10240 | 52 | 0 | 0 |
| final_matrix | remix_context | 10240 | 92 | 0 | 25 |
| demo_catalog | live_context | 2592 | 44 | 0 | 9 |
| demo_catalog | remaster_context | 2592 | 9 | 0 | 0 |
| demo_catalog | remix_context | 2592 | 20 | 0 | 4 |

`live_context` procura live at/in/from/on, (live) ou sufixo - live; remaster e remix usam palavras explícitas. Ausência de divergência nessa checagem lexical não valida semanticamente as flags: o código original usa `\blive\b` em qualquer parte do título e `mix` pode acionar remix. Título com a palavra inglesa live não demonstra apresentação ao vivo. Contagens de 'flag sem contexto' são candidatos a revisão, não erros adjudicados.

Detector adicional independente: 1246 títulos da fonte contêm unplugged/recorded at/concert/session sem nenhuma das oito flags; 78 entraram na base integrada e 4 na matriz final. São indícios para auditoria privada, não correções automáticas. A taxa real de falsos positivos/negativos não pode ser estimada sem revisão humana cega ou metadados de gravação confiáveis.

## 3. Conferência técnica do demonstrador

Os três registros foram localizados nos arquivos, não por IDs presumidos. Foram executadas as 12 inferências (3 × 4 pipelines) com colunas na ordem e tipos do manifesto. As 219 entradas Baseline/LFM dos casos coincidem com a base congelada nas mesmas chaves. Comparação com previsões V0.6: diferença absoluta máxima 3.5527136788005009e-15, dentro de atol=1e-8 e rtol=1e-10. Popularidade ausente dos inputs. Observado associado por track_id + spotify_row_id; erro absoluto calculado antes do arredondamento de exibição. Trocar seleção limpa previsão e observado; estimar não revela o observado. Catálogo completo do app = holdout, sem perdas extras.

Categorias desconhecidas, imputações e valores fora do mínimo/máximo univariado do treino: nenhum encontrado nos três casos (incluindo as dimensões de embeddings, sem exportar vetores). Isso não comprova suporte multivariado ou similaridade semântica. Os coeficientes foram decompostos após transformações congeladas; intercepto + soma das contribuições reproduz cada previsão. São descrições do modelo em sua codificação, dependentes de escala, one-hot e PCA; não efeitos causais ou importância universal. A decomposição completa está privada.

## 4. Erros: OOF e teste separados

OOF: cinco folds salvos; chaves e alvos reconciliados com a matriz de desenvolvimento. Não foram usadas previsões ajustadas no próprio treino para esses diagnósticos. Resíduo = observado − previsto. Quantis: interpolação linear NumPy; desvio padrão populacional (ddof=0); previsões sem clipping. Grupos com n<30 têm n publicado e métricas apenas no arquivo privado `all_group_metrics.json`; faixas vazias são mantidas. Não são intervalos individuais nem porcentagens de acerto.

### Desenvolvimento OOF — n=7.648

| Modelo | MAE | RMSE | R² | Resíduo médio |
|---|---|---|---|---|
| Baseline | 7.0940 | 9.2138 | 0.5298 | -0.0081 |
| Tradicional | 7.0612 | 9.1883 | 0.5324 | -0.0202 |
| Profundo | 7.1625 | 9.2801 | 0.5230 | -0.0152 |
| Combinado | 7.1631 | 9.2955 | 0.5214 | -0.0258 |
| Dummy | 10.7222 | 13.4364 | -0.0000 | 0.0000 |

| Modelo | Mediana |erro| | P75 | P90 | P95 | ≤5 (%) | ≤10 (%) | ≤20 (%) | >20 n | >20 (%) |
|---|---|---|---|---|---|---|---|---|---|
| Baseline | 5.8596 | 9.8216 | 14.3249 | 18.1946 | 43.6192 | 76.0068 | 96.2866 | 284 | 3.7134 |
| Tradicional | 5.7894 | 9.7553 | 14.4007 | 18.2594 | 44.2992 | 76.3337 | 96.4043 | 275 | 3.5957 |
| Profundo | 5.8830 | 10.0101 | 14.3652 | 18.4157 | 43.0962 | 74.9477 | 96.3389 | 280 | 3.6611 |
| Combinado | 5.8159 | 9.9683 | 14.5594 | 18.2470 | 43.8154 | 75.1831 | 96.2343 | 288 | 3.7657 |
| Dummy | 9.0059 | 15.0268 | 21.9600 | 25.0387 | 27.9942 | 54.4195 | 87.3562 | 967 | 12.6438 |

| Distribuição | Média | DP | Mín | P5 | P25 | P50 | P75 | P95 | Máx |
|---|---|---|---|---|---|---|---|---|---|
| Observado | 25.9920 | 13.4362 | 0.0000 | 6.0000 | 16.0000 | 25.0000 | 34.0000 | 51.0000 | 80.0000 |
| Baseline | 26.0001 | 9.7885 | -4.4491 | 10.2989 | 19.1848 | 25.7884 | 32.1544 | 42.3115 | 64.2718 |
| Tradicional | 26.0122 | 9.9503 | -9.2700 | 10.3103 | 19.0946 | 25.7764 | 32.4438 | 42.7504 | 64.2005 |
| Profundo | 26.0072 | 9.8931 | -3.4788 | 10.2371 | 19.1592 | 25.8013 | 32.2308 | 42.7937 | 64.8369 |
| Combinado | 26.0178 | 9.9377 | -4.5779 | 10.4438 | 19.0801 | 25.7751 | 32.3669 | 42.7830 | 63.7177 |
| Dummy | 25.9920 | 0.0259 | 25.9600 | 25.9600 | 25.9732 | 25.9941 | 25.9966 | 26.0363 | 26.0363 |

### Holdout V0.6 — n=2.592

| Modelo | MAE | RMSE | R² | Resíduo médio |
|---|---|---|---|---|
| Baseline | 7.2029 | 9.2573 | 0.5568 | -0.0501 |
| Tradicional | 7.1831 | 9.2095 | 0.5614 | -0.0360 |
| Profundo | 7.2990 | 9.3429 | 0.5486 | 0.0006 |
| Combinado | 7.2679 | 9.3301 | 0.5498 | 0.0299 |
| Dummy | 11.1164 | 13.9058 | -0.0001 | 0.1179 |

| Modelo | Mediana |erro| | P75 | P90 | P95 | ≤5 (%) | ≤10 (%) | ≤20 (%) | >20 n | >20 (%) |
|---|---|---|---|---|---|---|---|---|---|
| Baseline | 6.1039 | 10.1052 | 14.4882 | 18.0415 | 42.4383 | 74.5756 | 96.8750 | 81 | 3.1250 |
| Tradicional | 5.9180 | 10.1346 | 14.3920 | 18.1978 | 42.8627 | 74.4213 | 96.5664 | 89 | 3.4336 |
| Profundo | 6.1788 | 10.2169 | 14.4294 | 17.7591 | 41.3966 | 73.9583 | 96.4120 | 93 | 3.5880 |
| Combinado | 6.0951 | 10.2613 | 14.5741 | 17.9836 | 41.5509 | 73.6883 | 96.1806 | 99 | 3.8194 |
| Dummy | 9.0080 | 15.9920 | 22.0080 | 26.0080 | 27.0448 | 52.7778 | 85.9568 | 364 | 14.0432 |

| Distribuição | Média | DP | Mín | P5 | P25 | P50 | P75 | P95 | Máx |
|---|---|---|---|---|---|---|---|---|---|
| Observado | 26.1100 | 13.9053 | 0.0000 | 6.0000 | 16.0000 | 24.0000 | 34.0000 | 52.0000 | 82.0000 |
| Baseline | 26.1600 | 9.9773 | -2.4414 | 9.3787 | 19.8417 | 25.9735 | 31.9298 | 43.1431 | 62.4969 |
| Tradicional | 26.1460 | 10.2188 | -2.9124 | 9.7831 | 19.5549 | 25.7534 | 32.3387 | 43.3775 | 65.9835 |
| Profundo | 26.1093 | 9.8010 | -3.0938 | 10.4704 | 19.7946 | 25.7042 | 31.8896 | 42.6905 | 62.2154 |
| Combinado | 26.0801 | 9.9907 | -3.2170 | 10.2104 | 19.4969 | 25.6886 | 32.1007 | 42.9440 | 63.0270 |
| Dummy | 25.9920 | 0.0000 | 25.9920 | 25.9920 | 25.9920 | 25.9920 | 25.9920 | 25.9920 | 25.9920 |

### Distribuição em faixas fixas

| Faixa/corte | OOF n | Teste n |
|---|---|---|
| [0,10) | 729 | 263 |
| [10,20) | 1949 | 654 |
| [20,30) | 2187 | 720 |
| [30,40) | 1590 | 527 |
| [40,50) | 749 | 261 |
| [50,60) | 319 | 118 |
| [60,70) | 98 | 40 |
| [70,80) | 26 | 7 |
| [80,90) | 1 | 2 |
| [90,100] | 0 | 0 |
| >40 | 1093 | 389 |
| >60 | 105 | 38 |
| >80 | 0 | 2 |

Faixas [0,10), …, [90,100]; cortes >40, >60 e >80 são estritos e se sobrepõem (não somar essas linhas). Há somente 27 observações ≥70 no desenvolvimento e 9 no teste; >80: 0 e 2. Não foi aberto o alvo dos registros que não entraram na matriz final para investigar essa seleção. O perfil histórico de matching já publicado (média 27,1641 em aceitos versus 17,4467 em não aceitos, `reports/tables/selection_bias.json`) é reutilizado apenas como contexto agregado, sem reabrir esses alvos.

### Condicionamento pelo alvo versus pela previsão

Subestimar grupos definidos pelo alvo alto não demonstra, por si só, falta de calibração. O alvo tem ruído residual e maior dispersão que a estimativa condicional; mesmo um modelo calibrado pode apresentar esse padrão. A tabela por previsão pergunta algo diferente: qual observado médio entre músicas que receberam previsões semelhantes? Não houve ajuste de calibrador nem novo teste de significância.

#### Tradicional: target_bin

| Conjunto | Grupo | n | MAE | Resíduo médio | Prev. média | Obs. média | >20 (%) |
|---|---|---|---|---|---|---|---|
| development_oof | [0,10) | 729 | 8.9568 | -8.4133 | 14.1225 | 5.7092 | 3.2922 |
| development_oof | [10,20) | 1949 | 6.4748 | -4.9087 | 19.8743 | 14.9656 | 0.5131 |
| development_oof | [20,30) | 2187 | 5.2324 | -1.0196 | 25.4156 | 24.3960 | 0.0457 |
| development_oof | [30,40) | 1590 | 6.0328 | 3.0152 | 30.9753 | 33.9906 | 1.5094 |
| development_oof | [40,50) | 749 | 8.9440 | 8.0070 | 35.7326 | 43.7397 | 8.6782 |
| development_oof | [50,60) | 319 | 14.1138 | 13.7230 | 39.8977 | 53.6207 | 25.0784 |
| development_oof | [60,70) | 98 | 18.8042 | 18.6835 | 44.8370 | 63.5204 | 51.0204 |
| development_oof | [70,80) | 26 | — | — | — | — | — |
| development_oof | [80,90) | 1 | — | — | — | — | — |
| development_oof | [90,100] | 0 | — | — | — | — | — |
| holdout_v0_6 | [0,10) | 263 | 8.3885 | -7.6420 | 13.1705 | 5.5285 | 3.8023 |
| holdout_v0_6 | [10,20) | 654 | 6.7701 | -5.3565 | 20.2923 | 14.9358 | 0.1529 |
| holdout_v0_6 | [20,30) | 720 | 5.2664 | -1.1669 | 25.4224 | 24.2556 | 0.2778 |
| holdout_v0_6 | [30,40) | 527 | 5.9801 | 3.1027 | 30.9523 | 34.0550 | 0.7590 |
| holdout_v0_6 | [40,50) | 261 | 9.2859 | 7.8935 | 36.0452 | 43.9387 | 6.1303 |
| holdout_v0_6 | [50,60) | 118 | 13.6894 | 13.2663 | 40.6913 | 53.9576 | 26.2712 |
| holdout_v0_6 | [60,70) | 40 | 18.1659 | 18.0785 | 45.0715 | 63.1500 | 45.0000 |
| holdout_v0_6 | [70,80) | 7 | — | — | — | — | — |
| holdout_v0_6 | [80,90) | 2 | — | — | — | — | — |
| holdout_v0_6 | [90,100] | 0 | — | — | — | — | — |

#### Tradicional: prediction_bin

| Conjunto | Grupo | n | MAE | Resíduo médio | Prev. média | Obs. média | >20 (%) |
|---|---|---|---|---|---|---|---|
| development_oof | [0,10) | 340 | 5.6607 | 3.1860 | 7.0082 | 10.1941 | 1.4706 |
| development_oof | [10,20) | 1805 | 6.5547 | 0.2312 | 15.8514 | 16.0825 | 2.5485 |
| development_oof | [20,30) | 3021 | 7.2070 | -0.8860 | 25.1329 | 24.2469 | 3.0785 |
| development_oof | [30,40) | 1814 | 7.3963 | 0.1494 | 34.4140 | 34.5634 | 4.9614 |
| development_oof | [40,50) | 552 | 7.5286 | 1.0432 | 43.3499 | 44.3931 | 6.5217 |
| development_oof | [50,60) | 94 | 7.7297 | 0.9408 | 53.2294 | 54.1702 | 4.2553 |
| development_oof | [60,70) | 11 | — | — | — | — | — |
| development_oof | [70,80) | 0 | — | — | — | — | — |
| development_oof | [80,90) | 0 | — | — | — | — | — |
| development_oof | [90,100] | 0 | — | — | — | — | — |
| holdout_v0_6 | [0,10) | 134 | 5.0415 | 2.4331 | 6.3654 | 8.7985 | 0.7463 |
| holdout_v0_6 | [10,20) | 557 | 6.3526 | -0.1915 | 15.9240 | 15.7325 | 1.7953 |
| holdout_v0_6 | [20,30) | 1055 | 7.3505 | -0.9202 | 25.0860 | 24.1659 | 3.0332 |
| holdout_v0_6 | [30,40) | 604 | 7.9725 | 0.3368 | 34.1930 | 34.5298 | 5.6291 |
| holdout_v0_6 | [40,50) | 193 | 7.9096 | 1.9699 | 43.5534 | 45.5233 | 5.6995 |
| holdout_v0_6 | [50,60) | 39 | 6.2938 | 0.8812 | 53.7341 | 54.6154 | 2.5641 |
| holdout_v0_6 | [60,70) | 7 | — | — | — | — | — |
| holdout_v0_6 | [70,80) | 0 | — | — | — | — | — |
| holdout_v0_6 | [80,90) | 0 | — | — | — | — | — |
| holdout_v0_6 | [90,100] | 0 | — | — | — | — | — |

#### Tradicional: period_diag

| Conjunto | Grupo | n | MAE | Resíduo médio | Prev. média | Obs. média | >20 (%) |
|---|---|---|---|---|---|---|---|
| development_oof | 2000-2009 | 2087 | 7.0111 | 0.2068 | 19.7309 | 19.9377 | 3.7374 |
| development_oof | 2010-2019 | 5312 | 6.9855 | -0.0685 | 28.1915 | 28.1229 | 3.3133 |
| development_oof | 2020-2023 | 249 | 9.0945 | -0.8913 | 32.1684 | 31.2771 | 8.4337 |
| holdout_v0_6 | 2000-2009 | 713 | 7.0209 | -0.1041 | 19.7086 | 19.6045 | 3.2258 |
| holdout_v0_6 | 2010-2019 | 1802 | 7.1849 | -0.0289 | 28.3569 | 28.3280 | 3.2741 |
| holdout_v0_6 | 2020-2023 | 77 | 8.6411 | 0.4272 | 34.0143 | 34.4416 | 9.0909 |

#### Tradicional: any_version

| Conjunto | Grupo | n | MAE | Resíduo médio | Prev. média | Obs. média | >20 (%) |
|---|---|---|---|---|---|---|---|
| development_oof | false | 7264 | 7.0482 | -0.0203 | 26.2831 | 26.2628 | 3.5931 |
| development_oof | true | 384 | 7.3060 | -0.0178 | 20.8876 | 20.8698 | 3.6458 |
| holdout_v0_6 | false | 2494 | 7.1828 | 0.0016 | 26.2810 | 26.2827 | 3.4082 |
| holdout_v0_6 | true | 98 | 7.1901 | -0.9950 | 22.7093 | 21.7143 | 4.0816 |

No Tradicional do teste, por alvo: MAE 18,1659 na faixa [60,70), n=40, contra 5,2664 em [20,30), n=720. Por previsão: as médias observadas de 15,7325, 24,1659 e 34,5298 acompanham previsões médias de 15,9240, 25,0860 e 34,1930 nas faixas centrais. Há desvios descritivos nos extremos, mas não evidência suficiente para aplicar uma correção global arbitrária. No período 2020–2023, MAE 8,6411 (n=77), versus 7,0209 em 2000–2009 (n=713); composição de gênero/artistas e tamanho amostral diferem. As flags de versão não concentram sozinhas todo o erro: MAE 7,1901 (n=98) com flag e 7,1828 (n=2.494) sem flag.

Gêneros, períodos, cada flag, quatro blocos e Dummy: resultados completos no CSV agregado; células pequenas explicitamente identificadas, sem ranking conclusivo de grupos raros.

### Quanto os blocos mudam as previsões?

| Conjunto | A | B | n | Pearson | Média |Δŷ| | Mediana | P95 | Máximo | |Δŷ|>5 (%) |
|---|---|---|---|---|---|---|---|---|---|
| development_oof | Baseline | Tradicional | 7648 | 0.9788 | 1.5741 | 1.3542 | 3.6900 | 45.4337 | 1.2422 |
| development_oof | Baseline | Profundo | 7648 | 0.9785 | 1.6199 | 1.3534 | 4.0595 | 12.5208 | 1.4906 |
| development_oof | Baseline | Combinado | 7648 | 0.9632 | 2.1166 | 1.7786 | 5.1833 | 32.6744 | 5.6878 |
| development_oof | Tradicional | Profundo | 7648 | 0.9698 | 1.8892 | 1.5974 | 4.6552 | 46.8358 | 3.5303 |
| development_oof | Tradicional | Combinado | 7648 | 0.9840 | 1.4052 | 1.1844 | 3.4570 | 12.7593 | 0.6276 |
| development_oof | Profundo | Combinado | 7648 | 0.9842 | 1.3751 | 1.1905 | 3.2365 | 34.0764 | 0.4838 |
| holdout_v0_6 | Baseline | Tradicional | 2592 | 0.9842 | 1.4654 | 1.2670 | 3.4379 | 9.0575 | 0.4244 |
| holdout_v0_6 | Baseline | Profundo | 2592 | 0.9810 | 1.5240 | 1.2759 | 3.8047 | 10.9168 | 1.0802 |
| holdout_v0_6 | Baseline | Combinado | 2592 | 0.9689 | 1.9860 | 1.6804 | 4.8880 | 12.1432 | 4.3981 |
| holdout_v0_6 | Tradicional | Profundo | 2592 | 0.9751 | 1.8093 | 1.5325 | 4.4648 | 10.1192 | 2.9321 |
| holdout_v0_6 | Tradicional | Combinado | 2592 | 0.9867 | 1.3122 | 1.0906 | 3.2789 | 9.6274 | 0.4244 |
| holdout_v0_6 | Profundo | Combinado | 2592 | 0.9874 | 1.2932 | 1.1491 | 2.9222 | 8.1695 | 0.3086 |

No teste, os acréscimos textuais mudam a previsão Baseline em média 1,4654 / 1,5240 / 1,9860 pontos; correlações 0,9842 / 0,9810 / 0,9689. Isso é compatível com contribuição incremental pequena, não prova inutilidade de letras. O ganho de MAE oficial do Tradicional é apenas 0,019798 ponto; não redefinir o candidato usando o holdout. PCAs retêm variância de X, não necessariamente o sinal mais relevante a y; não há teste aqui que demonstre que trocar o embedding solucionaria a cauda.

## 5. Entradas efetivas e função de ajuste

| Modelo | Inputs | Depois de transformar | PCA LFM | PCA MiniLM |
|---|---|---|---|---|
| Baseline | 23 | 110 | — | — |
| Tradicional | 219 | 187 | 77 | — |
| Profundo | 407 | 295 | — | 185 |
| Combinado | 603 | 372 | 77 | 185 |

Baseline: 23 entradas. Categóricas nominais: genre, key, time_signature → imputação pela moda e one-hot; desconhecidas ignoradas. As outras 20 entradas usam mediana + indicador de ausência e padronização: year (linear), características acústicas, mode binária e oito flags semânticas booleanas. As flags não foram confundidas com qf_* técnicas: estão explicitamente permitidas. Remoção de constantes ocorre após concatenar, não uma proibição semântica de flags. Listas, ordem, dtypes e dimensões conferem com o manifesto.

LFM2b: 196 descritores, imputação e indicadores, remoção de constantes, escala, PCA90 com 77 componentes, escala dos scores. MiniLM: 384 dimensões, PCA90 separada com 185 componentes; não mistura Baseline com textos. Cada PCA final registra n_samples_=7.648; a auditoria anterior V0.5 verificou os ajustes dentro dos folds. Nesta etapa somente transform/predict e inspeção de objetos já ajustados.

Elastic Net minimiza perda quadrática penalizada L1/L2; a seleção interna minimizou MAE médio de três folds. Não são a mesma função objetivo. Isso é escolha metodológica documentada, não bug: justifica testar uma alternativa alinhada ao MAE, sem garantir redução de erros extremos. O coeficiente linear de year e os efeitos one-hot de genre são relevantes nas decomposições privadas, mas suas semânticas limitadas pedem cautela antes de atribuir causas.

## 6. Gráficos agregados novos (V0.7)

- `reports/figures/diagnostico_v0_7/distribuicoes.png`: alvo versus previsões brutas; frequências por intervalos de dez pontos

- `reports/figures/diagnostico_v0_7/erro_acumulado.png`: fração com erro absoluto até cada limiar inteiro, sem exportar pontos individuais

- `reports/figures/diagnostico_v0_7/erro_por_alvo.png`: MAE e resíduo médio condicionados à faixa observada; não é sozinho diagnóstico de calibração

- `reports/figures/diagnostico_v0_7/observado_por_previsao.png`: observado médio em faixas da previsão; n anotado refere-se ao Tradicional

Os quatro gráficos V0.6 permanecem byte a byte iguais. Nos gráficos de médias por faixa, células n<30 são omitidas, mas seus n permanecem no CSV. Estatísticas são descritivas, sem novos intervalos de confiança que ignorariam agrupamento por artista.

## 7. Avaliação futura e limites

A exclusão de grupos conhecidos de pilotos (coorte inteira de 2.000, suplemento de 47 e modelagem de 1.441), dos 10.240 registros finais e do preview histórico de 100 linhas deixa 25,213 representantes em 8,341 grupos. Excluir também todos os grupos que apareceram na coorte/reserva V0.4 deixa 17,275 representantes em 7,102 grupos. As listas são apenas candidatos de metadados; não um teste sorteado ou certificado como independente.

Os alvos da fonte/base foram perfilados agregadamente nas etapas iniciais (`audit.py`, `validation_v011._split_audit`, relatórios de seleção). Além disso, toda a fonte orientou regras de integração. Esta exposição agregada não equivale a treino individual, mas impede afirmar sem ressalvas que o remanescente é completamente intocado. O split original foi agrupado deterministicamente, sem estratificação por alvo; quintis foram usados no piloto/desenvolvimento, não para refazer o split agora. Nova divisão dos mesmos registros examinados não restaura independência.

O preview_100_linhas.csv foi lido exclusivamente pela projeção track_id, sem seus alvos/proxies; os grupos correspondentes foram excluídos. O script pessoal exp_base.py documenta outra inspeção head(5) da base original. Workbooks de preview/revisão e JSON de head foram inventariados, mas não abertos para evitar exposição adicional; a extensão exata de suas inspeções e de outras aberturas manuais permanece não certificada. Portanto, o inventário não é garantia de ausência de inspeção individual anterior.

Opção mais forte: amostra externa/prospectiva, protocolo e pipeline congelados antes da abertura, identidades de artista/composição/gravação verificadas sem olhar popularidade, avaliador/gestor separado. Remanescentes locais só podem sustentar avaliação condicional com inventário de exposição e regra de elegibilidade pré-registrada; se não for possível demonstrar não exposição relevante, tratá-los como exploratórios. O V0.6 serve agora para explicação, não seleção de futuras mudanças.

Sem evidência suficiente: ano original de gravação/lançamento; igualdade exata de textos LFM2b–LRCLIB ou de gravações; prevalência verdadeira de erros de flags; aliases externos não codificados; motivo externo de ausência de faixas no dataset; distribuição de popularidade dos novos candidatos (deliberadamente não lida); efeito causal das regras; ganho de qualquer revisão proposta.

## 8. Reprodutibilidade e verificações

Comandos executados, códigos de saída e limitações operacionais: seção `verification_commands` do run summary. CLI diagnóstica: `.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.diagnostics_v070`; renderização: `.\.venv\Scripts\python.exe -X utf8 -m tcc_music_popularity.diagnostics_report_v070`. Ambos produzem somente artefatos V0.7; não chamar módulos de treino/coleta. Reexecutar a CLI recalcula diagnósticos a partir dos mesmos dados autorizados e substitui apenas suas saídas V0.7; não altera artefatos científicos anteriores.

Reconciliação MAE/RMSE/R² com as métricas publicadas: 30 comparações, diferença máxima 0 (tolerância 1e-10). Joins 1:1 e contagens do funil conferidos; ausência de cruzamentos de grupos e igualdade do catálogo verificadas. Os testes da interface usam dados sintéticos via AppTest, não uma avaliação científica. Não houve inspeção manual de browser com dados novos.

## Fontes locais específicas

- `AGENTS.md`; `reports/final_sampling_protocol_v1_0.md`; `reports/final_analysis_protocol_v1_0.md`; `reports/final_sampling_report_v1_0.md`.
- `reports/lyrics_scale_report_v0_4.md`; `reports/embeddings_scale_report_v0_4.md`; `reports/cohort_reconciliation_v0_4.md`.
- `reports/final_development_execution_plan_v0_5.md`; `reports/final_matrix_audit_v0_5.md`; `reports/final_model_manifest_v0_5.json`; `reports/final_development_report_v0_5.md`.
- `reports/final_holdout_evaluation_plan_v0_5.md`; `reports/final_holdout_report_v0_6.md`; `reports/run_summary_final_holdout_v0_6.json`.
- `reports/feature_manifest_v0_1_1_revision.csv`: linhas year/genre (semântica parcial, fonte Spotify_1Million_Tracks).
- `src/tcc_music_popularity/spotify.py`: normalização e coorte temporal; `normalization.py`: padrões de versão/base_title/composition_key; `matching.py`: candidatos e aceitação 1:1.
- `src/tcc_music_popularity/final_study_v040.py`: load_target_free_source, select_representatives_without_target, deterministic_main_and_reserve.
- `src/tcc_music_popularity/modeling_recalibration_v031.py`: build_representation_transformer; `final_development_v050.py`: tune/tune_fold e freeze_models.
- `apps/streamlit_demo.py`; `src/tcc_music_popularity/local_demo.py`; `local_demo_delivery.py`: apresentação, chaves, predict e integridade.
