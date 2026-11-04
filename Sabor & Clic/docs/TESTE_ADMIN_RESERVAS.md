# Verificação do administrador

Conta criada neste pacote: admin@saborclic.local (perfil administrador). A senha foi informada na conversa e é armazenada apenas por hash no banco do projeto. Nenhuma senha padrão foi acrescentada ao código.

Teste realizado com login real na API Flask e banco desta cópia:

- Login do administrador: HTTP 200.
- Acesso à página de reservas: HTTP 200.
- Cadastro/consulta de bancadas: permitido pelo perfil.
- Tentativa de criar reserva via POST /api/reservas: HTTP 403.
- Conferência do banco: nenhuma reserva foi inserida pela tentativa.
- A tela do administrador apresenta cadastro de bancada, não o formulário de reserva do cliente.

A criação de reservas permanece restrita ao cliente, conforme o controle de acesso existente. Nenhuma permissão foi ampliada nesta verificação. Para permitir criação pelo administrador será preciso definir se ele reserva em nome de um cliente ou se há reservas internas com outro responsável; o ID do funcionário não pode ser usado como se fosse ID de cliente.

Esta cópia está configurada com administrador e duas bancadas de referência. Portanto o banco deste pacote já foi migrado e configurado; não é mais uma cópia byte a byte do banco original. O código é o mesmo da versão completa.
