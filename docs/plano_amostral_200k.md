# Plano amostral fixo — 200.000 faixas Spotify

Protocolo preparado em 31/10/2026. Este documento especifica o desenho; não
apresenta resultados de uma amostra real ainda não executada. O relatório da
execução registrará a reconciliação da população e a alocação realizada.

## População, unidade e alcance

A população de referência é o CSV anterior ao matching identificado por caminho,
tamanho e SHA-256 no `resumo_catalogo_spotify.json` concluído. A auditoria local
de 31/10/2026 registra 1.159.764 linhas e IDs distintos e 499 faixas com
`popularity >= 80`; são evidências anteriores, que serão recalculadas antes do
sorteio. Hash registrado:
`42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897`.

A unidade sorteada é `track_id`. O alcance das inferências é esse catálogo,
não todo o Spotify. Uma faixa não equivale necessariamente a uma gravação nem a
uma composição. Títulos repetidos, versões e créditos colaborativos permanecem;
não há deduplicação por título, artista+título ou escolha da maior popularidade.
Nenhum título-base, classificador de versões ou grupo de composição é criado.

As contagens textuais usam espaços U+0020 aparados e tratam como ausentes NULL
ou os tokens exatos `""`, `NA`, `N/A`, `null`, `None`. Caixa, acentos e ordem dos
créditos são preservados: não se desambiguam pessoas, aliases ou colaborações.
Pares completos exigem crédito e título não ausentes. Títulos distintos não são
composições únicas, e créditos textuais distintos não são artistas identificados.
Campos originais, inclusive índice sem nome e strings de ausência, são
preservados no Parquet como texto; derivações têm nomes separados.

## Fundamento metodológico e escolhas operacionais

A amostragem probabilística associa seleção aleatória a probabilidades
calculáveis. A amostragem estratificada divide a população em estratos e permite
sorteio dentro deles; na amostragem aleatória simples sem reposição, unidades
não se repetem. Esses fundamentos estão na seção [Probability sampling, da
Statistics Canada](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm).

O manual [Survey Methods and Practices, catálogo 12-587-X](https://www150.statcan.gc.ca/pub/12-587-x/12-587-x2003001-eng.pdf)
trata do desenho no capítulo 6 (em particular 6.2.2 e 6.2.6), de ponderação e
estimação no capítulo 7, e de tamanho/alocação no capítulo 8. Sua seção 7.1
define o peso de desenho como inverso da probabilidade; a seção 8.2.2 distingue
alocação proporcional e desproporcional. Referência: Statistics Canada, edição
eletrônica de 2010, originalmente publicada em 2003; consulta em 31/10/2026.

**Escolhas deste estudo, não prescrições dessas fontes:** total 200.000, seed
20261031, limiar 80, limites dos períodos/bandas, reserva mínima de duas unidades,
alocação por capacidades residuais e desempate determinístico. O total é um
orçamento operacional fixado pelo pesquisador para viabilizar etapas futuras;
não é tamanho ótimo demonstrado, cálculo de poder ou garantia baseada em margem
de erro de proporções. Proteger a cauda de popularidade evita perder casos
raros do catálogo e permite descrevê-los; não demonstra desempenho preditivo.

## Desenho e estratos

Sorteio aleatório simples sem reposição dentro de cada estrato não integral.
Total **exatamente 200.000 IDs**, com seed **20261031**.

1. Estrato integral: todas as faixas de popularidade ≥80. Integram as 200.000,
   com probabilidade 1 e peso 1; não são acrescentadas após o sorteio.
2. Restante: cruzamento da célula de gênero registrada com os períodos
   2000–2009, 2010–2019, 2020–2023 e as bandas 0–19, 20–39, 40–59, 60–69, 70–79.

`year` é o campo informado pela fonte; seu significado como ano original de
lançamento não está confirmado. Nenhuma data é inferida de títulos ou LRCLIB.
Versões, idiomas, títulos/artistas ausentes e atributos acústicos não condicionam
elegibilidade nem estratificação. Gênero não é dividido ou reagrupado.

Antes do sorteio, conferir hash/tamanho, linhas/IDs, cauda ≥80, schema original
e contagens/domínios anuais e de gênero contra a auditoria. Exigir IDs presentes
e únicos, popularidade inteira finita em 0–100, gênero presente e ano em quatro
dígitos entre 2000 e 2023. Qualquer divergência bloqueia a execução sem excluir
registros. Tanto duplicatas iguais como conflitantes bloqueiam o sorteio; não
se tenta corrigi-las. Problemas acústicos e ausências em artista/título são
quantificados, mantendo as faixas na população.

## Alocação determinística

Seja H o número de faixas ≥80, com alocação integral H. Para cada outro estrato
não vazio de tamanho N_h:

- Reserva b_h = min(2, N_h).
- Orçamento residual R = 200.000 − H − soma(b_h). Se R < 0, interromper.
- Capacidade residual c_h = N_h − b_h; C = soma(c_h).
- Distribuir R proporcionalmente a c_h: q_h = R c_h / C.
- Atribuir inicialmente n_h = b_h + piso(q_h). Distribuir as vagas restantes
  aos maiores restos, desempate pela chave estável crescente do estrato.

A implementação usa `divmod(R*c_h, C)` com inteiros, evitando desempates
acidentais de ponto flutuante. Se C=0, somente R=0 é admissível. Verificar
0 < n_h ≤ N_h e soma total igual a 200.000. Estratos de uma ou duas faixas são
integrais; outros também podem tornar-se integrais após a alocação.

O mínimo de duas unidades é proteção operacional de pequenos estratos, não
garantia de poder, precisão ou possibilidade de modelagem em cada estrato.
O desenho é **desproporcional**: inclusão integral da alta popularidade e
reservas mínimas alteram a alocação. Não é alocação proporcional pura nem ótima.

Chaves: `C|popularity>=80` para o estrato integral; `S|` seguido de um vetor JSON
compacto `[gênero, período, banda]` para os demais. Estratos e IDs são ordenados
lexicograficamente por Unicode, em ordem crescente. Usa-se
`numpy.random.Generator(numpy.random.PCG64(20261031))` e
`choice(N_h, n_h, replace=False)`. Estratos integrais não consomem números
aleatórios. Não há busca de seed ou repetição para melhorar equilíbrio.
Uma repetição interna idêntica verifica reprodução e é descartada, sem comparar
equilíbrio ou selecionar entre alternativas. Versões Python/NumPy/Polars e
hashes do código e configuração são registrados.

## Probabilidades, pesos e estimação

Para cada faixa do estrato h: pi_h = n_h/N_h e w_h = 1/pi_h = N_h/n_h.
`certainty_selection` indica n_h=N_h, inclusive pequenos estratos integrais.
O arquivo individual registra `stratum_id`, `N_h`, `n_h`,
`inclusion_probability`, `sampling_weight`, `certainty_selection` e `seed`.

A estimativa ponderada da média é:

\[
\widehat{\mu}=\frac{\sum_{i\in s}w_i y_i}{\sum_{i\in s}w_i}.
\]

Para variável com ausências ou valores não finitos, o numerador e o denominador
usam somente as observações válidas para aquela métrica. Publicar tanto o número
observado quanto a soma de pesos válidos. Isso descreve os valores disponíveis;
não corrige mecanismo de ausência. Frequências de ausência/invalidade usam toda
a população/amostra no denominador. O CSV distingue `n_observed` (casos reais)
de `count` (soma de pesos, ou contagem quando todos os pesos são 1).

Quantis: inversa da CDF empírica ponderada. Ordenar os valores finitos, acumular
os pesos positivos e escolher o menor valor cujo peso acumulado atinja q vezes
o peso total válido; não interpolar. Usar a mesma definição com pesos 1 no
catálogo e na amostra sem pesos. Informar P1, P5, P25, P50, P75, P95 e P99.
P50 é a mediana. O desvio-padrão descritivo é
sqrt(soma(w_i*(y_i−média)^2)/soma(w_i)), com divisor W; não é erro-padrão,
estimador de variância do desenho ou intervalo de confiança. A auditoria
anterior usou quantis interpolados e divisor n−1: convenções diferentes.

As 13 variáveis acústicas são danceability, energy, key, loudness, mode,
speechiness, acousticness, instrumentalness, liveness, valence, tempo,
duration_ms e time_signature. Resumir todos os valores finitos e, separadamente,
os que atendem às regras locais de `configs/quality_rules.yaml`; falhas não
retiram faixas. A duração é em milissegundos. Não inventar limites para loudness.

Créditos distintos e sua distribuição de frequência são contagens observadas.
Não estimar riqueza populacional somando pesos de artistas observados. A
concentração ponderada ordena créditos observados pela soma dos pesos de suas
faixas; é um resumo plug-in do conjunto observado, não estimativa não enviesada
do ranking populacional. Nenhum nome/ID/título individual aparece nos agregados.

## Validação e interpretação

Exigir total exato, IDs únicos pertencentes ao catálogo, todas as faixas ≥80,
alocação realizada igual à planejada, probabilidades em (0,1], pesos finitos
positivos e soma dos pesos igual ao N do catálogo (tolerância relativa 1e−12,
absoluta 1e−6). Verificar reprodução e igualdade dos campos após reler o Parquet.

Comparar catálogo, amostra sem pesos e com pesos. Diferenças sem pesos são
esperadas. Gênero, período e bandas do desenho têm totais ponderados preservados
por construção, salvo arredondamento numérico; isso não é prova de validade
externa. Anos individuais, valores pontuais de popularidade e atributos
acústicos podem diferir. Equilíbrio observado não garante erro preditivo pequeno.
Não usar testes de significância como selo de representatividade.

## Etapas posteriores e exposição anterior

A disponibilidade/aceitação futura de letras pode introduzir seleção adicional;
pesos do sorteio não a corrigem automaticamente. Preservar a amostra original
mesmo para faixas sem letra, sem substituição automática. LFM2b não condiciona
elegibilidade e a cobertura LRCLIB histórica não é extrapolada.

Splits e dependência entre artistas, gravações e versões serão tratados
posteriormente, com reconciliação dos registros/grupos anteriores e agrupamento
por artista e composição operacional. O teste V0.6 foi aberto em 14/10/2026,
conforme `reports/run_summary_final_holdout_v0_6.json`; novo sorteio não apaga sua
exposição nem restaura automaticamente independência. Nenhum split, grupo ou
modelo é criado nesta etapa.

## Preservação e produtos da execução

O Parquet individual permanece local e é ignorado pelo Git. A entrada é aberta
somente para leitura; todas as colunas originais são mantidas. A pasta nova recebe
protocolo, alocação, amostra, comparação, relatório, resumo JSON e três gráficos
(popularidade, gênero e período), com contagens visíveis da cauda rara.

Reexecução na mesma pasta só é aceita se já estiver concluída, com a mesma
entrada/auditoria/configuração/versões e todos os hashes de saída intactos:
verificar e reutilizar, sem sobrescrever ou sortear de novo. Divergências ou
execução incompleta bloqueiam a reexecução; não produzir alternativa silenciosa.
`completed: true` e `status: completed` no JSON são necessários para usar a saída.
Antes de criar a pasta, falhas de hash/referência são informadas no terminal.
