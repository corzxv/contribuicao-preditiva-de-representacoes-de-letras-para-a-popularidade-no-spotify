# Fechamento metodológico — execução leve concluída em 02/11/2026

Leitura principal: `../reports/parecer_fechamento_metodologico_200k_v1.md`.
Decisão/registro D-021; todos os resultados principais e PDF/ZIP 24 preservados.
Não há novo trabalho pesado para o pesquisador neste parecer.

## O que foi executado

1. Script 25: previsões existentes/perdas por componente, hashes do resumo 23,
   resíduos, clipping separado, limites auxiliares por fold/componente. Duas
   tabelas com no máximo 80 mil linhas/32 MiB cada; 0,264 s na lógica do diagnóstico.
   Não carrega modelos, encoder, letras ou matrizes. Não executa bootstrap/refit.
2. Script 26: selos e configurações; oito letras do primeiro lote, todos os 21
   descritores recalculados e vínculos por hash; projeção de 9,68 MiB comprimidos.
   Tokenizer real em 11 frases artificiais e testes de cobertura em 2.001 tokens
   sintéticos; não carrega pesos nem chama forward. Concluído em 20,461 s.
   O arquivo inteiro de descritores excedia o limite inicial: leitura integral
   foi bloqueada e substituída por projeção pequena, sem elevar o orçamento.
   Hash integral dos descritores permanece evidência anterior da etapa 21.
3. Encontrada diferença entre prefixo separado e concatenação oficial (token
   de espaço extra). Script 27 foi preparado **por essa evidência concreta**:
   somente quatro frases artificiais, oito forwards curtos até 64 tokens,
   CPU/duas threads, sem corpus/cache/exportação de vetores. 20,702 s incluindo
   carregamento; snapshot completo/hash dos pesos conferido. Similaridade não é
   teste de impacto preditivo. Nenhuma letra do corpus codificada nesta rodada.
4. `resumir_cauda_auxiliar.py`: caracterização adicional das 128 observações com
   y≥80, somente contagens agregadas e contribuição ao ganho. A primeira execução
   dessa lógica foi em Python pelo terminal; a CLI posterior reproduz o JSON e
   verifica igualdade sem sobrescrevê-lo.

O protocolo `protocolo_fechamento_metodologico_200k_v1.md` corresponde ao script
25 e seus limites estatísticos. Não editar esse protocolo selado para incorporar
o achado posterior da auditoria; detalhes 26/27 e limitações estão neste guia e
no parecer. “Sem encoder” descreve 25; o diagnóstico limitado posterior foi
especificamente motivado pelo desvio real.

## Reprodução deliberada — não precisa rodar agora

As saídas 25–27 já existem. Os scripts se recusam a substituí-las. Para repetir
25 em novo destino, opcionalmente:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\25_diagnosticar_fechamento_metodologico.py" --output "C:\Users\Concursos Felipe\Documents\UnB\TCC\reports\fechamento_metodologico_200k_reproducao"
```

26/27 são auditorias específicas da versão congelada; nova execução deliberada
deve definir outra saída numa cópia versionada. Não apagar evidência existente
para forçar reexecução. Nunca substituir esse trabalho pelos modos históricos all.

## Verificações e conclusão

17 testes: fechamento (4), encoder (8), descritores (4), pooling artificial (1).
Ruff check/format e git diff --check. Hashes/proveniência em resumos JSON e
`verificacao_fechamento.json`. Nenhum treino real, LRCLIB ou novo vetor do corpus.

Critério de encerramento atual: comparação exploratória documentada; incorporar
o desvio técnico do prefixo, a incerteza integral não estimada e as limitações de
suporte/seleção. Não alegar equivalência canônica do E5 ou significância da pipeline.
Alterar representação/população/desenho de inferência requer decisão específica,
nova versão e eventual execução pesada manual; não é continuação automática.
