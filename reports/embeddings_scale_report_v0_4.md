# Embeddings escalados das letras — v0.4

## Pipeline congelado

- Modelo: `sentence-transformers/all-MiniLM-L6-v2`.
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- Dimensão: 384; dtype: float32; limite: 256 word pieces, sendo 254 de conteúdo; overlap: 32.
- Agregação: média ponderada pelos tokens novos de cada chunk e normalização L2 final.
- Sem tradução, fine-tuning, PCA ou uso de popularidade.

## Resultados agregados

- Embeddings de desenvolvimento: 7648 × 384.
- Embeddings de holdout: 2592 × 384.
- Vetores do piloto reutilizados por hash compatível: 213 composições.
- Novos hashes codificados: 10025.
- NaN: 0; infinito: 0.
- Maior desvio da norma L2: 0.00000006.
- Idiomas: `{"english": 10117, "non_english": 119, "uncertain": 4}`.
- Tokens: `{"maximum": 1723.0, "mean": 309.737109375, "median": 269.0, "minimum": 4.0, "n": 10240}`.
- Chunks: `{"maximum": 8.0, "mean": 1.75625, "median": 2.0, "minimum": 1.0, "n": 10240}`.

As matrizes e índices individuais permanecem privados e separados por split. O arquivo de holdout não contém `spotify_popularity` nem qualquer target.
