# Reprodução do TCC

## Instalação

O projeto foi executado com Python 3.13 e PowerShell. Na raiz do repositório, instale as dependências para rodar a análise.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-cientificos.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

## Dados

- **Spotify** — [catálogo da pesquisa no Kaggle](https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks). O CSV de entrada fica em `data/raw/spotify/spotify_data.csv`.
- **LRCLIB** — dump de 12/10/2026. O [guia do dump e do SSD](dump_lrclib_ssd.md) explica a preparação local.

Para reproduzir etapas que reaproveitam vínculos, índices ou embeddings, prepare as entradas locais descritas nos protocolos. O [mapa de artefatos](MAPA_ARTEFATOS.md) identifica as dependências, incluindo as da coorte histórica usada na seleção final.

## Etapas

| Scripts | Etapa | Guia |
| --- | --- | --- |
| 39–40 | Descrição do catálogo e sorteio | [Descrição](execucao_descritiva_catalogo_completo_v1.md) e [amostragem](execucao_nova_amostra_catalogo_v1.md) |
| 41–51 | Recuperação de letras e diagnóstico de cobertura | [Reaproveitamento](execucao_reaproveitamento_nova_amostra_v1.md), [busca local](execucao_busca_nova_amostra_v1.md) e [cobertura final](../reports/recuperacao_consolidada_nova_amostra_v1/resumo_cobertura.json) |
| 52–56 | Seleção das 9.526 faixas com letra | [Desenho da seleção](amostra_com_letras_candidata_v1.md) e [quadro ampliado](recuperacao_generos_deficitarios_v1.md) |
| 57 | Classificação ordinal | [Protocolo e comando](protocolo_classificacao_9526_v1.md) |
| 58–59 | Contrastes, tabelas e figuras da monografia | [Diagnóstico das previsões](../scripts/58_diagnosticar_previsoes_monografia_final.py) e [agregados descritivos](../scripts/59_consolidar_descritivas_monografia.py) |

Os [scripts anteriores](HISTORICO_METODOLOGICO.md) documentam a preparação dos dados e as análises da coorte de 200 mil faixas.

## Monografia

Importe o [ZIP](../reports/monografia_template_overleaf.zip) no Overleaf, escolha `main.tex` e selecione **XeLaTeX**. A bibliografia é processada por BibTeX. As [fontes](../reports/monografia_template_overleaf/) incluem as figuras e tabelas usadas na compilação.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_normalization.py tests/test_catalog_description.py tests/test_ordinal_classifier.py
```
