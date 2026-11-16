# Nova etapa: execução manual inicial — 04/11/2026

Situação mais recente (05/11/D-026): 31 e 32 já concluídos; não repetir. Triagem
técnica 33 concluída; próximo comando é 34 smoke, no guia
execucao_classificacao_ordinal_200k_v1.md. Comandos abaixo são registro das etapas
anteriores. Revisão semântica humana permanece pendente.

Atualização de 05/11: 31 previsoes já concluído e conferido; não repetir.
Executar novamente somente 32. A correção v1.1 deriva uma coluna numérica de
popularidade, preservando o bruto textual, e usa pastas novas. A tentativa v1
interrompida fica intacta; não apagar owner.json para tentar reutilizá-la.

Os resultados Ridge/PDF anteriores permanecem. A autorização atual é para explorar
uma nova etapa com autonomia; não é execução de novos treinos pelo agente.

## O que está preparado e o que executar

31 agregados pode ser executado pelo agente: lê só tabelas públicas pequenas.
31 previsoes e 32 percorrem tabelas individuais completas e ficam para o pesquisador.
Não exigem internet, SSD LRCLIB ou instalação de novo pacote. Não treinam.
Executar um comando por vez; o segundo independe do resultado científico do primeiro.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\31_diagnosticar_niveis_popularidade.py" previsoes
```

Depois:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\32_preparar_piloto_vinculacao.py"
```

31 deve terminar [4/4] Concluído. Conferir
reports/niveis_popularidade_200k_v1/previsoes/resumo_niveis.json:
completed=true, observed_tracks=77535, components=21893; avaliar
operational_support_all_partitions. False é alerta do diagnóstico, não erro para
ser resolvido mudando cortes após olhar desempenho. Qualquer divergência de selo,
ID ou grupo interrompe em vez de excluir observações.

32 deve terminar [4/4] Piloto preparado; revisão semântica ainda pendente.
Conferir reports/piloto_vinculacao_200k_v1_1/resumo_piloto.json: completed=true,
human_review_completed=false, new_lrclib_queries=0. Preparação não aumenta o número
de letras aceitas. As fichas privadas não devem ser enviadas ao GitHub.

Em interrupção, repetir o mesmo comando. 31 reconstrói apenas tabelas derivadas
pequenas da mesma versão; 32 preserva ficha já exportada. Código/entrada/protocolo
diferente bloqueia reuso, sem apagar versões. Se 32 encontrar ficha existente e
resumo incompleto, interrompe para inspeção, preservando possíveis anotações.

## Continuidade

Analisar resumos/tabelas, verificar suporte das classes e evidências do piloto;
então preparar e testar a logística ordinal e sua execução manual. PCA será
alternativa dentro dos treinos, sem ajuste na base inteira. Cruzamento integral,
log1p, treino com custos e nova amostra não são disparados por estes comandos.
