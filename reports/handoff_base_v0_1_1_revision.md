# Handoff da revisão incremental — Base v0.1.1

## Resultado

A revisão foi concluída sem alterar bases, pares aceitos, IDs ou split. Foram identificados **38 casos especiais**: 16 anos LFM implausíveis e 22 chaves de composição ausentes, com interseção **0**.

## Auditoria temporal válida

Ao tratar os 16 anos implausíveis como ausentes apenas para estatística, restaram **111742** diferenças válidas e **16** ausentes. A média passou a **1.891133**, a mediana permaneceu **0.000000**, o desvio-padrão amostral passou a **6.804583** e o máximo válido passou a **150** anos. Estatísticas brutas e válidas completas estão em `matching_temporal_audit_v0_1_1_revision.md`.

## Semântica

- `lfm_compression_ratio`: confirmada. O extrator oficial calcula `sys.getsizeof(UTF-8) / sys.getsizeof(zlib.compress(UTF-8))`; razão adimensional. A possível dependência residual do comprimento deverá ser avaliada somente no treino.
- `lfm_entropy`: não confirmada. A coluna foi preservada fisicamente apenas para auditoria e removida das listas autorizadas de preditoras.
- `year` e `genre`: descrições revisadas de modo conservador conforme o schema/data card da fonte Spotify; detalhes não documentados pela fonte não foram inferidos.

## Mudança na autorização de preditoras

Os descritores tradicionais autorizados passaram de **197 para 196** e o conjunto tradicional/combinado atual passou de **220 para 219**. O baseline permaneceu em **23**.

## Planilha de revisão

A nova aba `casos_especiais` contém a união deduplicada dos dois grupos e cinco campos humanos vazios. A aba `revisao_matches` preserva os 225 registros existentes. Nenhuma linha recebeu rótulo automático.

## Integridade

- Base v0.1 original: hash preservado.
- Base v0.1.1 e matching audit: hashes preservados.
- Split: hash preservado, mesmos IDs e mesma alocação 75%/25%.
- Pares aceitos: 111.758, sem alteração.
- Letras coletadas: não.
- Modelos treinados: não.

Os comandos e códigos de saída finais são registrados em `run_summary_v0_1_1_revision.json` após a verificação.
