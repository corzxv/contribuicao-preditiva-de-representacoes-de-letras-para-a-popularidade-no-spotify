# Nova amostra do catálogo — D-030, 06/11/2026

## Escolha adotada

Sortear **9.526 faixas** do cadastro acessível de **1.159.764 faixas**, por
amostragem aleatória simples sem reposição, independentemente em cada um dos
**82 gêneros**. A alocação é proporcional ao tamanho do gênero, com arredondamento
pelos maiores restos. O menor estrato recebe cinco faixas; o maior, 179.
Semente fixa: 20261106. Não alterar o sorteio para aproximar estatísticas observadas.

O pesquisador autorizou condução autônoma dessa etapa em D-029. Os resultados
dos 200 mil, 77.535 aceitos, regressão e classificação permanecem históricos e
intactos. Este desenho não muda seus pesos, divisões ou conclusões.

## Critérios de tamanho

Não existe tamanho determinado apenas por N. Adotaram-se duas metas de
planejamento, escolhidas para este estudo antes do novo sorteio:

1. Margem de aproximadamente **1 ponto percentual**, com confiança **individual
   de 95%**, para uma proporção global binária, usando o limite conservador de
   variância de uma variável 0/1. Exige resposta completa e aproximação normal.
2. Margens de até **0,05 desvio-padrão populacional** para as doze médias
   numéricas descritas, com confiança conjunta aproximada de 95% via Bonferroni.
   Os desvios e variâncias dentro dos gêneros vêm do catálogo já descrito.

As margens são escolhas substantivas de planejamento, não recomendações
numéricas universais de Cochran ou da Statistics Canada. Não significam erro
relativo de 1%, nem que cada música, gênero ou previsão terá esse erro. A família
das doze médias e uma proporção isolada não formam juntas uma garantia simultânea
de 95%. Não se dimensionou a precisão de um modelo preditivo futuro.

Com as duas metas mantidas, os cenários resultam em:

| Margem máxima para proporção global | Tamanho | Maior margem das médias, em DP |
|---|---:|---:|
| 2 pontos percentuais | 3.195 | 0,0500 |
| 1,5 ponto percentual | 4.254 | 0,0433 |
| **1 ponto percentual — adotado** | **9.526** | **0,0289** |

A meta de proporção determina o cenário escolhido; a meta de médias também é
satisfeita. O limite calculado para a proporção é 0,999974 ponto percentual.
É o primeiro inteiro que atende às restrições no algoritmo de alocação adotado,
não um ótimo global entre todos os desenhos possíveis.

## Cálculo reproduzível

Para gênero h, sejam N_h o tamanho populacional, n_h a alocação e W_h=N_h/N.
Calcula-se inicialmente n_h=floor(n N_h/N) e distribuem-se as vagas restantes
em ordem decrescente dos restos inteiros, com empate pela ordem alfabética do
gênero. As contagens, probabilidades e pesos estão em alocacao_generos.csv.

A média estratificada e sua variância exata sob o desenho são:

\[
\widehat{\bar Y}_{st}=\sum_{h=1}^{82} W_h\bar y_h,
\qquad
V(\widehat{\bar Y}_{st})=
\sum_{h=1}^{82} W_h^2\left(\frac1{n_h}-\frac1{N_h}\right) S_h^2,
\]

com S_h² calculada com divisor N_h−1. A variância do perfil agregado, cujo
divisor é N_h, é convertida antes do cálculo. Não se usa uma fórmula de AAS
como se a estratificação/arredondamento fossem inexistentes.

Para a proporção binária, como S_h²≤N_h/[4(N_h−1)], usa-se:

\[
E_p(n)=z_{0,975}\sqrt{\sum_h W_h^2
\left(\frac1{n_h}-\frac1{N_h}\right)\frac{N_h}{4(N_h-1)}}.
\]

Para cada uma das doze médias, a margem de planejamento é
z_{1−0,05/(2×12)}√V(Ȳ_st), comparada com 0,05 S_j. Bonferroni usa a soma dos
limites de probabilidade de erro e dispensa supor independência entre médias;
a aproximação normal de cada intervalo continua necessária. A busca percorre
tamanhos inteiros, exige n_h≥2 e verifica ambas as metas em cada alocação.
Maiores restos podem retirar uma vaga de algum estrato quando n aumenta;
por isso não se usa busca binária supondo monotonicidade irrestrita.

Margens de planejamento para algumas médias, já com o ajuste para as doze:
popularidade 0,356 ponto; BPM 0,832; duração 4,117 segundos; energia 0,00581;
dançabilidade 0,00411. Todas as doze estão em precisao_metadados.csv.

## Por que estratificar assim

A descritiva mostrou diferenças expressivas entre gêneros: eta² de 45,99% para
energia e 51,76% para acousticness, mas apenas 8,50% para BPM. A estratificação
preserva a composição de gêneros e a análise das variâncias verifica a precisão
das médias de **todos** os metadados numéricos, incluindo BPM, ano, popularidade
e duração. Não se exige que todos os metadados tenham a mesma distribuição.

Escolheu-se proporcionalidade pela simplicidade, conservação da composição e
pesos próximos entre faixas. Uma alocação de Neyman otimiza uma variável
específica; uma otimização multivariada pode estudar compromissos, mas não é
necessária para atender às metas atuais com menos de dez mil faixas. Não se
afirma que o desenho proporcional seja o mais eficiente possível.

PCA permanece descritiva. Dois eixos retêm apenas 44,35% da variação das dez
contínuas: não bastam como critério exclusivo de composição amostral. Gênero é
o rótulo fornecido pelo cadastro, sem presumir taxonomia musical universal.

## Seleção e comparação

Cada gênero tem um gerador PCG64 com SeedSequence([20261106, índice alfabético
do gênero]). Sorteiam-se posições sem reposição no cadastro de bytes selados.
Assim, π_i=n_h/N_h e d_i=N_h/n_h. O arredondamento torna o desenho
aproximadamente autoponderado; usar os pesos exatos nas descrições.
Totais ponderados dos gêneros reproduzem N_h por construção. Essa identidade
não é uma evidência independente de representatividade.

O script 40 `sortear` preserva os vinte campos originais como lidos do CSV e
acrescenta apenas colunas `_nova_*`. Não elimina os 1.199 BPM zero nem troca
faixas com metadados atípicos. Os perfis por gênero usam BPM positivo: seus
momentos completos foram reconstruídos reinserindo os zeros documentados e
reconciliados com média/variância global antes do dimensionamento.

Após o único sorteio, exporta comparação de médias ponderadas/não ponderadas,
dispersões e quantis, além de gênero, ano, período, tonalidade, modo e compasso.
Dispersões/quantis amostrais dessa tabela são explicitamente não ponderados;
as médias e proporções principais usam os pesos do desenho. Não realiza teste
de hipótese de igualdade com o próprio cadastro nem exclui observações para
melhorar uma figura. Eventuais diferenças serão interpretadas como resultado
do sorteio e do desenho, sem ressorteio oportunista.

## Letras e alcance das conclusões

**9.526 é o número sorteado, não o número garantido de letras.** A nova amostra
completa admite estimadores probabilísticos para o cadastro finito acessível,
conforme seu desenho; não para o Spotify inteiro ou outros momentos no tempo.
Não é necessário independência musical entre faixas para a validade da
variância de desenho das médias, que trata os valores finitos como fixos.

Reduzir n não aumenta a chance de uma faixa ter letra disponível. A recuperação
anterior encontrou cerca de 38,7% com letras aceitas, com cobertura desigual.
Se essa taxa se repetisse, a ordem de grandeza seria 3,7 mil letras, sem que isso
constitua previsão validada para a nova coleta. Não se promete atingir 9.526
letras, ampliar artificialmente o sorteio ou substituir silenciosamente perdas.

O próximo trabalho de recuperação deverá começar reutilizando vínculos e
evidências compatíveis dos caches locais. Depois, somente para as selecionadas
ainda pendentes, definir a busca local e eventual complementação. Manter todos
os sorteados no cadastro: letra aceita, instrumental confirmado e não localizada
são situações distintas. Auditar cobertura por gênero e metadados.

A aceitação das letras pode desfazer o equilíbrio probabilístico: tamanho e
pesos originais não corrigem automaticamente essa seleção. Inferência sobre
conteúdo textual do catálogo exige tratamento e hipóteses adicionais. A etapa
atual não resolve essa limitação nem reaproveita conclusões de generalização
do estudo anterior. Só depois da recuperação será definido o domínio/modelo.

Gêneros raros recebem poucas faixas e a cauda ≥80 tem apenas 499 casos no
cadastro: um desenho quase proporcional desse tamanho espera cerca de quatro
dessas faixas, antes de perdas. Logo, este plano privilegia descrição global,
não estudos precisos de hits extremos ou de cada gênero isoladamente. Não
garante precisão para correlações, quantis ou todas as distribuições conjuntas.

## Referências verificadas

- COCHRAN, W. G. **Sampling Techniques**. 3. ed. New York: Wiley, 1977.
  Capítulos 3–5: proporções, dimensionamento e estratificação. Edição/ISBN
  9780471162407 confirmados no [catálogo da editora](https://www.wiley-vch.de/de/fachgebiete/mathematik-und-statistik/sampling-techniques-978-0-471-16240-7).
- STATISTICS CANADA. **Survey Methods and Practices**. Ottawa, 2010. Catálogo
  12-587-X; original impresso de 2003. Seção 6.2.6, capítulo 7 e capítulo 8,
  especialmente 8.2.2.1 (alocação proporcional) e 8.2.3 (múltiplas variáveis e
  considerações práticas). [Texto oficial](https://www150.statcan.gc.ca/pub/12-587-x/12-587-x2003001-eng.pdf).

As fórmulas foram implementadas diretamente; não se declara implementação do
algoritmo de Bethel. As metas numéricas são decisões desta pesquisa.
