# Piloto de revisão da vinculação — v1.1 (correção de 05/11/2026)

Adendo técnico: o campo popularity original é texto no Parquet. Criar coluna
review_popularity_numeric Float64, validar valores e usá-la na ordenação e na
comparação ≥80; preservar o campo original. A v1 falhou antes da seleção e suas
pastas ficam intactas. A v1.1 usa pastas novas, mantendo os critérios de seleção.

## Objetivo e alcance

Identificar mecanismos de falha e capacidade de revisar a integração existente,
antes de justificar outro cruzamento integral. O piloto 32 prepara fichas; não
altera aceitação, texto, amostra, índice, modelo ou folds. Não executa o script 15.
Não acessa dump/SSD, API, rede, pesos de encoder ou inferência de embeddings.

Fontes: resultados_faixas_200k.parquet da v2 e state.sqlite locais de v1/v2.
Uma leitura projetada das 200 mil linhas é execução manual pelo pesquisador.
Cache consultado somente por chave primária de evidence, com EXPLAIN exigindo
SEARCH, sem varredura de payloads. Arquivos abertos mode=ro, immutable,
query_only; WAL não vazio bloqueia. Não refazer hash de bancos de vários GB:
registrar caminho, tamanho, mtime e estabilidade, distinguindo de hash integral.

## Unidade e seleção

Unidade de revisão: consulta única representada na amostra de 200 mil, não faixa
nem população LRCLIB. Excluir explicitamente consultas ausentes e publicar sua
contagem. Exigir consistência do status dentro da consulta. Representante para
estratificação: maior popularidade entre suas faixas, desempate pelo menor ID.
Não passar popularidade à regra de vinculação.

Estratos: seis status v2 × indicador de pelo menos uma faixa ≥80. Sortear até
vinte consultas de cada célula não vazia, sem reposição, PCG64/seed 20261104,
ordenação por consulta e ordem de status fixada no código. Registrar N, n e n/N
para cada célula. Máximo 240 consultas; células pequenas são integrais. Não
somar pesos desse piloto com os pesos da amostra Spotify. Correlações entre
consultas de um artista/composição continuam relevantes para eventual incerteza.

## Evidências e revisão

Tentar cache v2 antes de v1, com identificador atual e identificador herdado.
Payload acima de 2 MiB não é carregado. Ficha contém até cinquenta candidatos
com artista, título, álbum, duração, versão inferível do texto do título,
indicador instrumental e presença de texto. Truncamento e limites da evidência
são visíveis. Não exportar corpo de letra nem considerar ausência de cache como
prova de ausência no LRCLIB. Metadados sozinhos podem ser inconclusivos.

Manifesto privado conserva status anterior, motivo, estrato e candidato selecionado.
Ficha de revisão omite popularidade e status anterior para reduzir indução da
decisão; isso é mascaramento parcial, não estudo cego certificado. Campos humanos
começam vazios: identidade, versão, decisão e notas. Decisões possíveis a definir
na revisão: compatível nos metadados, conflito, evidência insuficiente. Não
promover compatibilidade em metadados a identidade semântica humana confirmada.

Reexecução da mesma versão preserva a ficha existente, inclusive anotações. Selo
incompatível interrompe; não sobrescrever revisão feita. Bases/índices anteriores
permanecem somente leitura. Saídas individuais em data/derived/private_linkage_review_200k_v1_1/,
ignoradas pelo Git; reports/piloto_vinculacao_200k_v1_1/ contém somente agregados.

## Critério para ampliar

completed=true indica preparação das fichas, não revisão concluída. Não estimar
precisão do matching ou recall de recuperação sem rótulos de referência adequados.
Nem este piloto, nem as aceitações automáticas da v3, fornecem esse padrão-ouro.

Depois da revisão, escolher uma intervenção delimitada sobre falhas demonstradas.
Verificar se os candidatos recuperáveis existem e se as regras distinguem versões.
Só então estimar custo e preparar cruzamento ampliado/manual, com checkpoints,
regra congelada e validação separada. Não relaxar correspondência para atingir
meta de cobertura. Se construído um cadastro integral de vínculos aceitos,
amostragem posterior representa esse cadastro operacional sob o desenho adotado,
não automaticamente o catálogo Spotify ou músicas sem letras disponíveis.

Fundamento: Winkler (2006), [Overview of Record Linkage and Current Research Directions](https://www.census.gov/library/working-papers/2006/adrm/rrs2006-02.html),
e Statistics Canada, [amostragem probabilística](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm).
