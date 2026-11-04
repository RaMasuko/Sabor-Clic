# Controles de segurança desta versão

| Controle | Onde e como |
|---|---|
| Autorização | Middleware lê usuário/perfil/status atuais; decorators restringem cada rota; clientes só consultam seus próprios pedidos e reservas |
| Contas privilegiadas | Primeiro administrador no terminal; cadastro de equipe somente por administrador; funcionários antigos inativos até revisão explícita |
| Senhas e autenticação | Hash Werkzeug, mensagem genérica de falha e contadores persistentes/atômicos por e-mail e IP |
| Sessões | Chave fora do código, token aleatório registrado por hash no banco, expiração absoluta de 30 minutos e revogação no logout |
| CSRF | Token por sessão nos formulários e cabeçalho nas chamadas mutáveis; renovação no login/logout; cookies HttpOnly/SameSite e Secure em produção |
| SQL Injection | Todas as entradas são parâmetros de consultas; SQL de migração interpola somente nomes/definições constantes do próprio código |
| XSS | Templates com escape, dados dinâmicos via textContent/createElement, nenhum dado de usuário interpretado como HTML |
| Catálogo e estoque | Validação de tipos/limites, versão otimista, exclusão lógica e trigger de baixa; atualizações administrativas desatualizadas são recusadas |
| Pedidos | Preços no servidor, cálculo Decimal, transação, snapshots históricos e chave idempotente por cliente/conteúdo |
| Reservas | Datas normalizadas em UTC, intervalo limitado, propriedade verificada e bloqueio atômico de sobreposição por trigger |
| Erros | Mensagens de domínio controladas; falhas internas são registradas no servidor e não expõem SQL ao navegador |
| Navegador | CSP sem scripts inline, antiframing, nosniff, no-store em respostas dinâmicas e HSTS no modo produção HTTPS |
| Integridade relacional | Chaves estrangeiras ativadas em cada conexão; scripts SQL e migrações testados |

## Relação didática com OWASP Top 10:2025

A01: controles de acesso, propriedade e CSRF. A02: configuração e cabeçalhos. A04: hash, chaves/tokens e HTTPS. A05: parâmetros SQL e saída segura. A06: preço/estoque/intervalos controlados no servidor. A07: sessões, contas inativas e limitação de login. A10: validação de condições excepcionais e reversão de transações.

A relação acima descreve controles implementados, sem alegar cobertura integral das dez categorias ou certificação. Auditoria de status existente é preservada; não há um sistema completo de alertas/monitoramento. Referências: https://top10.owasp.org/2025/pt-BR/ e https://flask.palletsprojects.com/en/stable/web-security/ .

## Demonstrações de regressão

A suíte testa criação indevida de funcionário, elevação de perfil, acesso cruzado, conta inativa, expiração e replay após logout; token CSRF ausente/de outro navegador/inválido; entrada SQL em login, JSON malformado, tipos/quantidades/preços inválidos; falsificação de subtotal, falta de estoque, disputa pela última porção, pedido duplicado, versão desatualizada e preservação do histórico; reserva sobreposta, cancelamento de outra conta e datas extremas.

O teste DOM percorre as telas contra Flask com banco temporário e verifica que um nome com HTML permanece texto literal. Chromium não ficou disponível para teste visual/CSP real. Execução, resultados e limites constam em VERIFICACAO.md.
