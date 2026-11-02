# Revisão acadêmica no template fornecido — 02/11/2026

## Entrega

Nova entrada principal: `reports/monografia_template_200k_v2/main.tex`.
Pacote de upload: `reports/monografia_template_200k_v2.zip`.
PDF TeX: `output/pdf/monografia_template_200k_v2.pdf`.

34 páginas, cinco seções principais, dois apêndices científicos, dez tabelas,
cinco figuras e 27 referências originais. A versão de 57 páginas, seu ZIP/PDF
e os demais resultados continuam preservados. A redução resultou de reescrita
e consolidação, sem comprimir o texto principal em fonte menor.

Orientador: **Leandro Tavares Correia**. O pesquisador confirmou a correção de
grafia após a consulta ao SIGAA/Departamento de Estatística. O registro anterior
“Correa” é histórico e não foi alterado silenciosamente nos PDFs antigos.

## Mudanças de conteúdo e apresentação

1. Cinco seções, seguindo o template e o exemplo: Introdução; Referencial
   teórico; Dados e metodologia; Resultados e discussão; Considerações finais.
2. Retirados do PDF o inventário do repositório, hashes, histórico de universos
   e scripts, contagens de execução e lista administrativa para o orientador.
   As evidências continuam nos relatórios/documentação do projeto.
3. Narrativa reconstruída: catálogo bruto → descrição → LRCLIB → amostra
   probabilística → integração → 77.535 aceitas → comparação preditiva.
4. Spotify ampliado: distribuição de popularidade/zeros/cauda, 82 gêneros, year,
   créditos de artistas, versões heurísticas, qualidade e atributos acústicos.
   Duas figuras novas e uma tabela foram geradas somente de agregados concluídos.
5. LRCLIB: origem/dump, snapshot, volumes, 33.714.178 metadados percorridos,
   campos, representações e unidade. Sem confundir registros, letras distintas,
   índices e aceitas. Não se inventou distribuição global de idiomas/comprimentos
   do dump, que não consta dos agregados disponíveis.
6. Fórmulas e notação para inclusão/pesos, média e variância estratificadas,
   razão/linearização, graus de liberdade, equivalência, Ridge/padronização,
   MAE/RMSE/R², diferenças/ganho, ponderação, embeddings, seleção interna,
   contribuição da cauda, clipping e limites por componente.
7. As fórmulas foram confrontadas com a implementação. O diagnóstico de
   equivalência usa quantis t com graus de Satterthwaite; não foi descrito como
   se utilizasse z. A análise condicional de contrastes mantém sua aproximação
   normal própria. Nenhum resultado foi recalculado ou código científico alterado.
8. Descritores enumerados em linguagem acadêmica, com 21 definições; nomenclatura
   de engenharia retirada do apêndice. Mantida a transparência da variante E5.

## Consulta à BDM e bibliografia

A página geral indicada apresentou indisponibilidade no leitor web; a coleção
específica de Estatística e os PDFs públicos foram acessados, estes por HTTPS
com a conexão nativa do Windows. Não se considerou um resumo de busca como leitura
do PDF. Foram inspecionadas estrutura, passagens pertinentes e bibliografias:

| Exemplo consultado | Evidência e uso editorial | Fontes originais pertinentes |
| --- | --- | --- |
| Ana Clara, ZIP fornecido | Fonte TeX e PDF de 28 páginas; capa, fórmulas, métodos, tabelas/referências | Hyndman/Athanasopoulos; usou-se a 3ª edição, 2021, conferida, em vez da 2ª edição de 2018 citada no exemplo |
| Maria Luiza Barreto Escobar, 2024 | BDM 10483/41348, 49 páginas; descrição do objeto, amostragem e referências pp. 44–45 do PDF | Cochran (1977), 3ª edição; Lohr aparece em 2ª edição no exemplo |
| Matheus Tadeu Rainero Mendonça, 2023 | BDM 10483/36446, 57 páginas; estratificação, fórmulas e bibliografia p. 41 do PDF | Lohr (2022), 3ª edição, adotada; não se reproduziram indiscriminadamente dados editoriais de outros itens |
| Rodrigo Cavalcanti Loreto, 2022 | BDM 10483/34267, 70 páginas; tema musical, notação e referências p. 70 do PDF | Izbicki/Santos (2020), conferido no livro original e na página do autor; documentação Spotify |

Coleção: https://bdm.unb.br/handle/10483/37.
Itens: https://bdm.unb.br/handle/10483/41348,
https://bdm.unb.br/handle/10483/36446 e https://bdm.unb.br/handle/10483/34267.

O livro de Izbicki/Santos foi consultado no original (CIP, sumário e passagens
sobre predição/risco/seleção). Cochran e Lohr tiveram edição/metadados e escopo
conferidos nas editoras, além das fontes metodológicas já disponíveis. As
definições MAE/RMSE foram conferidas na seção 5.8 do livro de Hyndman/Athanasopoulos;
não se atribuiu a eles uma origem histórica não demonstrada dessas medidas.
Hastie/Tibshirani/Friedman e James et al. fundamentam aprendizado/Ridge/validação;
Cover/Thomas, entropia; Wellek, equivalência. Artigos originais e documentação
técnica complementam os livros. Nenhum TCC foi adicionado ao .bib.

As 27 chaves são citadas, sem entradas órfãs ou citações ausentes. O arquivo
`referencias_conferidas.csv` do pacote registra fonte, uso e origem da indicação.
Reaproveitar referências significa conferir e citar o original pertinente,
não copiar uma bibliografia inteira ou métodos que não foram aplicados.

## Verificação e preservação

Compilação nativa Tectonic/XeTeX/BibTeX e compilação no editor integrado concluídas.
Corrigida a ordem de carregamento hyperref/abntex2cite e o escopo do estilo
bibliográfico para evitar duplicação. Sem referências indefinidas, erros BibTeX
ou overfull/underfull. O aviso inputenc ignorado no XeTeX é esperado.

Todas as 34 páginas finais foram inspecionadas: 31 permaneceram pixel a pixel
iguais às páginas já revistas e três foram reinspecionadas após eliminar duas
páginas residuais nos apêndices. Equações do apêndice numeradas B.1–B.4.
Dez testes leves de normalização/diagnósticos passaram; lint/formato do script 29
verificados. Sem leitura de dados individuais, treinamento, LRCLIB ou geração
de embeddings. Nenhum commit/push.

O registro final de hashes, ZIP, fontes originais dos exemplos e integridade está
em `reports/verificacao_monografia_template_200k_v2.json`. A modelagem congelada
e os artefatos anteriores são verificados, sem atribuir novamente ao agente
execuções antigas do pesquisador.

## Próximos ajustes acadêmicos

Revisar com o orientador a narrativa, a extensão e a interpretação do ganho.
Confirmar, se houver documentação disponível, data da resposta, versão do CSV e
significado de year. Agradecimentos/dedicatória só devem ser escritos pelo autor
ou com seu conteúdo pessoal; não foram preenchidos com exemplos alheios. Regras
de defesa/depósito permanecem distintas da adaptação ao template fornecido.
Nenhuma nova rodada de modelos é necessária para ler e revisar esta versão.
