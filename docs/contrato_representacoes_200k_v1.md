# Contrato de representações — domínio observado (01/11/2026)

## Evidência e escopo

Auditoria 17 executada pelo pesquisador e concluída em 18,79 s: 200.000 faixas
preservadas, 77.535 aceitas e 77.535 consultas textuais com hashes/referências
verificados. 484 registros excedentes compartilham fingerprint estrito e 16 textos
ligam mais de um artista operacional. O corpus permanece multilíngue: 56.908
estimadas inglesas, 20.447 não inglesas e 180 incertas. Idioma não é rótulo humano.

Há 421 IDs do teste v0.6, 438 colisões de composição e 7.162 colisões de artista
com esse teste. As flags se sobrepõem e não são parcelas aditivas. Não alegar
nova confirmação independente. Interseção com LFM2b antigo: 13.558 IDs; 63.977
sem vínculo antigo. Mesmo nos comuns, o ID não prova que descritores representem
o mesmo texto. Manter as 77.535 observações na linha principal, sem interseção
forçada com LFM2b e sem novas buscas. Matching semanticamente correto continua
questão distinta da integridade dos arquivos; revisão dirigida permanece pendente.

## Texto comum e preservação

Única fonte de conteúdo: `accepted_text` do Parquet privado v2. Reusar a função
`normalize_lyrics_text` existente: NFC, remoção de BOM, CRLF/CR→LF, remoção de
espaços/tabs no final de cada linha e linhas vazias externas. Não remover palavras,
repetições, traduções, marcadores, estrofes ou pontuação. Não alterar a fonte:
armazenar hash SHA-256 do input normalizado separado do hash original/estrito.
O mesmo input normalizado deverá alimentar descritores e encoder; prefixos e
tokens especiais serão apenas tratamento técnico explícito do encoder.

Linhas, IDs, campos originais, resposta e pesos permanecem. O alvo futuro será
`spotify_popularity` derivado explicitamente de `popularity`; nenhum alvo é usado
para extrair descritores, formar grupos, escolher texto, filtrar idioma ou ajustar
encoder. Hashes, IDs, nomes, idioma estimado e qualidade/matching são controles,
não preditores desta etapa. Preservar as 200 mil faixas para descrição/seleção.

## Tradicional — 21 descritores lexicais e estruturais

São descritores transparentes do texto observado, sem prometer equivalência aos
196 LFM2b antigos. Não incluem sentimento, rima ou legibilidade com dicionários
ingleses aplicados indiscriminadamente. As limitações de interpretação por idioma
integram o método; avaliar ganhos em grupos linguísticos posteriormente, sem
modificar regras pelo alvo.

| Família | Definição |
| --- | --- |
| Extensão | caracteres (pontos de código Unicode, não grafemas) após normalização; caracteres não brancos; linhas não vazias; estrofes delimitadas por uma ou mais linhas vazias |
| Segmentos lexicais | sequências Unicode de letras, com apóstrofo/hífen interno; caixa uniforme para contagens. Não são palavras linguísticas universais: escrita sem espaços pode produzir segmentos longos |
| Diversidade | número de segmentos e tipos; média/DP populacional de comprimento; tipos/segmentos; tipos com ocorrência única/tipos; entropia de frequências em bits |
| Estrutura de linhas | média/DP de caracteres não brancos por linha não vazia; fração de linhas excedentes repetidas após casefold e uniformização de espaços |
| Composição gráfica | frações de letras, dígitos decimais e pontuação Unicode entre caracteres não brancos; maiúsculas entre letras |
| Interrogação/exclamação | fração de linhas não vazias com ?/？ e !/！ |
| Controle numérico incluído | flag de ausência de segmentos lexicais; denominador zero recebe zero acompanhado dessa flag. Nenhuma linha é removida por isso |

DP usa divisor n; não se aprende vocabulário global, IDF, PCA ou normalização
estatística nessa extração. Escalas e eventuais transformações aprendidas serão
ajustadas apenas em cada treino. Nenhuma tradução/stopword automática. Não declarar
que esses descritores esgotam informação linguística ou são igualmente comparáveis
em todos os idiomas. Palavras/linhas não são deduplicadas no texto fonte.

## Grupos para prevenir vazamento

Construir componentes conexos com arestas de artista conservador, composição
operacional e fingerprint textual estrito. Participações explicitamente feat./ft.
ligam o crédito principal e o crédito convidado inteiro; não dividir bandas por
&, and, vírgula ou ponto e vírgula. Essas regras não resolvem todos os pseudônimos,
colaborações ou identidades universais. As quatro exceções inspecionadas da auditoria
são do artista `!!!`: conservar chave literal, sem excluí-las por normalização vazia.
Chaves novas têm prefixo text_; preservar as chaves/flags antigas para proveniência.

O script 19 gera componentes, seus tamanhos e exposição herdada por componente;
não gera folds nem determina exclusões. Verificar componentes gigantes ou chaves
não resolvidas antes de congelar validação. As quatro configurações terão exatamente
as mesmas linhas, componentes e folds; texto repetido não deve atravessar treino/
avaliação. Hash privado identifica conteúdo para cache/auditoria, nunca preditor.

## Profundo — candidato para próxima preparação, ainda não gerado

Recomenda-se investigar `intfloat/multilingual-e5-small` para evitar adotar sem
verificação o MiniLM antigo neste corpus multilíngue. O [model card oficial](https://huggingface.co/intfloat/multilingual-e5-small)
declara licença MIT, 384 dimensões, suporte a 100 idiomas com limitações em línguas
de poucos recursos; recomenda prefixo `query: ` para features e limite de 512
tokens. Isso não comprova adequação a letras nem desempenho incremental.

Antes da geração: fixar commit/revisão e hashes do snapshot, compatibilidade local
e licença; testar pequeno; definir CPU/GPU e lotes; usar janelas que cubram todo
o texto, sobreposição documentada, pooling/L2 e cache por input/revisão/configuração.
Reusar os utilitários testados de cobertura de tokens e agregação existentes.
O snapshot multilingue não está no cache inspecionado; nenhum download foi feito.
Encoder/revisão final e execução de embeddings ficam para a próxima entrega, sem
procurar modelos pelo resultado de popularidade.

## Execução e validação pendente

Script 19 gera somente descritores e componentes, com SQLite/checkpoints e
retomada; não baixa modelos, não cria embeddings/splits e não treina. O contrato
é selado junto às fontes e código. Mudança posterior exige nova versão, sem
sobrescrever resultados incompatíveis.

Validação **aprovada pelo pesquisador em 01/11/2026**: CV aninhada agrupada 5×3, mesmos folds para
quatro blocos, seleção por MAE e RMSE secundária, com transparência sobre exposição
histórica. Registro da aprovação em `decisions.md`/`ESTADO_ATUAL.md`; o script 19 é
independente da escolha dos folds. Política de ponderação das métricas preditivas
ainda será congelada, sem presumir correção da seleção por letras.
