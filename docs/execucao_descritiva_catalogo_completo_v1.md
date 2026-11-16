# Descrição inicial do catálogo completo — D-029

**Situação atual:** execução real concluída pelo pesquisador e conferida.
1.159.764 faixas, vinte campos, 82 gêneros, treze figuras. Interpretação em
reports/interpretacao_descritiva_catalogo_completo_v1.md; conferência em
reports/verificacao_descritiva_catalogo_20261106.json. Não repetir o comando
para avançar: próxima etapa é o dimensionamento da amostra menor.

Plano vigente, determinado pelo pesquisador em 06/11/2026:
descrição do catálogo → dimensionamento e nova amostragem menor → recuperação
das letras sorteadas → definição da modelagem posterior.
Esta descrição compõe a parte inicial do TCC; não é seu tema central.

## Comando utilizado

No PowerShell, de qualquer pasta:

    & "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\39_descrever_catalogo_completo.py"

Não há smoke, etapas de validação para o pesquisador ou comandos de treinamento.
O script lê o CSV original uma vez em memória, calcula os agregados e gera
as figuras. O hash inicial da fonte é conferido. Não usa rede ou SSD do LRCLIB.
O processamento integral é executado manualmente pelo pesquisador.

Entrada: data/raw/spotify/spotify_data.csv, 175.822.041 bytes na inspeção local.
Saída: reports/descritiva_catalogo_completo_v1/.
Execução real concluída e interpretada após o pesquisador enviar a saída final.
O agente conferiu os agregados e as figuras, sem repetir a leitura integral.

## Conteúdo

- LEIA_PRIMEIRO.md: índice de leitura, convenções e referências.
- dicionario_variaveis.csv e qualidade_campos.csv: todos os vinte campos originais.
- resumo_numerico.csv e histogramas.csv: média, mediana, quantis, dispersão,
  assimetria, curtose e zeros. Valores finitos brutos e válidos pela regra local
  ficam em escopos separados; o tamanho do catálogo permanece intacto.
- frequencias_categoricas.csv: todos os gêneros, anos, períodos, key, mode e
  time_signature. genero_periodo.csv apresenta as contagens cruzadas.
- perfis_grupos.csv: atributos numéricos por gênero, ano e período.
  associacoes_grupos.csv resume eta² descritivo, sem testes ou causalidade.
- correlacoes.csv: Pearson/Spearman nos mesmos casos completos; o denominador
  está em resumo_correlacoes.json.
- popularidade_log1p.csv: descrição de log(1+popularidade), mantendo os zeros.
  Não altera o alvo de qualquer modelo anterior.
- resumo_pca.json, pca_variancia.csv, pca_coeficientes.csv e pca_perfis_grupos.csv:
  estrutura multivariada dos atributos acústicos e duração.
- figuras/: treze figuras em PNG de 300 dpi e SVG.

## Escolhas simples e explícitas

A duração original permanece em milissegundos; a coluna temporária adicional
_desc_duration_s e os resumos correspondentes usam segundos, com unidade informada.
Variâncias com divisor n e n−1 são distinguidas. Quantis por interpolação linear.
Gêneros e categorias musicais permanecem como fornecidos.

PCA nas dez contínuas: danceability, energy, loudness, speechiness, acousticness,
instrumentalness, liveness, valence, tempo e duração. Cada variável é centrada e
dividida por seu DP com divisor n−1; a matriz de correlação é decomposta exatamente.
Ano e gênero contextualizam os perfis, e a popularidade é descrita separadamente.
Esses três campos não entram na construção dos eixos. Não há clusters automáticos.

Casos inválidos/ausentes são contados. Apenas para PCA e correlações usam-se
casos completos válidos, com denominadores e motivos informados. Não há imputação,
exclusão da população ou remoção de outliers. As hastes dos gráficos por gênero
representam P5–P95, com caixa P25–P75 e mediana. O mapa de PCA também apresenta
ampliação central; os pontos fora da ampliação continuam na PCA e na visão completa.

Fonte metodológica: Jolliffe, I. T. (2002), Principal Component Analysis, 2ª ed.,
Springer, https://link.springer.com/book/10.1007/b98835.
Definições acústicas: documentação oficial do Spotify,
https://developer.spotify.com/documentation/web-api/reference/get-audio-features.
Não houve escolha do método/tamanho da nova amostra nesta preparação: essa decisão
vem depois de interpretar a descrição, com livros/artigos pertinentes.

## Continuidade

Após a execução, interpretar o catálogo e suas relações para a parte inicial da
monografia. Em seguida pesquisar dimensionamento e alocação de uma amostra menor,
com confiança/precisão e critérios de composição documentados. Depois recuperar
as letras dessas faixas, aproveitando trabalho compatível anterior quando houver.
Não repetir modelagem 22/34, gerar embeddings ou abrir novo cruzamento integral.
Não substituir faixas difíceis silenciosamente; o procedimento de recuperação
será especificado na etapa própria.

Versões acadêmicas e resultados anteriores são preservados. Em reexecução idêntica
concluída, o script informa o caminho já produzido. Mudança de fonte/código exige
outra pasta de saída, sem apagar o relatório anterior.
