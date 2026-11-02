# Auditoria do split — Base v0.1.1

## Regra

Split determinístico com `random_state=42`, alvo de 25%, sem usar popularidade, gênero, ano ou qualquer variável de desfecho para escolher grupos. `split_group_id` é o componente conectado entre `artist_group_id` e `composition_group_id`; portanto, nenhum artista ou composição pode atravessar as partições.

| split | linhas | % |
| --- | --- | --- |
| development_train | 83817 | 74.998658% |
| holdout_test | 27941 | 25.001342% |

- Fração real de teste: **25.001342%**.
- Grupos: `{"artist_group_id": 13901, "composition_group_id": 111444, "split_group_id": 13901}`.
- Sobreposição: `{"artist_group_id": 0, "composition_group_id": 0, "split_group_id": 0}`.
- SMD da popularidade: **0.008614**.

## Comparações

As comparações foram calculadas somente depois de o split estar fixado por grupos e servem para auditoria, não para refazer o holdout com base no desfecho.

Alertas de desequilíbrio relevante: ['nenhum pelos limiares operacionais'].

Disponibilidade dos descritores:

```json
{
  "development_train": {
    "any_descriptor_available_percent": 100.0,
    "all_descriptors_available_percent": 62.377560638056714,
    "structure_block_complete_percent": 62.377560638056714
  },
  "holdout_test": {
    "any_descriptor_available_percent": 100.0,
    "all_descriptors_available_percent": 60.69217279267028,
    "structure_block_complete_percent": 60.69217279267028
  }
}
```

O `holdout_test` fica lacrado para decisões de seleção, imputação, padronização, PCA e hiperparâmetros. A validação cruzada ocorrerá apenas dentro de `development_train`, respeitando grupos.
