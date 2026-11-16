# Contribuição das letras na classificação da popularidade

A avaliação reuniu previsões externas para 9.526 faixas com letra verificada.
Os mesmos 6.271 componentes e as mesmas divisões agrupadas de validação cruzada
5×3 foram usados nos quatro modelos. As classes observadas tinham 5.548 faixas
de popularidade baixa, 2.919 de média e 1.059 de alta.

| Modelo | Acurácia balanceada | Diferença vs. Baseline (p.p.) | Acurácia | Sensibilidade baixa | Sensibilidade média | Sensibilidade alta |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 56,14% | 0,00 | 71,37% | 90,19% | 51,97% | 26,25% |
| Tradicional | 56,24% | +0,11 | 71,12% | 89,80% | 51,46% | 27,48% |
| Profundo | 55,91% | −0,23 | 69,27% | 86,75% | 49,91% | 31,07% |
| Combinado | 55,96% | −0,18 | 69,40% | 86,77% | 50,43% | 30,69% |

O Tradicional teve a maior acurácia balanceada, com ganho observado de 0,11
ponto percentual. O Baseline teve a maior acurácia geral. O Profundo acertou
329 das 1.059 faixas de popularidade alta, frente a 278 no Baseline. O ganho
líquido de 51 acertos na classe alta veio junto de 191 acertos a menos na
classe baixa e 60 a menos na média. A precisão das previsões de popularidade
alta foi de 75,96% no Baseline e 69,56% no Profundo.

Na avaliação com os pesos da candidata, as diferenças de acurácia balanceada em
relação ao Baseline foram +0,13 ponto percentual para o Tradicional, −0,07 para
o Profundo e +0,02 para o Combinado. Os valores descrevem esta avaliação e as
diferenças são pontuais. A evidência observada sugere ganho global pequeno
dos descritores tradicionais e um ganho concentrado na classe alta quando se
usam embeddings. O alcance é a avaliação agrupada das faixas com letra vinculada.

A conferência reconciliou os hashes da amostra, das divisões e das previsões.
Foram verificadas 20 partes dos quatro blocos, cinco partes da referência
por frequência de classe, 240 ajustes internos e 482 vetores novos. As métricas
por classe, matrizes de confusão e resultados por divisão foram reproduzidos
das probabilidades externas. [Métricas](metricas_externas.csv) · [Matrizes](matrizes_confusao.csv)
