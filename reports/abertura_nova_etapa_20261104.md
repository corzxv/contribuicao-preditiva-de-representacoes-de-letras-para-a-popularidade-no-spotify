# Abertura da etapa exploratória de classificação — 04/11/2026

O pesquisador autorizou condução autônoma após discutir classificação, PCA,
transformação e amostragem com o orientador. Primeira regressão e material
acadêmico permanecem como referência. Não há novo treino real nesta preparação.

## Escolhas e fatos confirmados

Começar nas 77.535 aceitas atuais, com limites operacionais 20/40. A definição
sensível 40/60 é separada; não escolher limites por acurácia. Contagens calculadas
somente a partir de 2.009 linhas de agregados existentes:

| Nível principal | Pontuação | Catálogo | Amostra original | Aceitas |
| --- | --- | ---: | ---: | ---: |
| Baixo | 0–19 | 682.921 | 116.980 | 34.069 |
| Intermediário | 20–39 | 343.467 | 59.045 | 30.785 |
| Elevado operacional | 40–100 | 133.376 | 23.975 | 12.681 |
| Total | 0–100 | 1.159.764 | 200.000 | 77.535 |

Nas aceitas: 43,94%, 39,70% e 16,36%. As diferenças entre domínios continuam
visíveis; três classes não corrigem seleção por disponibilidade textual. O nome
elevado não é definição oficial de hit. A cauda ≥80 é diagnóstico distinto:
499 faixas no catálogo/amostra, 128 aceitas. Não reduzir para 10 mil sem desenho.

## Preparado, ainda não executado no corpus

- Script 31 previsoes: hash/alinhamento de previsões e folds, suporte por classe
  nas partições 5×3, matrizes e métricas categorizadas dos quatro Ridge e referências.
  Não é resultado de um classificador novo; não há probabilidades/IC ou refit.
- Script 32: piloto de até 240 consultas únicas por status e presença de ≥80,
  evidências dos caches por chave, sem dump/SSD/rede. Ficha omite popularidade e
  status anterior; respostas de revisão vazias. Não exporta corpo de letra nem
  reclassifica decisões. Metadados não são padrão-ouro semântico.

Caches locais v2/v1 existentes (aproximadamente 1,04/6,20 GB); abertura somente
leitura e EXPLAIN por chave conferidos, sem ler registros nem refazer hash desses
bancos. Não foi executada a leitura integral de resultados/folds/previsões pelo
agente. Footers e arquivos pequenos/selos foram inspecionados.

## Ordem seguinte

Executar os dois comandos do guia docs/execucao_nova_etapa_niveis_v1.md, um por
vez. Analisar suporte nas partições e fichas limitadas antes de preparar logística
ordinal regularizada. Acurácia balanceada primária, métricas por classe e erros
extremos; quatro blocos e mesmas observações. PCA das numéricas é alternativa
dentro do treino; log1p, custos, novo cruzamento integral e nova amostragem ficam
condicionados à necessidade demonstrada.

37 testes selecionados aprovados, incluindo 14 novos; lint de src/scripts/tests
e formatação dos seis arquivos Python novos aprovados. Verificação reproduzível
em verificacao_nova_etapa_20261104.json. Nenhum commit/push desta nova preparação.
Protocolos/estado/dicionário/proveniência atualizados; monografia v2 preservada.
