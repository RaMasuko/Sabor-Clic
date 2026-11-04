# Registro de verificação — 03/11/2026

## Código e integração

- **103 testes Python aprovados**: autenticação, perfis/propriedade, CSRF, conta inativa, expiração/revogação/replay, entrada SQL, JSON/tipos/preços/quantidades inválidos, CRUD com versão, checkout atômico, preço do servidor, snapshot histórico, idempotência, estoque concorrente, reservas e cancelamento, datas extremas, relatórios, migração e bootstrap.
- **20 asserções JavaScript aprovadas** nos modelos com atributos privados, validações, estoque, quantidades, versões, endereço, reserva e herança de perfis.
- **10 fluxos HTTP/DOM integrados aprovados**: visitante sem checkout; cadastro/edição de prato; carrinho/compra; perfil/endereço/histórico; reservas/conflito/cancelamento; KDS/estimativa/status; relatórios; exclusão lógica; cadastro da equipe; login com erro/sucesso e logout.
- Scripts das telas executados contra servidor Flask e SQLite temporários; HTML malicioso em nome de prato apareceu como texto literal, sem criação de elemento ou execução.
- Sintaxe de todos os scripts JavaScript e compilação Python verificadas.
- Revisão independente sem defeitos críticos/importantes identificados. Foram reproduzidos e corrigidos dois casos de datas extremas para erro 400 controlado e três casos de preço legado fora das regras (zero, casas decimais excedentes e limite excedido) para conflito 409 sem pedido/baixa de estoque.

## Banco e reprodutibilidade

- Disputa simultânea pela última porção permite somente um pedido.
- Pedido com item inválido ou estoque insuficiente não deixa gravação parcial.
- Versão é alterada na baixa de estoque: uma edição administrativa antiga não restaura porções consumidas.
- Triggers bloqueiam reservas sobrepostas tanto em INSERT como em UPDATE.
- Migração aditiva mantém registros e deixa funcionário legado inativo/estoque legado zero até revisão/configuração.
- Novo banco criado pela aplicação possui o mesmo schema do modelo físico SQL e triggers entregues.
- Scripts repetidos não duplicam bancadas de referência nem criam credenciais.
- Atualização das triggers foi agrupada em transação para evitar janela sem proteção de estoque.
- Na versão completa base, o banco original foi comparado byte a byte ao enviado. Nesta cópia configurada, a migração já foi aplicada e foram criados administrador e bancadas de referência; ver TESTE_ADMIN_RESERVAS.md.

## Artefatos acadêmicos

Documentação PDF, apresentação PDF, DER de referência e dicionário DOCX foram renderizados e revisados. O grupo deve preencher identificação, revisar o conteúdo e conferir o protótipo original e suas normas acadêmicas. O dicionário foi obtido do schema SQL com SQLite, incluindo campos e referências. O DER nativo brModelo foi criado com classes oficiais e reaberto pelo leitor oficial: 10 entidades, 5 relacionamentos e 68 atributos, sem ligações desconectadas. Detalhes e limitações em DER_NATIVO_LEIA.md.

## Limites

Não houve validação visual nem teste de execução real de CSP em navegador: Chromium não ficou disponível. DOM não substitui navegador, teste de carga, auditoria completa de segurança ou validação de ambiente publicado. Não há certificação de segurança nem promessa de nota. O estado de Figma/brModelo/commits e demais itens externos consta em MATRIZ_REQUISITOS.md.
