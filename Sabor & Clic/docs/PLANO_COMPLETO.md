# Plano de complementação - Sabor & Clic

Pedido: corrigir e completar os códigos segundo o enunciado, preservando a essência do projeto e reforçando segurança.

## Restrições

Flask, SQLite, Python, HTML/CSS puros e JavaScript ES6. Manter MVC, nomes das telas e caminhos existentes sempre possível, identidade vermelha/cinza/branca, cartões simples e navegação inferior. Sem no-code, framework de interface ou site novo. Preservar banco original e aplicar migrações aditivas.

## Decisões

Estoque contado em porções de cada prato: o enunciado exige baixa automática, mas não fornece unidade/modelagem de insumos. Trigger SQL realiza baixa e bloqueia falta de estoque; sem inventar estoque positivo para pratos legados. Exclusão lógica mantém histórico de pedidos. Reservas usam intervalos em UTC e apresentação local, com bloqueio contra sobreposição no banco. Cliente tem endereço de entrega; cozinheiro tem turno e especialidade; pedido tem tempo estimado. JSON/fetch para operações, incluindo cadastro/login/perfil/equipe, com flash visual e token CSRF renovado após autenticação. Primeiro administrador continua via terminal, sem senha padrão.

## Trabalho

- [x] Banco/modelos: schema físico, migração preservando dados, seeds sem credenciais, triggers de estoque/reservas/auditoria, queries de vendas/estoque/ocupação e modelos MVC.
- [x] Backend: CRUD de catálogo, pedidos completos com endereço e estimativa, perfil, reservas/bancadas/relatórios, APIs de autenticação e equipe, validação/autorizações, idempotência.
- [x] Frontend: manter estética, CSS responsivo/semântico, modelos com atributos privados/herança/método estático, fetch GET/POST/PUT/DELETE e estados de tela sem recarga de dados.
- [x] Testes: manter regressões de segurança; incluir estoque, concorrência, reservas, CRUD, relatórios, migração e DOM ponta a ponta.
- [x] Materiais: SQLs nomeados conforme enunciado, dicionário de dados, DER de referência, guia de estilos, matriz de requisitos, documentação e apresentação revisáveis.
- [x] Revisão independente, verificação do ZIP extraído e instruções finais.

## Limites externos

Figma original, identificação dos integrantes e histórico de commits não foram fornecidos. Não fabricar esses itens nem alegar conformidade visual comprovada. Além da referência em PDF, foi gerado um arquivo nativo brModelo com as classes oficiais, reaberto pelo leitor oficial; o grupo deve revisar a modelagem conceitual/cardinalidades antes da entrega. Documentação acadêmica é minuta para revisão dos integrantes.

## Verificação

Revisão independente sem falhas críticas/importantes. Suíte Python e fluxos HTTP/DOM executados; resultados finais em VERIFICACAO.md. Datas extremas com overflow de fuso retornam validação controlada. A troca da trigger de estoque acontece em transação para não deixar pedidos observarem uma janela sem baixa automática. Não foram fabricados nomes, Figma aprovado ou histórico Git.
