# Histórico metodológico e mapa dos códigos

Este resumo foi reconciliado com os 18 commits anteriores, registros de decisões,
protocolos e relatórios concluídos. A análise atual não começa em um projeto novo
e não transforma resultados de universos distintos em uma única comparação.

| Período / fase | Evidência | Papel na trajetória |
| --- | --- | --- |
| Agosto/2026, Base v0.1/v0.1.1 | Commits iniciais; `reports/data_audit.md`, matching, validação e mapa LFM2b | Integração inicial Spotify–LFM2b, 111.758 pares; separação Spotify/Genius/Last.fm e splits agrupados |
| Setembro–outubro, pilotos de letras | Pilotos v0.1.x e respectivas configurações/relatórios | Regras de recuperação, ambiguidade, textos privados e diagnóstico de seleção |
| Outubro, embeddings e comparação inicial | v0.2/v0.3/v0.3.1 | Embeddings MiniLM e desenvolvimento exploratório; outro domínio |
| 10–14/10, v0.4–v0.6 | Protocolos/manifestos; últimos commits até `a37946a` | 7.648 desenvolvimento/2.592 teste; teste aberto em 14/10, exposição histórica preservada |
| Etapas posteriores v0.7–v0.9 | Relatórios de diagnósticos/revisão/ampliação e módulos correspondentes | Explorações no desenvolvimento e dependências reutilizadas; resultados separados da coorte recente |
| Recuperação local e coorte anterior | Scripts 01–10, guias e `cohort_*` | Infraestrutura LRCLIB e estudos intermediários; a coorte antiga de 58.633 não é o domínio final |
| 31/10, catálogo e sorteio | Scripts 11–12, auditoria e plano amostral | População acessível e amostra fixa de 200 mil, pesos e proteção da cauda |
| 31/10–01/11, letras e seleção | Scripts 13–17 | Recuperação final de 77.535 aceitas, diagnóstico e decisão pelo domínio observado |
| 01–02/11, representações/base/modelos | Scripts 19–23; D-015 a D-020 | Componentes, E5 operacional, quatro blocos Ridge, CV 5×3 e resultados congelados |
| 02/11, fechamento e escrita | Scripts 24–29; D-021 a D-023 | Auditorias, incerteza auxiliar e monografia no template, preservando resultados |
| Publicação do código | Script 30 e política de GitHub | Auditoria do índice e documentação para consulta/reprodução |

## Linha principal e dependências

Os scripts 11–29 são as entradas recentes. As importações conectam essas etapas a
normalização, persistência, lógica de letras e fitters já implementados. A análise
das dependências encontrou módulos históricos efetivamente importados pelo código
atual; seus nomes não foram mudados nem removidos para aparentar uma implementação
inteiramente nova. Os caminhos também participam de selos de integridade.

`observed_regression.py` é o regressor principal Ridge. Ele reutiliza helpers de
`cohort_regression.py`, que compartilha infraestrutura com a revisão histórica.
`manual_lyrics.py`, `local_lyrics.py`, `lyrics_*`, normalização e persistência
fornecem controles de texto/checkpoint. Isso não incorpora silenciosamente
resultados, alvos ou embeddings antigos ao domínio de 77.535.

`local_demo.py` e `local_demo_delivery.py` contêm helpers usados por diagnósticos
históricos e testes. A interface Streamlit, seus ajustes e prévias pessoais
ficaram somente no arquivo local. A existência desses helpers não define a
interface como parte da comparação Ridge recente.

## O que foi retirado da versão atual do Git

Oito arquivos rastreados deixaram de integrar a versão atual: três resumos com
prévias individuais, um relatório com exemplos de IDs, dois handoffs redundantes,
um resumo de execução sintética e o roteiro inicial de próxima coleta, superado
pelas decisões posteriores. Os arquivos locais foram mantidos e os commits
anteriores não foram reescritos. Conteúdo individual já presente em commits antigos
não é eliminado retroativamente por retirar o arquivo da versão atual.

Planilhas/prévias, dump, matrizes, modelos, vetores, caches, arquivos temporários,
ZIPs de outros autores e configurações pessoais não entraram na publicação.
Agregados e fontes editoriais usados na monografia permanecem versionados.

## Idioma e integridade

Novos commits, comentários e documentação são em português. Nomes de APIs,
pacotes, colunas e funções existentes continuam estáveis. Os códigos científicos
selados, inclusive comentários/docstrings históricos em outro idioma, são
preservados byte a byte: traduzi-los alteraria as assinaturas e a identidade da
implementação avaliada. O histórico de commits em inglês foi mantido, sem rebase
ou force push. Explicações atuais em português acompanham os módulos no guia.
