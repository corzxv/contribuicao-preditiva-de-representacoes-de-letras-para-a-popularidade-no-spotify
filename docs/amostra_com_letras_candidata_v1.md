# Amostra candidata de 9.526 faixas com letras

O sorteio de 9.526 faixas do catálogo permanece como base do diagnóstico de
cobertura. Ele tem 3.869 letras aceitas e 5.657 faixas sem letra aceita,
incluindo 416 indicações instrumentais da classificação local de origem.
Essas indicações são evidência da fonte e a faixa permanece no sorteio.
Completar exatamente os mesmos IDs dependeria da disponibilidade de letras
das gravações correspondentes e de uma fonte adicional.

## Candidata inteiramente vinculada

A etapa 52 formou um quadro de 80.722 faixas unindo 77.535 aceitas do histórico
e 3.869 do sorteio menor. As 682 faixas repetidas tinham metadados e hash de
letra iguais. A amostra candidata tem 9.526 IDs distintos. A verificação leu
os 9.526 textos selecionados das fontes seladas, confirmou conteúdo não vazio
e comparou o SHA-256 de cada vínculo. Os textos permanecem nas fontes de
origem e o Parquet da candidata traz o arquivo, a consulta e o hash de cada
letra. O script 52 reproduz o sorteio com semente 20261108.

As unidades foram sorteadas sem reposição dentro de gênero × banda de
popularidade. A banda 80–100 foi agrupada em um estrato, com cinco vagas.
O total original de cada banda foi mantido. Quando uma célula tinha capacidade
inferior à cota, a diferença foi redistribuída dentro da banda, preservando
probabilidade positiva para toda célula com capacidade. Os pesos valem para o
quadro observado de vínculos aceitos. [Seleção de uma amostra, Statistics Canada](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/sample-echantillon/5214900-eng.htm)

Os 82 gêneros estão presentes. Mesmo com uso integral da capacidade conhecida,
faltariam 207 vínculos para reproduzir todas as cotas de gênero. O maior déficit
é `sleep`, com cinco faixas no quadro para uma cota de 147. A média de
instrumentalidade é 0,134 na candidata e 0,252 no catálogo. A popularidade
média é 19,85 na candidata e 18,38 no catálogo, apesar dos mesmos totais por
banda. O dimensionamento original estimava a precisão descritiva do sorteio
do catálogo. A candidata atende ao tamanho solicitado sob outro quadro.

Entre as 9.526 faixas da candidata, 9.186 já estavam na coorte histórica de
modelagem. As comparações futuras precisam registrar essa exposição. A
candidata fica disponível para avaliação metodológica do domínio do TCC.

## Onde continuar a recuperação

A inspeção de metadados achou 43 consultas antigas com vínculo aceito e cache
local, fora do quadro atual e com os mesmos artista, título e duração da
faixa de referência. São 28 em `minimal-techno`, 14 em `guitar` e uma em
`chicago-house`. A próxima revisão pode conferir esses caches, as versões e
os textos antes de ampliar o quadro. Para `sleep`, `romance` e `detroit-techno`,
essa triagem histórica não encontrou vínculos adicionais. Na amostra inicial,
a mediana da instrumentalidade foi 0,864 em `sleep` e 0,878 em `detroit-techno`.
Esses escores descrevem o cadastro e a identificação de letra segue dependendo
da evidência da gravação.

Para o sorteio original, a alternativa externa identificada é testar uma
fonte licenciada, com acesso ao texto integral e chave da gravação. A
LyricFind oferece licenciamento de letras e dados. A cobertura das faixas
pendentes e o acesso para este projeto ainda precisam ser verificados.
[Produtos e licenciamento LyricFind](https://www.lyricfind.com/)
