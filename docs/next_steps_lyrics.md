# Próxima etapa — obtenção de letras

Nenhuma letra foi coletada nesta execução. A próxima etapa deve ser separada, auditável e condicionada a direitos de uso.

## Cascata proposta

1. Reutilizar os matches LFM2b para descritores já disponíveis, sem presumir texto integral.
2. Procurar corpus estruturado e autorizado, com licença compatível e identificadores/proveniência documentados.
3. Avaliar APIs ou fontes estruturadas com termos, cotas e campos bem definidos.
4. Somente depois de auditoria jurídica/técnica de termos, `robots.txt`, licença e limites, avaliar Genius e Letras.mus.br.
5. Usar busca web apenas como fallback controlado, com revisão e cache de metadados, nunca como scraping massivo.

## Controles mínimos

- Não versionar letras nem respostas integrais de APIs no Git.
- Registrar URL, identificador, timestamp, licença/termos, método e hash quando legalmente cabível.
- Separar autorização para pesquisa, redistribuição e publicação de trechos.
- Evitar armazenar texto além do necessário; preferir features/embeddings quando a licença permitir derivação, documentando o modelo e a versão.
- Criar uma fila de revisão humana para ambiguidades; não propagar letra entre live, remix, remaster, instrumental ou versões incompatíveis.
- Manter opt-out/remoção e política de retenção.

Antes de implementar, deve haver uma decisão explícita sobre a fonte autorizada e a forma de armazenamento. Scraping de Google, Genius, Letras.mus.br ou outros sites permanece fora do escopo da Base v0.1.

