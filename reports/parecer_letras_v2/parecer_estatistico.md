# Parecer estatístico — base completa disponível

**Conclusão: incompatível com os critérios observados.** Escopo: resultados_faixas_200k.parquet, hash registrado no resumo;
200,000 faixas, 77,535 aceitas. Catálogo de referência: 1,159,764.
A avaliação pequena de busca não aprova esta base; este parecer usa seus resultados completos.

**A. Sorteio:** hashes, IDs, alocação, estratos, probabilidades e pesos conferem com
o desenho congelado. Isso verifica os artefatos registrados, sem repetir o sorteio.

**B. Seleção por letras:** Há diferenças materiais apoiadas pelos intervalos simultâneos. A tabela compara médias e proporções com o catálogo fixo,
com e sem pesos. 83 de 104 critérios primários ponderados
não demonstraram equivalência; 102 estratos têm cobertura
nula e 348 têm menos de cinco aceitações. Falta de
equivalência não prova diferença; a conclusão de incompatibilidade exige intervalo
simultâneo fora da margem. Veja cada motivo/status e as distribuições nos CSVs.

**C. Tolerâncias:** ±1 ponto de popularidade; ±0,10 DP do catálogo para médias
contínuas/ano; min(1 pp,20% da proporção do catálogo) para categorias. Todas devem
ser atendidas conjuntamente. Limites fixados após conhecimento de resultados
anteriores: não é confirmação independente. Falhas/inconclusivos estão integralmente
em diagnostico_equivalencia.csv; primeiras comparações abaixo.

**D. Alcance:** os pesos estimam razões no domínio de aceitação sob este protocolo;
não corrigem disponibilidade seletiva de letras. Resultados permitem descrever o
subconjunto observado. Concordância nestas marginais não prova representatividade
global, equivalência multivariada, identificação correta da letra ou causalidade.

**E. Modelagem:** não se afirma suficiência preditiva pelo tamanho. Antes de avançar,
revisar correspondências propostas e regressões de matching, declarar o alcance
restrito ao domínio observado e planejar splits por artista/composição reconciliados
com o teste V0.6 exposto. Se a intenção for generalizar ao catálogo, as lacunas
listadas exigem avaliação específica de seleção e suporte; não se recomenda outra
busca integral automaticamente. Não recalibrar pesos para aprovar o diagnóstico.

TOST de Wald/Taylor a 5% (IC90%) por comparação; IC95% também informado.
Conclusão conjunta de equivalência por interseção de todos os testes primários,
sem escolher maioria. Para afirmar alguma diferença relevante na família, ICs
Bonferroni 95% simultâneos. Aproximação pode ser fraca em categorias raras: células
com <5 positivos, domínio válido <20 ou variância não estimável ficam inconclusivas.
Qualidade do matching e semelhança estatística são avaliações separadas.

| variable | category | difference | margin | conclusion |
| --- | --- | --- | --- | --- |
| popularity | all_finite | 5.3650 | 1.0000 | relevant_difference |
| energy | all_finite | 0.0553 | 0.0271 | relevant_difference |
| loudness | all_finite | 1.8614 | 0.5682 | relevant_difference |
| acousticness | all_finite | -0.0748 | 0.0355 | relevant_difference |
| instrumentalness | all_finite | -0.1460 | 0.0365 | relevant_difference |
| _s_genre | acoustic | 0.0089 | 0.0036 | relevant_difference |
| _s_genre | afrobeat | -0.0062 | 0.0021 | relevant_difference |
| _s_genre | alt-rock | 0.0083 | 0.0036 | relevant_difference |
| _s_genre | ambient | -0.0137 | 0.0037 | relevant_difference |
| _s_genre | black-metal | 0.0079 | 0.0038 | relevant_difference |
| _s_genre | blues | 0.0079 | 0.0034 | relevant_difference |
| _s_genre | breakbeat | -0.0082 | 0.0021 | relevant_difference |
| _s_genre | chicago-house | -0.0038 | 0.0009 | relevant_difference |
| _s_genre | classical | -0.0126 | 0.0031 | relevant_difference |
| _s_genre | club | -0.0071 | 0.0025 | relevant_difference |