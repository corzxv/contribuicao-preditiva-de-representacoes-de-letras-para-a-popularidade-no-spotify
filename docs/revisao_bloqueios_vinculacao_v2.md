# Correção dirigida da vinculação — D-033

## O que a auditoria encontrou

42 real concluído: 1.425 aceitas, 3.574 ambíguas, 4.164 sem candidato pelas
chaves controladas, uma sem texto e 362 indicações instrumentais. Sem erro
técnico ou consulta pendente. Resultados anteriores preservados.

O pesquisador questionou a baixa recuperação. A auditoria leve dos motivos
encontrou dois bloqueios inadequados do classificador v2 reutilizado:

| Motivo | Consultas | Diagnóstico |
|---|---:|---|
| plain_synced_conflict | 2.139 | Rejeição por divergência entre texto simples e extração LRC |
| positive_version_conflict | 1.176 | Presença de outra versão vetava a consulta inteira |

Das 1.176 por versão, **1.023 já tinham candidato plenamente compatível** por
artista, título, participações, qualificadores e duração. Os 153 sem candidato
compatível continuam sem justificativa para aceitar e ficam fora da revisão.

Foram examinadas dez consultas do primeiro motivo, em ordem determinística de
query_id, com acesso pontual ao dump por ID. Nas dez, os textos coincidiram
após uniformizar whitespace e aplicar a tipografia já existente, preservando
palavras, ordem, pontuação e capitalização. Nenhum corpo de letra foi exposto.
Não é amostra probabilística para estimar a prevalência do problema: não
extrapolar 10/10 às 2.139. A correção verifica a condição em cada candidato.

Os testes anteriores reproduziam o comportamento antigo; não demonstravam sua
adequação para a nova busca. Esta auditoria revelou falsas rejeições. O agente
reconheceu a falha ao reutilizar os filtros e mantém esta alteração rastreável,
sem reescrever o código/avaliações congelados.

## Duas mudanças precisas

1. Texto simples e extração sincronizada só são considerados equivalentes
   quando coincidirem exatamente após substituir sequências de whitespace por
   um espaço e aplicar a normalização tipográfica já usada. Não remover palavras,
   reordenar versos, deduplicar refrões, ignorar capitalização, apagar acentos
   ou aplicar similaridade aproximada. O texto simples original continua sendo
   o texto aceito; plain/synced originais permanecem preservados separadamente.
2. Quando há candidato totalmente compatível, versões/artistas/créditos/durações
   incompatíveis não vetam esse candidato. Elas já seriam inelegíveis pelo
   próprio critério de metadados. Não aceitar outra versão no lugar da pedida.
   Sem candidato compatível, permanece a rejeição anterior. Conflito de ID,
   conteúdos substantivamente diferentes e limite de enumeração continuam
   barrados. A tolerância de duração e os qualificadores não mudaram.

A visão usada na classificação retira uma representação sincronizada redundante
somente após essa igualdade ter sido comprovada; o original sincronizado volta
ao produto privado da letra selecionada. Não se altera o texto principal para
forçar equivalência entre candidatos distintos. A equivalência entre candidatos
continua sujeita às regras v2, sem adoção do fingerprint flexível diagnóstico.

## Execução manual

**Conecte o SSD em D:** e execute somente:

```powershell
& "C:\Users\Concursos Felipe\Documents\UnB\TCC\.venv\Scripts\python.exe" "C:\Users\Concursos Felipe\Documents\UnB\TCC\scripts\43_revisar_bloqueios_vinculacao.py"
```

Reavalia **3.162 consultas** (2.139 + 1.023) por acesso aos índices existentes,
sem reconstruí-los ou varrer novamente os 33 milhões de registros. Não repetir
42. Pode interromper e retomar pelo mesmo comando. `--status` lê progresso;
`--retry-errors` retoma erros técnicos, com limite de três tentativas.

Os resultados 42 ficam intactos. A revisão preserva as 1.425 aceitas, as 362
instrumentais, todos os sorteados e pesos. Não revisa automaticamente os 4.164
sem candidato, as ambiguidades de outras causas ou as 153 versões sem candidato
compatível. Esses casos exigem diagnóstico separado. Não há promessa de quantas
letras serão recuperadas pelas duas correções.

Saídas públicas: reports/revisao_matching_nova_amostra_v2, com resumo JSON,
status_revisao.csv, cobertura_revisao.csv e transicoes_status.csv. Saídas privadas:
data/derived/private_nova_amostra_matching_v2, com checkpoint, todas as faixas,
letras aceitas (originais e texto efetivo) e pendências. Nada disso foi executado
no conjunto real pelo agente; quatro testes sintéticos foram aprovados.

## Significado de instrumental e sem candidato

As 362 instrumentais correspondem à indicação instrumental do LRCLIB e ausência
de texto nos candidatos compatíveis pelas regras. Foram 87 herdadas de 41 e
275 novas em 42. Não são determinadas pela variável instrumentalness do Spotify,
nem são confirmação humana de que a gravação realmente não tem voz/letra.
Podem existir erros de cadastro/vínculo. A indicação permanece como evidência
observada e não autoriza substituir a faixa no sorteio.

Os 4.164 not_found são consultas sem candidato nas chaves de artista/título
controladas. Diferenças de cadastro/normalização e lacunas reais são explicações
a investigar; a contagem não estabelece ausência universal de letras no LRCLIB.
Nenhuma nova busca ampla ou alteração de população foi feita nesta auditoria.
