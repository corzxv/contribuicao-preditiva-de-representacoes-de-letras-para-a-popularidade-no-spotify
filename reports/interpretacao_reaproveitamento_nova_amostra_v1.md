# Reaproveitamento da nova amostra — 41 real conferido

9.526 consultas concluídas em 30,32 segundos, sem erros de cache e sem acessar
dump/rede. Todos os arquivos privados e agregados publicados no resumo foram
conferidos por hash; a amostra continua a mesma.

| Situação após cache | Faixas | Percentual da amostra |
|---|---:|---:|
| Letras aceitas reaproveitadas | 682 | 7,16% |
| Indicação instrumental anterior | 87 | 0,91% |
| Pendentes de busca | 8.757 | 91,93% |
| Metadados insuficientes / erro de cache | 0 | 0,00% |

**7,16% não é a cobertura final do LRCLIB.** Esta fase apenas procurou consultas
idênticas nos caches do estudo anterior. A amostra nova contém sobretudo
consultas ainda sem decisão reutilizável; nenhuma ausência no cache demonstra
que uma letra não existe. Não há motivo para reduzir/substituir a amostra ou
alterar critérios de aceitação a partir dessas contagens.

Próxima ação: 42, busca local no mesmo snapshot com as regras v2 congeladas.
O índice v2 existente está completo: 33.714.178 registros de metadados percorridos,
5.726.985 entradas indexadas e lista selada de 24.330 chaves de artista. Agente
conferiu somente schema, meta, plano de acesso e identidade do dump, sem consultar
faixas reais ou ler letras. Não repetiu varredura ou hash integral do SSD.

42 identifica os artistas das pendências fora do índice e cria um complemento
somente se necessário; processamento real permanece manual. Decisões de busca
controlada completa já comprovadas no cache podem ser reutilizadas para evitar
repetição. Resultados negativos permanecem restritos ao snapshot/chaves/regras.
As 682 aceitas/87 instrumentais são preservadas; todo o cadastro de sorteio e
pesos é mantido. Cobertura e seleção serão avaliadas após a etapa local completa.

Código 42 preparado/testado com dump sintético de nove registros, incluindo
retomada, complemento, preservação dos vínculos, versões conflitantes e texto
derivado de LRC. Guia: docs/execucao_busca_nova_amostra_v1.md. Nenhuma execução
integral real 42, treino, embedding, PDF ou publicação nesta preparação.
