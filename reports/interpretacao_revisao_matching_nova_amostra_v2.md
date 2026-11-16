# Resultado real da revisão 43

**3.647 letras aceitas de 9.526 faixas: 38,28% sem ponderação, 38,30% com os
pesos originais do sorteio.** Revisão concluída em 41,79 segundos, sem erro,
novo índice ou mudança de amostra. Ganho real de **2.222 letras** sobre 42.

| Resultado | Antes (42) | Depois (43) |
|---|---:|---:|
| Aceitas | 1.425 | 3.647 |
| Ambíguas | 3.574 | 1.298 |
| Sem candidato nas chaves controladas | 4.164 | 4.164 |
| Sem texto | 1 | 1 |
| Indicação instrumental | 362 | 416 |
| Erro técnico/pendente | 0 | 0 |

As 1.425 aceitas e 362 instrumentais anteriores foram mantidas; 54 ambiguidades
passaram a indicação instrumental quando a versão compatível pôde ser avaliada.
Instrumental continua sendo indicação do LRCLIB, não confirmação humana ou
derivação de instrumentalness do Spotify. Nenhum resultado anterior foi apagado.

Dos 2.139 bloqueios iniciais plain/LRC, 1.614 viraram aceitações. Dos 1.176 por
versão, 608 viraram aceitações e 54 instrumentais; 153 sem elegível permaneceram
ambíguas e fora da correção. Os demais casos mostram conflitos persistentes.
O ganho comprova o impacto dos dois bloqueios, sem demonstrar qualidade humana
de cada vínculo ou que todas as ambiguidades restantes sejam irrecuperáveis.

## Ambiguidades remanescentes

| Motivo atual | Faixas |
|---|---:|
| Textos concorrentes distintos sob a comparação atual | 831 |
| Versões sem candidato elegível | 153 |
| Metadados incompatíveis | 152 |
| Divergência plain/LRC persistente | 108 |
| Limite de candidatos | 40 |
| Conflito instrumental/texto | 8 |
| Formatos/timestamps LRC não suportados ou inválidos | 6 |

Em oito consultas ilustrativas do primeiro motivo, a uniformização de whitespace
não fez todos os textos coincidirem. Isso não mede prevalência ou qualidade
semântica dos 831; orienta não repetir uma flexibilização geral sem diagnóstico.

## Cobertura continua seletiva

Taxa ponderada de aceitação: 35,62% em 2000–2009, 40,35% em 2010–2019 e 39,07%
em 2020–2023. Por faixa de popularidade: 28,22% em 0–19, 50,41% em 20–39 e
58,18% em 40–59. A cauda ≥80 tem somente cinco sorteadas/uma aceita, insuficiente
para uma conclusão estável. São taxas observadas de recuperação/aceitação, não
probabilidades verdadeiras conhecidas de disponibilidade de letras.

Dois gêneros não têm aceitas; sleep tem zero de 147, minimal-techno uma de 125,
guitar seis de 142. Os pesos do sorteio não corrigem automaticamente essa seleção.
Não transferir a margem de dimensionamento da amostra completa ao subconjunto
com letras nem afirmar representatividade textual do catálogo.

## Investigar os 4.164 sem candidato

Doze consultas inspecionadas por metadados nos índices existentes e em consultas
nativas limitadas. Houve um exemplo com mesmo título/duração próxima, mas
artista “Secret & Whisper”/“Secret and Whisper”. Um título também apareceu com
outros artistas, o que não é justificativa para aceitar outra gravação.
Não extrapolar esse conjunto determinístico aos 4.164.

O dump tem índices nativos name_lower/artist_name_lower e FTS5. Planos de acesso
verificados sem varredura. 44 foi preparado para diagnosticar os 4.164 usando
esses índices, **sem alterar status ou aceitar letras**; candidatos são propostas
privadas para revisão. Guia: docs/execucao_diagnostico_chaves_nova_amostra_v1.md.
Nenhum treino, encoder, novo PDF ou publicação nesta análise.
