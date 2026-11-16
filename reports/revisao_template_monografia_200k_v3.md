# Consolidação acadêmica — versão 3, 06/11/2026

Entrega autorizada pelo pesquisador em D-028: PDF de 45 páginas e pacote
Overleaf de 46 arquivos, com main.tex/XeLaTeX/BibTeX. As versões anteriores
continuam intactas. A nova entrada é reports/monografia_template_200k_v3/main.tex.

## Conteúdo consolidado

Objetivos incorporados à introdução. Mantida a história do catálogo Spotify,
LRCLIB, amostragem, integração e seleção textual. Regressão original, extensão
exploratória ordinal e sensibilidade posterior da decisão permanecem distintas.
Acrescentados fundamentos e fórmulas de PCA, logística cumulativa penalizada,
matriz de confusão, precisão/sensibilidade, AB/Macro-F1, log-loss/Brier e decisão.

Os resultados mostram o incremento textual modesto, a seleção de PCA em 3/20,
o limite inferior da grade em 20/20, os desvios de calibração e o compromisso
entre recuperar elevadas e aumentar falsos positivos. A comparação categórica
com Ridge usa os mesmos cortes e não compara MAE numericamente com acurácia.
Reconhecer nível ≥40 na cauda ≥80 não é detecção binária de hits.

O texto não declara independência dos cinco folds, significância integral ou
representatividade do catálogo. Os limites condicionais antigos não são
transferidos ao ordinal. A regra alternativa não substitui a principal nem
constitui validação aninhada de uma pipeline otimizada para o novo custo.

## Bibliografia e apresentação

32 fontes originais, todas citadas: 27 anteriores e cinco novas. Agresti (2010)
e McCullagh (1980) fundamentam o modelo ordinal; Jolliffe (2002) e Jolliffe/Cadima
(2016), PCA; Gneiting/Raftery (2007), perdas probabilísticas. Metadados conferidos
nas editoras/periódicos/autores. A nota de McCullagh distingue artigo 109–127 de
versão com discussão 109–142. Notas de Harrell foram consultadas como conferência
complementar da parametrização cumulativa. Nenhum TCC foi adicionado ao .bib.
Fontes e alcance de cada conferência constam de referencias_conferidas.csv.

Cinco seções, dois apêndices científicos, catorze tabelas, sete figuras e 34
equações numeradas. O script 38 constrói quatro tabelas e copia duas figuras
de agregados pequenos; não abre dados individuais/modelos. Foram removidas
repetições que geravam duas páginas residuais. Fonte e margens do template mantidas.

## Verificação

- Compilação Tectonic 0.17.0+20260731/XeTeX/BibTeX e editor integrado concluídas.
- ZIP extraído em pasta limpa, recompilado; mesmo texto nas 45 páginas.
- CRC, identidade dos arquivos empacotados, citações e referências conferidos.
- Zero referências indefinidas, erros BibTeX ou overfull/underfull no TeX.
- Todas as páginas verificadas visualmente. Das 45 finais, 34 coincidem
  pixel a pixel com páginas já revistas; onze alteradas foram reinspecionadas.
- Sete testes leves de diagnósticos/sensibilidade passaram em 4,06 s.
  Ruff e formato do script 38 aprovados.
- 54 arquivos anteriores e catorze fontes públicas/códigos ordinais conferidos
  contra hashes registrados; nenhum ajuste científico real ou consulta LRCLIB.

Os avisos de host sobre inputenc no XeTeX e configuração padrão de Fontconfig
não impediram resolver as fontes Latin Modern e renderizar as equações. O PDF
foi inspecionado; não há caracteres ausentes ou caixas pretas observadas.
Evidências e hashes em verificacao_monografia_template_200k_v3.json.

## Continuidade

Versão para revisão acadêmica com Leandro Tavares Correia, sem requisitos ou
datas institucionais inventados. Discussão seguinte: utilidade e custo dos erros,
clareza da narrativa e extensão. Permanecem documentadas as limitações de fonte,
matching, prefixo E5, chances proporcionais, grade, exposição e dependência.
Nenhuma dessas pendências dispara treino, coleta ou reconstrução automaticamente.
Sem commit/push nesta entrega; os novos PDF/ZIP permanecem locais sob a política
vigente de publicação.
