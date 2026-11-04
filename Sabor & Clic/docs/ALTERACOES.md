# O que foi preservado e completado

A base continua sendo o projeto enviado: Flask, SQLite, JavaScript ES6, HTML e CSS puros, padrão MVC, as telas de cardápio/carrinho, login/cadastro, perfil, novo prato, KDS e reservas. Foram mantidos o vermelho de marca, o fundo claro, os cartões e a navegação inferior.

| Arquivo ou área original | Complementação |
|---|---|
| run.py | Continua como entrada; inicialização/configuração organizada em create_app, sem debug e segredo fixo |
| app/models/database.py | Mesma conexão SQLite e inicialização; esquema em SQL e migração aditiva |
| Controllers de cardápio e pedidos | Rotas existentes mantidas e completadas; persistência nos modelos, validações e perfis |
| main_controller.py | Telas originais e autenticação; APIs JSON adicionais e perfil editável |
| script.js | AppController e carrinho preservados; entidades extraídas para models.js para organização |
| Templates | Mesmos caminhos/telas; semântica, responsividade e funções que faltavam |
| Middleware vazio | Autenticação, autorização, CSRF e cabeçalhos comuns |
| Reservas demonstrativas | Registros reais, cancelamento e proteção de horários |
| Banco de dados original | Registros preservados; nesta cópia os novos campos/tabelas e o administrador já estão configurados, sem inventar estoque positivo |

Arquivos novos concentram as funções que ainda não existiam: modelos de dados, APIs de reservas, scripts de cada tela, SQLs exigidos, testes e materiais acadêmicos. Não houve troca de tecnologia nem uso de plataforma pronta.
