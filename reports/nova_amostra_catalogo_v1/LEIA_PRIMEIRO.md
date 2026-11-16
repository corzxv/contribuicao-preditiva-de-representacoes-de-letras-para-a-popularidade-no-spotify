# Nova amostra do catálogo — sorteio real concluído

**N=1.159.764; n=9.526**, por AAS sem reposição nos 82 gêneros, alocação
proporcional pelos maiores restos. Sorteio real executado pelo pesquisador e
conferido em 06/11/2026. Semente 20261106. Não repetir o sorteio.

Conclusão em resumo_sorteio.json; comparacao_metadados/categorias.csv contêm
os resultados observados. A maior diferença absoluta entre doze médias foi
0,01901 DP; por período, 0,4050 ponto percentual. Figuras:
comparacao_medias_dispersoes.png/svg e comparacao_periodos.png/svg.
Interpretação: reports/interpretacao_nova_amostra_catalogo_v1.md.

41 real concluído/conferido: 682 aceitas, 87 instrumentais, 8.757 pendentes.
Próximo comando manual: 42_buscar_letras_nova_amostra.py, com SSD em D:.
Guia docs/execucao_busca_nova_amostra_v1.md; execução real 42 ainda pendente.

Metas escolhidas para o estudo: margem aproximada individual de 1 ponto
percentual para proporção global a 95%, e margens conjuntas aproximadas de até
0,05 DP para as doze médias de metadados a 95% (Bonferroni). Incluem correção
de população finita. Não são garantias de igualdade de distribuições, precisão
preditiva, inferência por gênero raro ou quantidade final de letras.

Arquivos calculados somente de agregados da descrição 39:

- plano_amostral.json: critérios e selos.
- alocacao_generos.csv: 82 contagens, probabilidades e pesos; 5–179 por gênero.
- precisao_metadados.csv: margens para as doze médias, com unidades.
- cenarios_tamanho.csv: comparação de metas de 2, 1,5 e 1 ponto percentual.

O perfil de BPM foi reconciliado reinserindo os zeros conhecidos nos momentos;
nenhuma faixa foi excluída da população para reduzir o tamanho.

Protocolo: docs/plano_nova_amostra_catalogo_v1.md. Execução em um comando:
docs/execucao_nova_amostra_catalogo_v1.md. Código: scripts/40_preparar_nova_amostra.py.
Os 9.526 são os sorteados; disponibilidade e correção da vinculação de letras
continuam sendo questões posteriores. Não substituir perdas silenciosamente.

Arquivo acadêmico anterior: reports/preservacao_monografia_20261106/.
Todos os PDFs/fontes e resultados anteriores permanecem nos locais originais.
