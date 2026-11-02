# Contexto para continuidade do TCC — LRCLIB e resultados recentes

Atualizado em 31/10/2026. Resumo das etapas recentes, principalmente de 27 a 29/10/2026, e das decisões posteriores à leitura dos resultados. Não é o histórico completo do projeto.

## 1. Objetivo e ambiente

- TCC de Estatística da UnB, de Felipe Macedo Cordeiro.
- Objetivo: avaliar a contribuição preditiva incremental de descritores de letras para estimar a **popularidade Spotify observada na base**, além de atributos acústicos e metadados. Não estimar efeitos causais nem prometer previsão de sucesso comercial futuro.
- Repositório: `C:\Users\Concursos Felipe\Documents\UnB\TCC`.
- Ambiente: Windows/PowerShell, Python do projeto em `.venv\Scripts\python.exe`.
- SSD externo: `D:`, com o banco LRCLIB em `D:\TCC_LRCLIB`.
- Fluxo adotado: o assistente prepara código e instruções; o usuário executa os trabalhos reais no terminal. Dados, letras, caches, vetores e modelos ficam privados.

## 2. Fontes e ponto de partida

| Fonte utilizada | Papel no trabalho |
|---|---|
| Base com dados do Spotify | Popularidade observada, atributos acústicos e metadados |
| Material LFM2b utilizado no projeto | Descritores tradicionais de letras, identificadores e metadados para integração |
| LRCLIB | Textos de letras e metadados para localizar candidatos compatíveis |

A integração Spotify–LFM2b já existia antes das etapas aqui descritas. O universo de consultas de letras registrava **111.758 faixas, 111.422 composições operacionais e 111.736 consultas**; 22 faixas eram inelegíveis na preparação. Essas unidades não são intercambiáveis: uma chave operacional não é um identificador universal de composição.

A fonte exata da base Spotify, sua construção, a versão/derivado do LFM2b e as perdas do cruzamento serão revisitadas. Este resumo não presume que a fonte Spotify seja Kaggle nem inventa os tamanhos das bases originais.

## 3. Download do LRCLIB e busca local — concluídos

**Foram baixados textos e metadados, não arquivos de áudio.** A coleta anterior pela API enfrentava erros HTTP 503 e interrupções de proteção. Para acelerar as consultas, foi preparado um dump local do LRCLIB, preservando o trabalho anterior.

- URL registrada: `https://db-dumps.lrclib.net/lrclib-db-dump-20261012T090639Z.sqlite3.gz`.
- Snapshot: 12/10/2026.
- Compactado: **47.837.763.733 bytes** (aproximadamente 47,84 GB decimais).
- SQLite extraído: **261.755.867.136 bytes** (aproximadamente 261,76 GB decimais).
- Banco: `D:\TCC_LRCLIB\lrclib-db-dump-20261012T090639Z.sqlite3`.
- Checkpoint: `D:\TCC_LRCLIB\dump_progress.json`.
- Estado registrado: `ready`; download e extração completos; `gzip_crc_verified = true`; `sqlite_quick_check = ok`.
- Foi calculado SHA-256 local. Não havia SHA-256 independente publicado para comparação; a verificação não equivale a uma assinatura do publicador.

Foi construído um índice auxiliar de busca: o status apresentado registrou **33.714.178 registros percorridos e 12.757.266 indexados**. Esses números pertencem ao dump/índice, não à amostra do TCC.

As consultas locais reaproveitaram resultados existentes, mantiveram ambiguidades e aplicaram as regras implementadas de compatibilidade e aceitação. A fila local teve **95.250 trabalhos concluídos**; o último lote processou 95.200 em aproximadamente 72,8 minutos, sem erros técnicos.

### Resultado consolidado das consultas

| Resultado | Quantidade |
|---|---:|
| Aceitas | 78.323 |
| Ambíguas | 27.531 |
| Não encontradas | 5.045 |
| Instrumentais | 837 |
| Erros técnicos restantes | 0 |
| Não consultadas | 0 |
| Total de consultas | 111.736 |

Aceitas: 55.158 `accepted_exact_equivalent` e 23.165 `accepted_exact_unique`. Ambíguas: 26.477 por letras distintas, 259 por busca local incompleta, 794 por conflito de metadados e 1 por busca truncada. Aceitação automática não significa validação humana de cada correspondência.

## 4. Auditoria das letras — concluída

Saída: `data\derived\private_local_lyrics_audit\20261028T221245_413067Z`.

- 78.323 faixas aceitas auditadas: **58.705 no desenvolvimento e 19.618 no holdout**.
- 78.280 textos únicos, tanto pelo hash estrito quanto pelo normalizado.
- Nenhum hash de texto estrito ou normalizado compartilhado entre desenvolvimento e holdout.
- Nenhum grupo de artista ou composição compartilhado entre esses splits segundo os identificadores auditados.
- Zero erros de integridade, vínculos órfãos ou metadados de grupo ausentes.
- Manifesto, atribuições originais de split e arquivos de entrada preservados.

Escopo: integridade e sobreposição exata de textos. **Não comprovou que todas as letras sejam em inglês, nem realizou revisão humana dos matches ou validação semântica.**

## 5. Coorte e método estatístico executado

Workspace: `data\derived\private_statistical_cohort_v1`.

- Das 58.705 faixas aceitas no desenvolvimento, selecionou-se um representante por composição operacional, sem usar o alvo nessa escolha.
- Foram colapsadas 72 versões excedentes, resultando em **58.633 observações**.
- Havia 8.883 grupos de artista e 8.880 componentes de agrupamento. Componentes conectam registros relacionados para evitar vazamento entre treino e validação; não são gêneros nem classes de popularidade.
- Foram preservadas as atribuições originais de desenvolvimento/holdout. Os alvos do holdout **não foram carregados nesta rodada**.
- Comparação nas mesmas observações: **Baseline com 23 atributos** versus **Tradicional com os mesmos 23 + 196 descritores LFM2b**.
- Resposta: `spotify_popularity`. Identificadores, artista/título, matching, status de coleta e indicadores externos de popularidade não entraram como preditores.

### Ajuste e avaliação

- Validação cruzada agrupada: cinco folds externos no desenvolvimento; seleção por MAE em três folds internos, dentro de cada treinamento externo.
- Cada observação recebeu uma previsão externa ao respectivo treino (OOF). Os cinco conjuntos de validação tinham 11.617, 12.078, 11.674, 11.463 e 11.801 observações.
- Famílias: regressão linear por mínimos quadrados (OLS), Ridge, Elastic Net e regressão aditiva com splines e penalização Ridge.
- Referências simples: previsão pela média e pela mediana do treinamento.
- Imputação numérica por mediana, padronização e codificação categórica ajustadas dentro do treino. Nos candidatos tradicionais regularizados, compararam-se identidade e `asinh` para os descritores LFM2b.
- Modelo aditivo: splines cúbicas em 11 atributos contínuos do Baseline, sem interações; demais atributos tratados linearmente ou como categorias.
- Sem PCA, clipping, calibração, exclusão por erro alto, novos embeddings ou substituição dos modelos do demonstrador nesta rodada.
- Foram salvos **50 modelos externos de folds**. Não houve ajuste de um novo modelo final usando todo o desenvolvimento.

## 6. Resultados apresentados no documento

### Distribuição da resposta nas 58.633 observações

| Popularidade | n |
|---|---:|
| 0–9 | 5.694 |
| 10–19 | 14.822 |
| 20–29 | 16.747 |
| 30–39 | 12.138 |
| 40–49 | 5.799 |
| 50–59 | 2.512 |
| 60–69 | 772 |
| 70–79 | 138 |
| 80–89 | 11 |
| 90–100 | 0 |

São **9.232 observações com popularidade de pelo menos 40 (15,7%)**. Os 11 casos referem-se somente à faixa 80–89 dessa coorte de desenvolvimento. Não foi executada uma amostragem com cotas iguais por popularidade, embora isso estivesse previsto na proposta inicial.

Foram encontrados 233 pares de preditores com correlação de Spearman absoluta de pelo menos 0,8, usando pares completos. Isso registra redundância; não constitui, por si só, uma análise aprofundada das variáveis.

### Métricas OOF agregadas

Valores arredondados; P95 é o percentil 95 do erro absoluto. Todos os modelos abaixo foram avaliados nas mesmas 58.633 observações.

| Modelo | Bloco | MAE | RMSE | R² | P95 | Erros absolutos >20 |
|---|---|---:|---:|---:|---:|---:|
| Média do treino | Referência | 10,7488 | 13,4383 | ≈0 | 25,9820 | 7.662 |
| Mediana do treino | Referência | 10,7003 | 13,4760 | −0,0056 | 26,0000 | 6.948 |
| OLS | Baseline | 7,0536 | 9,1360 | 0,5378 | 17,7829 | 2.008 |
| OLS | Tradicional | 6,9854 | 9,0549 | 0,5460 | 17,6043 | 1.928 |
| Ridge | Baseline | 7,0524 | 9,1340 | 0,5380 | 17,7809 | 2.008 |
| Ridge | Tradicional | 6,9712 | 9,0269 | 0,5488 | 17,5938 | 1.918 |
| Elastic Net | Baseline | 7,4490 | 9,6340 | 0,4860 | 18,9713 | 2.459 |
| Elastic Net | Tradicional | 7,3577 | 9,5095 | 0,4992 | 18,7591 | 2.368 |
| Aditivo Ridge | Baseline | 6,9546 | 8,9924 | 0,5522 | 17,6078 | 1.945 |
| Aditivo Ridge | Tradicional | 6,8906 | 8,9016 | 0,5612 | 17,4403 | 1.882 |

Na seleção interna, a família aditiva foi escolhida nos cinco folds de ambos os blocos. Dentro dessa família, acrescentar os descritores reduziu MAE em **0,0639 ponto (aproximadamente 0,92%)**, RMSE em 0,0908 e P95 em 0,1675; aumentou R² em 0,0090 e reduziu em 63 a quantidade de erros acima de 20.

MAE, RMSE e P95 melhoraram nos cinco folds; a quantidade de erros acima de 20 melhorou em quatro. Na faixa 80–89, o MAE foi 33,23 no Baseline e 31,98 no Tradicional, com apenas 11 casos. O ganho incremental observado foi pequeno e a precisão na cauda superior foi limitada.

Também foram produzidos diagnósticos de resíduos, métricas por faixa/ano/gênero e comparações pareadas com 1.000 reamostragens por componente. Os intervalos são condicionais às previsões OOF, sem incorporar toda a incerteza de treino e seleção.

### Verificação da execução

`verification.json`: estado `verified`, 50 modelos salvos, diferença máxima entre previsões reproduzidas e salvas **0,0**, tolerâncias `atol=1e-8` e `rtol=1e-10`, entradas preservadas e `holdout_targets_loaded=false`.

Os resultados são exploratórios e específicos desta coorte. Não devem ser comparados diretamente com métricas de versões anteriores calculadas em outras observações. O holdout de uma etapa anterior (V0.6) já havia sido avaliado: esta rodada não constitui nova confirmação independente.

## 7. O que o projeto Overleaf contém

- ZIP: `reports\overleaf_resultados_coorte_aceita_v1.zip`.
- Fontes: `reports\overleaf_resultados_coorte_aceita_v1\`.
- Entrada: `main.tex`, compilador pdfLaTeX.
- Texto parcial de TCC: **metodologia, resultados e discussão**, começando na seção 3; não é a monografia completa.
- **Seis tabelas e duas figuras**: distribuição da popularidade e diagnósticos de resíduos do Tradicional aditivo.
- Explica formação da coorte, folds, atributos, regressões, métricas, os 11 casos de alta popularidade e limitações.
- Figuras copiadas dos resultados existentes e tabelas montadas dos agregados salvos; não houve novo treinamento para produzir o documento.
- Inclui bibliografia, README, proveniência e registro de verificação.
- Formatação reconstruída a partir de `C:\Users\Concursos Felipe\Documents\UnB\Proposta TCC\TCC1_Proposta_Felipe_Cordeiro.pdf`; não foi recebida uma classe institucional TeX original.
- Compilação local e integridade do ZIP verificadas. A entrega foi o projeto LaTeX para produzir o PDF no Overleaf; não foi exportado um PDF final nessa entrega.

## 8. Inventário prático disponível

Caminhos relativos abaixo partem do repositório informado na seção 1.

| Item | Local |
|---|---|
| Base integrada original, preservada | `data\processed\modeling_base_lfm_v0_1.parquet` |
| Dump e checkpoint no SSD | `D:\TCC_LRCLIB\` |
| Estado e caches da busca local | `data\derived\private_local_lyrics_v1\` (`state.sqlite`, `lrclib_cache_local`, `local_progress.json`) |
| Auditoria, índice de textos e proveniência | `data\derived\private_local_lyrics_audit\20261028T221245_413067Z\` |
| Coorte, folds e dicionário | `data\derived\private_statistical_cohort_v1\` (`development.parquet`, `accepted_links.parquet`, `folds.json`, `dictionary.csv`) |
| Modelos e previsões privados | Mesmo workspace: `models\`, `oof.parquet` |
| Resultados e diagnósticos | Mesmo workspace: `metrics.csv`, `paired_comparisons.csv`, `selected_parameters.csv`, `results.md`, `description\`, `diagnostics\`, `verification.json` |
| Protocolo e instruções da rodada | `docs\protocolo_coorte_aceita_v1.md`, `docs\execucao_estatistica_coorte_aceita.md` |
| Manuscrito parcial | `reports\overleaf_resultados_coorte_aceita_v1.zip` |

Scripts existentes relevantes:

- `01_preparar_universo_letras.py`: preparação offline e reconciliação do histórico.
- `02_coletar_letras.py` / `04_coletar_persistente.py`: coleta via API e supervisão.
- `03_gerar_embeddings.py`: implementação anterior de embeddings; não comprova processamento da nova coorte.
- `05_preparar_dump_lrclib.py`: download, extração e verificação do dump.
- `06_buscar_letras_local.py`: índice e busca local.
- `07_continuar_apos_indice.py`: encadeamento após conclusão do índice.
- `08_auditar_letras_local.py`: auditoria de integridade e sobreposição.
- `09_descrever_coorte_letras.py`: preparação e descrição da coorte aceita.
- `10_modelar_baseline_tradicional.py`: benchmark, regressões agrupadas e verificação.

Todos ficam em `scripts\`. A listagem é um inventário, não uma instrução para reexecutá-los.

## 9. Pendências e decisão atual

- No último estado consolidado desta coleta, `embedding_queries_completed=0` e `unique_vectors=0`. Existem trabalhos de embeddings de coortes anteriores, mas **não há conclusão registrada da geração para as 78.323 faixas atuais**.
- Um novo encoder foi discutido, mas não deve ser apresentado como escolhido ou executado nesta rodada. Os resultados acima não usam embeddings.
- Após ler o documento, o autor decidiu **priorizar a compreensão das fontes e do cruzamento**, antes de novos modelos ou embeddings.
- Próximo escopo acordado: inventariar Spotify e LFM2b; justificar suas funções; explicar o join e as perdas; verificar duplicidades/versões; descrever popularidade, anos, gêneros, artistas e ausências antes/depois da integração.
- Reavaliar se a disponibilidade de letras LRCLIB deve restringir Baseline/Tradicional, já que os descritores tradicionais vêm do LFM2b. Para comparar blocos, manter as mesmas observações na comparação pertinente.
- A concentração em baixa popularidade limita a análise da cauda, mas não prova isoladamente erro amostral. Balanceamento, população de interesse e cobertura precisam ser justificados.
- Diretriz do autor: **básico bem feito e bem justificado, sem multiplicar pipelines**. Preservar os resultados exploratórios existentes; não reconstruir tudo nem executar novos trabalhos sem alinhar o próximo passo.

Este arquivo reúne somente contexto e resultados agregados. Foi conferido por leitura dos checkpoints, relatórios e fontes locais; sua criação não executou coleta, embeddings, treinamento, alteração de dados, commit ou push.
