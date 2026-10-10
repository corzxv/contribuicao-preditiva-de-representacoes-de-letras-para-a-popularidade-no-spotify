# Protocolo final de amostragem — v1.0

## Regra congelada

- Seed: `20261010`.
- Coorte principal: 14000 composições, sendo 10500 de desenvolvimento e 3500 de holdout.
- Reserva ordenada: 2000 composições, sendo 1500 de desenvolvimento e 500 de holdout.
- A ordenação é o SHA-256 determinístico de seed, versão, split e `composition_key`. A reserva é a continuação da mesma permutação em cada split.
- Nenhuma popularidade, proxy de sucesso, disponibilidade de letra, cache ou resultado do piloto participa da seleção.

## Representante por composição

Regra idêntica ao piloto e sem popularidade: preferência por registros sem flags live/remix/acoustic/karaoke; maior confiança por status, método e score de matching congelados; maior completude de artista, título e duração; menor `spotify_row_id` e depois menor `track_id` como desempate estável.

## Reserva

A reserva somente será consultada se a coorte principal produzir menos de 10.000 letras aceitas. A ativação ocorrerá em até quatro lotes fixos de 500, cada um com 375 desenvolvimento e 125 holdout, interrompendo ao atingir 10.000 aceitas ou esgotar 2.000 casos. Não haverá substituição individual.

## Integridade

- Hash SHA-256 do arquivo completo da coorte: `119dc1ded7a61b67a4ed6116ba46758ae5e8a5c867f74775c5e74a8618123f8c`.
- Hash SHA-256 do arquivo completo da reserva: `1e6c0da25f6a068d1a5971cf0655e5cc5a966999a827b4287c46b63e65fe9574`.
- Hash lógico target-free da coorte: `3646c15e0164ca1ef5677ff649983439d25f0c6f9426d4d44e79c3986a17cd91`.
- Hash lógico target-free da reserva: `fd827a6f304fdde10335617c468acbba44f6f731d4926a9fad2cb3f02dd4ebfb`.
