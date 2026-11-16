# Contribuição preditiva de representações de letras para a popularidade no Spotify

Trabalho de Conclusão de Curso de **Felipe Macedo Cordeiro**, Bacharelado em Estatística da Universidade de Brasília. Orientador **Leandro Tavares Correia**.

- [Monografia em PDF](output/pdf/monografia_template_overleaf.pdf)
- [ZIP editável para o Overleaf](reports/monografia_template_overleaf.zip)
- [Fontes LaTeX e tabelas](reports/monografia_template_overleaf/main.tex)
- [Resultados da avaliação](reports/classificacao_9526_v1/interpretacao_resultados.md)

Para compilar, importe o ZIP como novo projeto no Overleaf e selecione `main.tex` e **XeLaTeX**. O BibTeX é executado automaticamente.

## Dados e resultado

O estudo avalia quanto as letras acrescentam à classificação do nível de popularidade observado quando já se conhecem os atributos acústicos e os metadados. O catálogo acessível tem **1.159.764 faixas**. Um primeiro sorteio probabilístico estratificado de **9.526 faixas** permitiu medir a recuperação de letras no LRCLIB, com **3.869 vínculos aceitos**. Uma segunda seleção, a partir de **80.943 vínculos consolidados**, reuniu as **9.526 faixas com letra** usadas na modelagem.

| Modelo | Informação adicional à do Baseline | Acurácia balanceada |
| --- | --- | ---: |
| Baseline | Atributos acústicos e metadados | 56,14% |
| Tradicional | 21 descritores lexicais e estruturais | 56,24% |
| Profundo | Embedding multilíngue de 384 dimensões | 55,91% |
| Combinado | Descritores e embedding | 55,96% |

A classe alta teve maior sensibilidade no modelo Profundo, de 31,07%, ante 26,25% no Baseline. As diferenças de desempenho balanceado foram pequenas na coorte avaliada. O [protocolo](docs/protocolo_classificacao_9526_v1.md) e os [agregados de classificação](reports/classificacao_9526_v1/metricas_externas.csv) documentam a validação e o alcance dos resultados.

## Reprodução

| Etapa | Entradas CLI | Resultados e documentação |
| --- | --- | --- |
| Descrição do catálogo e dimensionamento | `39` e `40` | [Diagnóstico descritivo](reports/interpretacao_descritiva_catalogo_completo_v1.md) e [plano amostral](docs/plano_nova_amostra_catalogo_v1.md) |
| Busca local, revisões e cobertura textual | `41` a `51` | [Cobertura do sorteio](reports/recuperacao_consolidada_nova_amostra_v1/resumo_cobertura.json) |
| Quadro com letras e seleção para modelagem | `52` a `56` | [Recuperação dirigida](docs/recuperacao_generos_deficitarios_v1.md) e [seleção final](reports/amostra_com_letras_candidata_v2/resumo_amostra_candidata.json) |
| Classificação ordinal | `57` | [Protocolo e execução](docs/protocolo_classificacao_9526_v1.md) |
| Incerteza condicional e figuras editoriais | `58` e `59` | [Contrastes pareados](reports/monografia_template_overleaf/material_complementar/contrastes_condicionais.csv) e [trajetória das amostras](reports/monografia_template_overleaf/material_complementar/trajetoria_amostras.json) |

O [guia de reprodução](docs/REPRODUCAO.md) explica dependências, dados de entrada e execução manual das etapas pesadas. O [dicionário](docs/data_dictionary.md), a [proveniência](docs/provenance.md) e o [registro de decisões](docs/decisions.md) documentam as variáveis e o desenho. A [classificação da etapa anterior](reports/interpretacao_classificacao_ordinal_200k_v1.md) é uma avaliação de outra coorte, usada no desenvolvimento e na composição do quadro atual.

Novas execuções estocásticas usam **semente 42**. A reprodução das etapas seladas usa as sementes das respectivas execuções. As fontes da monografia e as figuras necessárias à compilação acompanham o ZIP. Dados brutos, letras, previsões individuais, modelos, vetores, caches e credenciais ficam no ambiente local, conforme a [política de publicação](docs/PUBLICACAO_GITHUB.md).

## Verificações leves

O projeto usa Python 3.13. Após instalar as dependências do [guia de reprodução](docs/REPRODUCAO.md), execute:

```powershell
.\.venv\Scripts\python.exe scripts\30_auditar_publicacao_git.py
.\.venv\Scripts\python.exe -m pytest tests/test_git_publication.py tests/test_normalization.py
```

As verificações do GitHub Actions usam dados sintéticos. A licença MIT cobre o código do projeto. As condições das fontes valem para seus respectivos dados.
