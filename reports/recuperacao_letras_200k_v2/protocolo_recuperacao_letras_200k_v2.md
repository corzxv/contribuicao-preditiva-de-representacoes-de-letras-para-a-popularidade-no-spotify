# Recuperação local de letras — protocolo v2

Uma rodada delimitada, preparada para o pesquisador executar. Nenhuma recuperação
real foi executada durante a implementação. Não há meta de cobertura, ciclos de
flexibilização, rede, tradução, novos modelos, descritores, splits ou alterações
da amostra. O detector de idioma já instalado pode ser reutilizado, sem download.

## Fontes confirmadas e preservação

- Amostra, resumo e alocação: `reports/amostra_spotify_200k_20261031/`.
- Primeira busca: `data/derived/private_sample_lyrics_200k_v1/state.sqlite`,
  `resultados_faixas_200k.parquet` e `letras_aceitas_200k.parquet`.
- Resumo v1: `reports/busca_local_200k_20261031/resumo_busca_local_200k.json`.
- Dump: `D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`.
- Índices anteriores: `D:\TCC_LRCLIB\tcc_lookup_v1/` e
  `D:\TCC_LRCLIB\tcc_lookup_sample_200k_v1/`, ambos `lookup.sqlite`.

O resumo v1 concluído registra 200.000 faixas: 77.391 aceitas, 25.775 ambíguas,
88.049 não encontradas, 8.748 instrumentais, 10 sem texto simples e 27 com
metadados insuficientes. Não registra erros técnicos nem pendências. A nova CLI
reconcilia essas contagens com o Parquet e o mapa de consultas SQLite. Hash da
amostra: `cbaf98e2771067ab70538068d85b029ce77fbcdfb86e8b35f34a2a7abf46faff`.

A preparação inspecionou código, relatórios, schemas e poucos metadados. Foram
observados créditos explícitos feat./ft., nomes contendo &/ponto e vírgula e
nomes/títulos apenas com símbolos. Não foram varridos dump ou letras reais.
Não se infere gramática de lista para créditos com separadores ambíguos.

V1 permanece somente leitura e sem alteração de seus selos/código. Preservar as
aceitações e instrumentais v1, inclusive texto, IDs, motivo e versão das regras.
V2 registra a origem antiga; não afirma que decisões herdadas foram revalidadas.
Riscos encontrados no código v1 (acentos/sinais colapsados, flags fora de contexto,
ausência de confronto plain/synced) são documentados separadamente, sem declarar
erros individuais ou alterar silenciosamente aceitações antigas.

Antes de executar: validar hashes da amostra/alocação e desenho congelado, 200 mil
IDs únicos, 499 faixas ≥80, soma de pesos; conferir snapshot, selos e índices
concluídos. Calcular SHA-256 do estado v1 e resultado v1 na execução pelo usuário;
o estado tem aproximadamente 6,2 GB, portanto essa validação pode levar tempo.
Retomadas exigem o mesmo selo de entrada/código/protocolo/idioma. WAL não vazio
bloqueia leitura imutável; nunca apagar WAL. Dump validado pelo checkpoint anterior,
sem repetir hash completo de 262 GB. Fonte aberta com mode=ro, immutable e query_only.

## Diagnóstico e sequência de uma única execução

1. Diagnóstico por faixa a partir de `lyrics_reason`, reconciliado com as evidências
   ao reavaliar cada consulta. Separar textos distintos, vazios bloqueando texto,
   metadados, versões, instrumental/texto, mesmo ID e limites operacionais.
2. Para `not_found`, verificar existência do crédito completo no índice v1: crédito
   não localizado versus artista localizado sem candidato de título. É diagnóstico
   no espaço de chaves v1, não prova de ausência universal no LRCLIB. Esses
   resultados ficam no JSON antes da recuperação e no CSV final.
3. Para insuficientes, distinguir campos ausentes e símbolos apagados. Nomes como
   `!!!` e títulos `$$$$` recebem chave literal; símbolos diferentes não são iguais.
   O diagnóstico integral das 27 faixas será produzido pelo comando, não foi
   presumido a partir dos poucos exemplos inspecionados na preparação.
4. Reavaliar uma vez candidatos/textos guardados no estado v1. Não consultar de novo
   aceitações/instrumentais v1; não copiar cegamente status das demais consultas.
5. Consultar uma vez o índice v2 para casos sem candidatos ou ainda em conflito de
   metadados. Textos substantivamente distintos, conflitos positivos de versão e
   limites não provocam buscas sucessivamente mais permissivas.
6. Exportar a amostra integral, os textos e os agregados antes/depois. Não substituir
   faixas, mudar pesos/estratos, selecionar hits ou criar nova amostra.

## Créditos, títulos e recuperação

Entrada fechada: artista, título, duração e vínculo por ID. Alvo, peso, gênero,
estrato e instrumentalness nunca chegam ao classificador.

Chave nova: NFC, caixa uniforme, espaços uniformes, sinais tipográficos usuais
padronizados. Pontuação separadora vira espaço; &, + e / são mantidos em nomes
com letras/números. Acentos permanecem; sem aliases, tradução ou transliteração.
Sequências exclusivamente simbólicas têm chave literal, sem colapso.

Somente feat./ft./featuring explícitos delimitam participação. O colaborador pode
estar no crédito ou em sufixo do título. Exigir o mesmo artista principal e o mesmo
crédito colaborador completo; não dividir convidados por &, and, vírgula ou
ponto e vírgula, não inferir colaboração ausente nem reordenar nomes dentro do
crédito. Créditos contraditórios nos dois campos impedem aceitação. Isso sacrifica
recuperação onde a fonte não permite interpretação inequívoca.

Qualificadores de versão são reconhecidos somente em sufixos com parênteses,
colchetes ou hífen separado por espaços. Termos: live, remix/mix, remaster(ed),
acoustic, demo, karaoke, instrumental, radio/edit, mono/stereo, clean/explicit,
extended, sped up/slowed/nightcore e version. Guardar todas as palavras do
qualificador, inclusive local, ano e produtor. Só apresentação/pontuação e
remastered→remaster podem variar. Não apagar qualificadores desconhecidos.
`Live Forever` e `Radio Ga Ga`, sem sufixo contextual, continuam títulos comuns.
Mesmo perfil live não iguala apresentações diferentes. Clean e explicit diferem.

Recuperar candidatos por igualdade simultânea de chave do artista principal e
título contextual. Depois exigir crédito colaborador, qualificadores e duração
compatíveis. Tolerância continua ≤10 s quando ambas válidas/conhecidas; duração
ausente não prova nem exclui identidade. Não usar título/artista isolado, substring,
fuzzy ou similaridade. Se houver candidato de mesmo artista/título/colaboração e
duração compatível mas versão conflitante, manter ambiguidade, mesmo que também
exista candidato elegível. Homônimos indistinguíveis nos metadados continuam risco.

Os índices v1 restringem o crédito completo; mudar somente a consulta não basta.
V2 cria `D:\TCC_LRCLIB\tcc_lookup_sample_200k_v2/lookup.sqlite`: uma passagem por
`tracks`, em lotes de 5.000 IDs, mantendo registros dos artistas principais
necessários. Usa schema, conexão e transações do índice anterior. O conjunto de
artistas é congelado no estado v2 antes da construção e permanece nas retomadas.
Não lê letras ao indexar nem varre o dump por música. Mantém os limites de 500
candidatos, 2 milhões de caracteres por registro, 8 milhões por consulta e 30 s
de orçamento SQL; limites viram ambiguidade operacional explícita, sem aumentar
automaticamente o orçamento. Timeout/I/O são erros técnicos, nunca ausência.

## Texto, equivalência e instrumentais

Registros vazios compatíveis deixam de bloquear um conjunto textual equivalente;
registrar `empty_ignored`. Não ignorar indicação instrumental conflitante,
representação textual conflitante ou versão incompatível. Todos os textos
elegíveis precisam ser equivalentes; não escolher apenas o mais próximo em duração.

LRC suportado: um timestamp `[mm:ss]`, `[mm:ss.xx]` ou `[mm:ss:xx]` por linha;
segundos 00–59; timestamps não decrescentes. Remover apenas prefixos e linhas de
metadados completas ar/al/ti/au/by/re/ve/length/offset. Preservar conteúdo após o
timestamp, ordem das linhas, linhas vazias temporizadas e repetições. Linhas vazias
sem timestamp são espaçamento do arquivo. Não converter múltiplos timestamps,
sincronização por palavra ou linhas de conteúdo sem timestamp: registrar motivo
de formato inválido/não suportado. Não expandir/reordenar silenciosamente.

Quando houver plain e synced na mesma candidatura, confrontar as representações;
conflito ou sincronização inválida impede nova aceitação. Texto derivado só substitui
plain ausente. Preservar as duas representações originais separadas de `accepted_text`.

Fingerprint estrito v1 permanece. Equivalência adicional converte exclusivamente
aspas curvas em retas, travessões em hífen, reticência Unicode em três pontos e
espaço inseparável em espaço comum, antes do fingerprint estrito. Não remove
pontuação, palavras, acentos, caixa, versos, traduções, marcadores ou repetições.
Não usa bags/sets de palavras ou similaridade. Caso substantivo permanece separado.
Representante determinístico após equivalência: duração, completude e ID, como v1.

Preservar 8.748 instrumentais v1. Novos instrumentais exigem todos os elegíveis
marcados pela fonte sem texto; ausência de letra não basta. Comparar descritivamente
a marcação original LRCLIB, instrumentalness contínua (quantis/ausências, sem corte)
e presença contextual de instrumental no título. Nenhum indicador é verdade absoluta.

## Checkpoints, produtos e interpretação

Workspace: `data/derived/private_sample_lyrics_200k_v2/`. Mesmo padrão SQLite/lock
e exportador v1, com controle adicional de fase cache/lookup/done. Transação por
decisão; importação e consultas retomáveis. Repetir o mesmo comando pula concluídas;
`--retry-errors` permite até três tentativas locais por consulta técnica. Falha
para o lote. Ctrl+C/queda mantém commits e resultado incompleto. Nenhum laço muda
regras até alcançar cobertura. `--limit` limita só novas consultas, não diagnóstico,
reavaliação do cache ou construção do índice.

Privados: `state.sqlite`, `progress.json`, `diagnostico_inicial_privado.parquet`,
`resultados_faixas_200k.parquet`, `letras_aceitas_200k.parquet` e
`amostra_inspecao_novas_aceitacoes.json`. Resultado tem uma linha por track_id,
todos os campos/desenho originais, campos anteriores prefixados `v1_`, status novo,
motivo/método, regra exclusiva de recuperação, quantidade de vazios ignorados,
origem textual, hashes e transformações por candidato. Letras ligadas por query_id,
sem multiplicar faixas. Proveniência de cache aponta a evidência v1 preservada.

Inspeção privada: até três consultas novas por combinação de regras, selecionadas
deterministicamente por track_id; texto, metadados e origem, com revisão humana
pendente. Não é amostra de validação probabilística nem estimativa de precisão.

Públicos em `reports/recuperacao_letras_200k_v2/`: protocolo, relatório, resumo JSON,
CSV de diagnóstico inicial, transições, recuperações por regra, perdas restantes,
comparação de instrumentais, comparação de cobertura antes/depois e três gráficos.
Nenhum texto, trecho, token, ID de faixa/consulta/LRCLIB ou hash individual de letra.
Hashes de arquivo/código/fonte são permitidos para proveniência.

Cada faixa recuperada pertence a uma combinação exclusiva de regras; a soma
reconcilia com a diferença de aceitações, sem somar componentes sobrepostos.
Comparação reutiliza `coverage_tables`: amostra completa × aceitas × não aceitas
e status, sem/com pesos, denominadores explícitos, diferenças descritivas de
proporções e médias padronizadas, sem p-valores como selo. CSV `phase` identifica
before/after; `n_tracks` é real, `sum_weights` é soma dos pesos congelados. As 499
faixas ≥80 só aparecem no recorte posterior 80–89/90–100. Não entram na decisão.

Pesos não corrigem seleção por disponibilidade/aceitação de letras. Proximidade
das barras e grande n não demonstram representatividade ou generalização além
do catálogo/snapshot. Não há afirmações causais. Exposição prévia do teste V0.6
permanece. Cobertura, recuperações e tempos v2 reais só serão conhecidos após
execução; testes sintéticos demonstram comportamento, não precisão em dados reais.
