# Descrição do catálogo completo — 1.159.764 faixas

População acessível do CSV Spotify, anterior à amostragem e à recuperação de letras.
Esta análise é a parte inicial de caracterização dos dados. Não redefine amostra,
população analítica ou resultados preditivos anteriores.

## Conteúdo para a redação

1. dicionario_variaveis.csv: todos os campos originais, definições e unidades.
2. qualidade_campos.csv: ausências, falhas numéricas e regras locais por variável.
3. resumo_numerico.csv e histogramas.csv: distribuição, quantis, dispersão,
   assimetria e zeros; escopos todos_finitos e regra_local explicitados.
4. frequencias_categoricas.csv e genero_periodo.csv: todos os gêneros, anos,
   períodos e categorias musicais. Figuras de barras mostram recortes identificados.
5. perfis_grupos.csv: médias, dispersões e quantis por gênero, ano e período.
   associacoes_grupos.csv: eta² descritivo, sem testes ou afirmações causais.
6. correlacoes.csv: Pearson e Spearman nos mesmos casos completos válidos,
   com denominador informado. densidades_relacoes.csv contém células agregadas.
7. pca_variancia.csv, pca_coeficientes.csv, pca_perfis_grupos.csv e resumo_pca.json:
   PCA exploratória dos atributos acústicos contínuos e duração, sem o alvo.
8. popularidade_log1p.csv: descrição de log(1+popularidade), preservando os zeros,
   sem transformação do alvo para ajuste de modelos.

## PCA

Casos completos: 1,158,565; fora somente desta análise:
1,199. Todas as faixas permanecem na descrição
do catálogo; não houve exclusão da população, imputação ou eliminação de outliers.
Variáveis: danceability, energy, loudness, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms. Duração em segundos. Padronização por
média e desvio com divisor n−1; autodecomposição da matriz de correlação.
São necessários 6 componentes para 80% e
8 para 95% da variância dos preditores.
Isso não é variância explicada da popularidade. Gênero/período apenas descrevem
os escores; não há agrupamento automático de músicas ou uso preditivo dos eixos.
O sinal é orientado pelo maior coeficiente absoluto positivo, sem mudar a PCA.
O mapa mostra amplitude completa e uma ampliação central; o resumo registra
quantas faixas ficam fora apenas da ampliação. Nenhum escore individual é exportado.

## Convenções e alcance

- Todas as linhas são descritas; nenhum peso amostral é necessário para esse catálogo.
- Quantis por interpolação linear; DP descritivo usa divisor n. Variância com
  divisor n−1 também é fornecida como insumo de planejamento.
- Regras de domínio vêm de configs/quality_rules.yaml, não de uma certificação
  externa. Valores finitos fora delas continuam no escopo todos_finitos.
- year é o ano da fonte, sem pressupor lançamento original; o escore de
  instrumentalidade não prova que uma faixa não tenha letra.
- Chaves musicais e assinatura de tempo são categorias. Gênero não é codificado
  como número para PCA. Não há normalidade assumida ou causalidade inferida.
- O catálogo acessível não é um censo de toda a plataforma Spotify.

## Referências

- Jolliffe (2002), Principal Component Analysis, 2ª ed., Springer.
  https://link.springer.com/book/10.1007/b98835
- Spotify, documentação de atributos acústicos:
  https://developer.spotify.com/documentation/web-api/reference/get-audio-features
- Fonte do catálogo:
  https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks

## Próxima etapa

Interpretar esta descrição; depois pesquisar e definir dimensionamento/alocação
de uma amostra menor com referência e critérios de precisão explícitos. A busca
de letras começa apenas depois dessa definição. Nenhum tamanho foi fixado aqui.
