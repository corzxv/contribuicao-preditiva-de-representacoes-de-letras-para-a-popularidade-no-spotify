# Embeddings multilingues

Modo all; concluído: True; novos vetores 27352, reutilizados 49699. Dimensão 384, tokens até 512.

Teste técnico, não validação semântica ou ganho preditivo. Textos longos são cobertos por janelas, sem truncamento silencioso; pooling por tokens novos não elimina toda influência do overlap. Nenhuma faixa é excluída por idioma. Estimativa de escala, quando disponível, é grosseira: seleção dirigida de extremos/idiomas, aquecimento e cache afetam o tempo; não prevê duração total. Nenhum modelo preditivo, PCA ou split é ajustado.
