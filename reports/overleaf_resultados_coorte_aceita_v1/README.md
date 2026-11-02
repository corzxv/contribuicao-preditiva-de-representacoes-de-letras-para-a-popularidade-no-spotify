# Metodologia e resultados da coorte aceita

Projeto parcial para escrita gradual do TCC de Felipe Macedo Cordeiro, Departamento
de Estatística da Universidade de Brasília. Não contém letras, bases, previsões
individuais ou modelos. Somente texto, tabelas agregadas e figuras já existentes.

## Abrir no Overleaf

1. Crie um projeto por upload do ZIP entregue.
2. Selecione `main.tex` como documento principal.
3. Use o compilador **pdfLaTeX**, UTF-8 e uma versão recente do TeX Live.
4. Recompile; referências cruzadas podem precisar de duas passagens.

As referências estão em `references/referencias.tex` e não precisam de BibTeX ou Biber.
Não é necessário instalar Python, acessar os dados do projeto ou executar treinamento.

## Formatação e escopo

A aparência foi reconstruída a partir de `TCC1_Proposta_Felipe_Cordeiro.pdf`, autorizado
pelo autor: fonte latina serifada, texto justificado, títulos numerados, recuo de
parágrafo, espaçamento de uma linha e meia e cabeçalho com seção e página. Sem o
arquivo TeX original, não se afirma identidade exata ou conformidade com uma classe
institucional oficial. Não foi inventado um template da UnB.

O documento começa na seção 3 para facilitar sua inserção após introdução e objetivos.
É uma parte autônoma de metodologia, resultados e discussão; não é a monografia inteira.
Não repete capa, agradecimentos, cronograma ou conclusões sobre embeddings.

O conteúdo científico descreve a execução atual, não os procedimentos apenas previstos
na proposta inicial: Python em vez de R; base integrada Spotify–LFM2b e letras LRCLIB;
sem amostra equilibrada por faixas de popularidade; sem comprovação de restrição de
todas as letras ao inglês. Não apresenta previsão de sucesso comercial futuro.

## Arquivos para editar aos poucos

- `sections/metodologia.tex`: coorte, variáveis, preparação, regressões e avaliação.
- `sections/resultados.tex`: distribuição, explicação dos 11 casos, comparação e resíduos.
- `sections/discussao.tex`: interpretação, limites e contribuição já alcançada.
- `tables/`: seis tabelas montadas a partir de resultados salvos.
- `images/`: duas figuras originais, copiadas sem alteração.
- `references/referencias.tex`: referências metodológicas utilizadas neste trecho.
- `PROVENIENCIA.json`: identificação e hashes das fontes dos valores e figuras.

Para integrar ao TCC completo, copie essas pastas e os pacotes necessários do preâmbulo
de `main.tex`, e use `\input{sections/metodologia}`, `\input{sections/resultados}` e
`\input{sections/discussao}`. Remova `\setcounter{section}{2}` se a numeração já vier
das seções anteriores. Se o projeto maior usar capítulos, adapte apenas a hierarquia
dos títulos. Consolide a bibliografia para não criar duas listas de referências.

## Próxima sequência de escrita e análise

1. Ler e revisar esta parte, sobretudo a mudança da amostragem em relação à proposta.
2. Ajustar introdução e objetivos para o escopo efetivamente executado, sem reescrever
   ainda toda a monografia. Alinhar as mudanças de desenho com a orientação.
3. Revisar a seção de dados: proveniência, semântica de ano/gênero, aceitação de letras
   e limitações de versões. Não alegar representatividade do catálogo inteiro.
4. Preparar, em etapa separada, benchmark e execução manual do encoder congelado para
   embeddings; preservar representantes, linhas e folds desta rodada.
5. Somente depois, comparar Profundo/Combinado com as referências atuais na mesma
   amostra e escrever a nova seção de resultados. Nenhum ganho é presumido.

Não é necessário repetir os treinamentos para ler ou compilar este documento.
Resultados exploratórios não substituem a avaliação V0.6 nem o demonstrador congelado.
