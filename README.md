# TCC — popularidade musical e representações de letras

Código e materiais de reprodução do TCC de **Felipe Macedo Cordeiro**, Bacharelado
em Estatística da Universidade de Brasília. Orientador: **Leandro Tavares Correia**.

O estudo avalia a contribuição preditiva incremental de letras para estimar a
popularidade Spotify observada, em conjunto com atributos acústicos e metadados.
A análise principal está encerrada e congelada; a monografia permanece em revisão.

## Monografia e resultados atuais

- [PDF do relatório no template](output/pdf/monografia_template_200k_v2.pdf).
- [Projeto LaTeX](reports/monografia_template_200k_v2/main.tex) e
  [ZIP para Overleaf](reports/monografia_template_200k_v2.zip).
- [Resultados e interpretação](reports/interpretacao_modelagem_200k_v1.md).
- [Parecer de fechamento](reports/parecer_fechamento_metodologico_200k_v1.md).

A versão no template tem 34 páginas, cinco seções principais, dez tabelas,
cinco figuras e 27 referências originais. No Overleaf, importar o ZIP, usar
`main.tex` e selecionar XeLaTeX; as referências são processadas por BibTeX.

O percurso principal foi: catálogo acessível de 1.159.764 faixas → amostra
probabilística estratificada de 200.000 → recuperação local no LRCLIB → domínio
observado de 77.535 faixas com letras aceitas. Os quatro conjuntos de variáveis
foram avaliados com Ridge nos mesmos componentes e folds agrupados aninhados 5×3.

| Configuração | MAE externo | RMSE externo |
| --- | ---: | ---: |
| Baseline | 8,3525 | 10,8255 |
| Tradicional | 8,2957 | 10,7538 |
| Profundo | 8,1285 | 10,5540 |
| Combinado | 8,1151 | 10,5381 |

O ganho conjunto de MAE foi de 2,84%. São resultados do domínio observado,
sem causalidade ou generalização automática ao catálogo. A variante E5 efetivamente
utilizada, a seleção de letras, a exposição histórica e os limites condicionais
são descritos na monografia e no parecer. Pesos amostrais são preservados; a
modelagem principal atribui peso igual a cada faixa.

## Por onde começar

1. [Guia de reprodução](docs/REPRODUCAO.md): ambiente, entradas, etapas e execução manual.
2. [Histórico metodológico](docs/HISTORICO_METODOLOGICO.md): trajetória e dependências.
3. [Dicionário de dados](docs/data_dictionary.md) e [decisões](docs/decisions.md).
4. [Política de publicação](docs/PUBLICACAO_GITHUB.md): conteúdo versionado e preservação.

## Organização dos códigos

| Etapa | Entrada de execução | Papel |
| --- | --- | --- |
| Preparação local do LRCLIB | scripts 05–08 | Dump, índices e controles de busca |
| Catálogo e amostra | scripts 11–12 | Auditoria e sorteio de 200 mil faixas |
| Letras e cobertura | scripts 13–17 | Busca, recuperação, diagnóstico e prontidão |
| Representações e grupos | scripts 19–20 | 21 descritores e embeddings E5 de 384 dimensões |
| Base e validação | script 21 | Base comum e componentes/folds 5×3 |
| Comparação Ridge | script 22 | Quatro configurações, checkpoints e previsões externas |
| Diagnósticos | scripts 23 e 25–27 | Métricas, incerteza condicional e auditorias |
| Escrita e figuras | scripts 24, 28–29 | Agregados e materiais da monografia |
| Publicação do repositório | script 30 | Seleção de arquivos e auditoria do índice Git |

A lógica está em `src/tcc_music_popularity/`; os scripts são entradas CLI.
Códigos históricos utilizados no desenvolvimento ou importados pela linha atual
continuam identificados no histórico. Mantêm-se os caminhos dos arquivos selados
para não romper imports, checkpoints e proveniência.

## Ambiente e verificações

O ambiente científico registrado usa Python 3.13. Instalação completa, quando
necessária, é manual:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-cientificos.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

`requirements-lock.txt` registra o ambiente básico; `requirements-cientificos.txt`
acrescenta as versões observadas de modelagem e embeddings. O guia distingue a
reprodução científica da compilação do documento, que usa TeX.

```powershell
.\.venv\Scripts\python.exe -m pytest --ignore=tests/test_local_demo_ui.py
.\.venv\Scripts\python.exe scripts\30_auditar_publicacao_git.py
```

Os testes usam fixtures pequenas; não reproduzem o treinamento integral. A
verificação automática no GitHub usa somente a auditoria de publicação e testes
leves de publicação/normalização, sem baixar encoder, letras ou bases reais.

## Dados e preservação

As fontes são [Spotify no Kaggle](https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks),
[LRCLIB](https://lrclib.net/docs) e, na trajetória histórica,
[LFM2b Lyrics Descriptor Analyses](https://zenodo.org/records/10938615).
Letras, bases individuais, dump SQLite, modelos, embeddings, credenciais e caches
permanecem fora do Git. O repositório contém código, testes, configurações de
exemplo, protocolos, agregados e materiais acadêmicos. A licença MIT se aplica
ao código do projeto; não substitui as condições das fontes e dos textos musicais.

Novos commits, comentários e documentação do projeto são escritos em português.
Os commits anteriores e os bytes dos códigos científicos selados são preservados.
Atributos Git impedem conversão automática de quebras de linha, necessária à
conservação dos hashes de proveniência. Não há comando automático que reinicie
buscas, geração de representações ou treinamento.
