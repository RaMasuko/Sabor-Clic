# Roteiro da apresentação Sabor & Clic

Texto editável para o grupo revisar antes de atualizar o PDF.

## 1 Sabor & Clic

- Gestão de dark kitchens e espaços gastronômicos
- IFSP Campus São Paulo
- Integrantes: [preencher]    Turma: [preencher]
- 2026

## 2 Problema e atores

- Planilhas e anotações dificultam pedidos, preços e horários.
- Administrador: catálogo, equipe, bancadas e relatórios.
- Cliente: compra, acompanha pedidos e reserva espaços.
- Cozinheiro: fila de produção, estimativa e status.

## 3 Arquitetura MVC

- HTML5 e CSS3 puros apresentam a interface responsiva.
- JavaScript ES6 modela entidades, estado e eventos do DOM.
- Fetch envia e recebe JSON de forma assíncrona.
- Controllers Flask validam acesso e entrada. Models transacionam no SQLite.

## 4 Compra e produção

- O cliente escolhe pratos, quantidade e endereço.
- O servidor recalcula o total e confere versão, disponibilidade e estoque.
- Uma trigger baixa porções e bloqueia estoque insuficiente.
- Aguardando / Iniciando Preparo / Pronto para Entrega.
- A chave de idempotência reduz duplicações por reenvio.

## 5 Reservas e persistência

- Bancadas ativas recebem reservas futuras com início e fim.
- Datas com fuso são normalizadas para UTC.
- O banco impede sobreposição de reservas confirmadas.
- Pedidos e itens preservam o histórico após remoção lógica de pratos.
- Relatórios consultam vendas, estoque e ocupação.

## 6 Segurança e feedback

- Sessão identifica o usuário. Perfil e propriedade limitam cada operação.
- Senhas usam hash. Mutações exigem token CSRF.
- Consultas parametrizadas e validações protegem a entrada.
- DOM com textContent e mensagens visíveis reduzem riscos e dúvidas.
- Antes de uso público: HTTPS, segredos próprios e revisão de infraestrutura.

## 7 Demonstração e testes

- Compra do cliente e atualização da fila pelo cozinheiro.
- CRUD administrativo e tentativa de venda sem estoque.
- Dois clientes disputam um horário e recebem o resultado do conflito.
- Testes de API, migração, DOM e navegador verificam regressões.
- Resultados efetivos: consultar VERIFICACAO.md após a execução.

## 8 Revisão e entrega

- Preencher integrantes e turma e revisar documentação.
- Comparar com o Figma original, ainda não fornecido.
- Arquivo nativo brModelo fornecido: revisar entidades, relações e cardinalidades.
- Registrar contribuições reais no Git e preparar a apresentação oral.
- Submeter PDF da apresentação, documentação e projeto no Moodle.
