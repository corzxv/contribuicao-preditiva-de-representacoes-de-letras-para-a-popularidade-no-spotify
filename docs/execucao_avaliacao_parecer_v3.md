# Execução v3: avaliar primeiro, sem nova indexação

Preparação somente com testes sintéticos. Nenhuma execução real da avaliação,
recuperação ou parecer foi feita pelo assistente. V1/v2 permanecem intactas.

## 1. Execute primeiro somente a avaliação

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\15_avaliar_recuperacao_letras.py" evaluate --seconds 600
```

Seleciona 600 não encontradas, 300 ambíguas por motivo e 100 aceitas-controle,
seed 20261101, sem escolher artistas famosos. O limite abrange preparação e
processamento; ao atingir o prazo, gera relatório parcial. Exportação e I/O
bloqueante podem ultrapassar o limite. Não cria índices, não aceita fuzzy.
Para retomar, repita exatamente o comando: orçamento novo de 600 s por invocação,
reutilizando decisões já concluídas. Se houver erro técnico, corrija a causa/SSD
antes de repetir; não apagar estado. Sem loops automáticos de flexibilização.

Pasta pública:
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\avaliacao_letras_200k_v3\`.
Envie `resumo.json`, `relatorio.md`, `transicoes.csv`, `alocacao_diagnostica.csv`.
O resumo separa ganhos do classificador/busca ampliada, regressões, propostas e
tempos. Projeção de ganho por probabilidades diagnósticas só aparece se concluída,
restrita aos três grupos; não mede precisão nem promete o mesmo ganho real na escala.

Privados em `C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v3\`:
plano, resultados individuais, SQLite e `pares_revisao_privados.json` (até 100
pares, distribuídos por métodos). Inspecione localmente, registrando `review_label`
como `correto`, `incorreto` ou `inconclusivo`, e observações. Não publicar letras
ou enviar esse arquivo entre os relatórios agregados. Rótulos humanos ainda não
são consumidos automaticamente; não habilitam aceite aproximado. Pares com
rótulos ou observações preenchidos são preservados nas retomadas; os espaços
restantes podem ser atualizados com novas propostas, mantendo o teto de 100.

## 2. Diagnóstico inicial da base completa disponível (v2)

Este comando é independente da busca e não abre LRCLIB, índices ou SSD D:.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\16_parecer_estatistico_letras.py"
```

Usa as 200 mil linhas do resultado v2 e os agregados catalogados da auditoria/
sorteio. Saída: `C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\parecer_letras_v2\`.
Envie `parecer_estatistico.md`, `resumo.json`, `diagnostico_equivalencia.csv`,
`cobertura_por_estrato.csv`, `distribuicoes_quantis_qualidade.csv`,
`catalogo_amostra_referencia.csv`, `status_motivos.csv` e o protocolo copiado.
Se não houver aplicação v3, este é o parecer da base completa disponível.

## 3. Aplicação integral separada, somente depois de avaliar o benefício

Condições: avaliação concluída (`completed: true`), conferir controles/regressões,
inspecionar propostas, decidir se ganho/custo justificam a escala. O código exige
avaliação concluída; mantém somente aceite determinístico e registra todas as
transições, inclusive perdas de aceitações antigas. Não executa modelos.

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\15_avaliar_recuperacao_letras.py" apply --seconds 86400
```

Repetir para retomar. Usa o mesmo cache v3 validado, sem repetir casos avaliados
com as mesmas regras/entradas. Resultado privado `resultados_faixas_200k.parquet`
mantém uma linha por faixa e campos originais/pesos; letras na tabela privada,
com texto efetivo `accepted_text` separado dos originais. Índices existentes
são somente leitura. Relatórios em
`C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\recuperacao_letras_200k_v3\`:
resumo, relatório, transições, alocação diagnóstica e comparação de cobertura.

## 4. Atualizar o parecer após conclusão integral

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\16_parecer_estatistico_letras.py" --input "C:\Users\Concursos Felipe\Documents\UnB\TCC\data\derived\private_sample_lyrics_200k_v3\resultados_faixas_200k.parquet" --output "C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\parecer_letras_v3"
```

Mesmos produtos estatísticos, em pasta nova. Não substituir o parecer v2. Margens
e regras congeladas em `docs/protocolo_parecer_estatistico_letras.md`; matching em
`docs/protocolo_avaliacao_letras_v3.md`. Fonte modificada exige nova pasta/versão;
não editar selos para forçar retomada. A conformidade estatística não valida o
matching, nem demonstra suficiência preditiva.

Verificação da preparação: pytest nos testes v3 e regressões v1/v2/local; ruff
check e format nos dois módulos novos, dois scripts e teste v3. Somente fixtures.
