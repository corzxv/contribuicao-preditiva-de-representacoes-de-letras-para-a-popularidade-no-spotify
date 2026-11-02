# Recuperação v3 — avaliação antes da escala (01/11/2026)

Regras congeladas antes desta avaliação, mas após conhecimento dos resultados v1/v2.
V1/v2, seus índices, amostra, estratos e pesos permanecem imutáveis. A v3 não
constrói índices nem varre o dump. Caches v1/v2 e metadados dos três índices
existentes são lidos somente para leitura; textos só são lidos após filtragem.

Três decisões separadas: recuperar candidatos; avaliar artista/título/colaboração,
versão e duração; escolher texto. Qualificadores contextuais vêm da v2. Um candidato
incompatível é excluído individualmente. Qualificador ausente não comprova estúdio:
versão explícita de um lado e ausente do outro não é aceite determinístico. Ambos
sem qualificador recebem indicação de versão não especificada, sem resolver
homônimos universais. Duração conhecida deve diferir no máximo dez segundos.

Texto simples utilizável tem prioridade. Sincronização não suportada gera aviso,
sem invalidar plain; sem plain exige extração LRC válida. Plain e synced válidos
com conteúdo diferente permanecem inconclusivos. Para comparar, NFC, caixa
uniforme, sinais tipográficos da v2 e espaços/quebras de linha uniformes; nenhuma
palavra/verso/repetição/marcação removida. Pontuação, apóstrofos, hífens e escrita
não latina permanecem. Textos originais, hashes e comparação ficam separados.
Vazios não contradizem texto; instrumental/texto e mesmo ID conflitante continuam
ambíguos. Representante por duração/ID só após comprovar equivalência textual.

Sequência: reavaliar cache; depois, se necessário, blocos de crédito de artista
nos índices v1/v2, com chaves estritas e alternativas conservadoras (acentos,
pontuação e participação explícita). Não dividir bandas por &, and, vírgula ou
ponto e vírgula. Dentro dos blocos, razão de similaridade de título ≥80 recupera
propostas, não probabilidades. Somente artista/título estritos do perfil contextual
e colaboração/versão/duração compatíveis podem ser aceitos automaticamente. Todas
as demais propostas exigem revisão; não há opção de ativar aceite aproximado.
Popularidade, gênero, peso e status anterior não entram em `decide`/`agreement`.

Paginação de 200 metadados por bloco, teto de 2.000 por chave/índice, limites de
texto v1 e prazo SQL. Limite vira incompletude operacional, nunca prova de ausência
ou unicidade. Não comparar todo o catálogo com todo o dump. Metadados fora dos
blocos/índices permanecem limitação: a v3 não estima um benefício que justifique
automaticamente outro índice. Qualquer índice futuro exigiria proposta de custo
e evidência desta avaliação, com decisão separada.

Avaliação: seed 20261101; AAS dentro de 600 não encontradas, 100 aceitas-controle e
300 ambíguas alocadas proporcionalmente por motivo com piso de uma por motivo e
maiores restos. Ordenar IDs antes do sorteio, registrar N, n, probabilidade n/N e
misturar ordem de execução. Créditos conhecidos não têm prioridade; isso não
garante equilíbrio de artistas, pois a unidade diagnóstica é faixa. Não alterar
a amostra científica. Orçamento padrão 600 s desde a preparação; checagens entre
consultas e progress handler SQL. Exportar relatório parcial depois do prazo;
latência bloqueante de I/O e tempo de exportação podem exceder o limite.

Checkpoint por consulta em workspace v3, comum à avaliação/aplicação para reuso
sob os mesmos selos. Consulta interrompida permanece pendente. Repetir comando
retoma; decisões concluídas não são repetidas. Aplicação exige avaliação concluída
e reavalia também aceitações/instrumentais antigas; toda perda de cobertura é
publicada. Aproximadas continuam apenas propostas mesmo após revisão de exemplos.
Revisão privada: até 100 pares, distribuídos pelos métodos, rótulos correto,
incorreto, inconclusivo. Seleção dirigida, sem estimativa de precisão antes da
rotulagem. Extrapolações de tempo por grupo são aproximadas; censura pelo prazo,
grupos não avaliados e custos fixos impedem previsão exata de escala.

Arquivos v3 ficam em `data/derived/private_sample_lyrics_200k_v3/`; agregados da
avaliação em `reports/avaliacao_letras_200k_v3/` e aplicação em
`reports/recuperacao_letras_200k_v3/`. Somente agregados públicos; letras/IDs,
pares de revisão e decisões individuais permanecem privados. O parecer estatístico
separado usa resultados completos, nunca aprova a base a partir dos mil casos.

Referências verificadas em 01/11/2026: [Fellegi e Sunter (1969)](https://doi.org/10.1080/01621459.1969.10501049)
fundamentam separar decisões de ligação/não ligação/revisão; o código não implementa
seu modelo probabilístico nem estima pesos de concordância. [Macrae (2012), Linking
Music Metadata](https://c4dm.eecs.qmul.ac.uk/research/theses/) contextualiza a dificuldade
de ligar metadados musicais; não reproduzimos seus algoritmos. [Lohr (2022)](https://www.sharonlohr.com/sampling-design-and-analysis-3e)
fundamenta desenho e domínios; [Lohr (2023)](https://hdsr.mitpress.mit.edu/pub/sqinvh4c/release/1)
motiva explicitar hipóteses sobre não resposta/seleção em vez de presumir correção
pelos pesos. Os thresholds e regras conservadoras são decisões operacionais locais.
