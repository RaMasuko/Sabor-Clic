> **Cópia com administrador criado:** use `admin@saborclic.local` e a senha informada na conversa. Não é necessário executar `criar-admin` para essa conta. As bancadas de referência já foram carregadas. A criação de reservas pelo administrador retorna 403; detalhes em `docs/TESTE_ADMIN_RESERVAS.md`. O código não foi alterado para ampliar permissões.

# Sabor & Clic — projeto revisado

Versão complementada do projeto enviado, mantendo Python/Flask, SQLite, JavaScript, HTML/CSS puros, as telas principais e a identidade vermelha/cinza/branca. Não usa plataforma pronta ou framework de interface.

## Começar

Use Python 3.10 ou superior. Abra o terminal dentro da pasta `Igor` extraída do ZIP.

```bash
python -m venv .venv
```

Ative o ambiente:

```powershell
# Windows / PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Instale e crie seu administrador com uma senha própria:

```bash
python -m pip install -r requirements.txt
python -m flask --app run criar-admin
python run.py
```

Acesse http://127.0.0.1:5000. Não existe senha padrão de administrador. O comando solicita nome, e-mail exclusivo, CPF e senha de 12 a 128 caracteres com confirmação.

## Preparar os dados para a demonstração

Neste pacote, o banco `sabor_clic.db` já foi migrado e configurado com a conta administrativa e duas bancadas de referência, preservando os registros originais. A senha foi informada na conversa.

1. Entre como administrador. Em **PRATOS**, cadastre/edite nome, descrição, preço, disponibilidade, ficha técnica e estoque em porções. Pratos legados começam com **estoque zero**, pois a versão anterior não informava quantidades. Informe o estoque real ou quantidades de teste antes de tentar comprar.
2. Em **RESERVAS**, o administrador cadastra bancadas. Se preferir carregar as duas bancadas de referência do SQL, execute:

```bash
python -m flask --app run carregar-bancadas
```

3. Em **EQUIPE**, cadastre um cozinheiro com turno e especialidade. Use um e-mail exclusivo por conta.
4. No cadastro público, crie um cliente com endereço. Com essa conta, monte o carrinho e reserve uma bancada. Acompanhe seus pedidos em **PERFIL**.
5. Entre como cozinheiro no **KDS**, registre estimativa de preparo e avance Aguardando → Iniciando Preparo → Pronto para Entrega.
6. Como administrador, confira **ESTOQUE** e **RELATÓRIOS**.

O primeiro administrador só é criado por quem tem acesso ao terminal. O cadastro público não permite criar funcionário nem escolher privilégios.

### Funcionários antigos

A versão original permitia cadastro público de funcionários. Por segurança, essas contas legadas são preservadas, mas ficam inativas até conferência. Para reativar uma conta que você verificou:

```bash
python -m flask --app run ativar-funcionario --email conta@exemplo.com
```

O comando pede confirmação e mantém o perfil de cozinheiro. Clientes legados permanecem; confira seu endereço no perfil. Não há promoção automática de funcionário a administrador. Sessões da versão anterior deixam de ser aceitas.

Se já houve uso depois do ZIP original, não sobrescreva esse banco com o banco antigo do pacote: preserve o arquivo mais recente e faça backup antes da migração. Se existir o mesmo e-mail em contas diferentes, o login recusa a ambiguidade até conferência/correção dos registros.

## Funcionalidades implementadas

| Área | Comportamento |
|---|---|
| Catálogo | Criar, consultar, editar, ativar/inativar e excluir logicamente pratos; ficha técnica textual e estoque por porção |
| Carrinho | Adicionar, alterar quantidade e remover; mostrar subtotais e total; enviar por JSON/fetch |
| Checkout | Servidor confere preço/versão/disponibilidade e endereço, grava pedido atomicamente e evita duplicação com a mesma chave |
| Estoque | Trigger faz baixa automática e bloqueia quantidade insuficiente; versões impedem atualização administrativa com estoque desatualizado |
| Histórico | Nome/preço do item ficam registrados no pedido; exclusão/edição do prato não altera compras anteriores |
| Cozinha | Fila pendente com atualização periódica, estimativa e previsão, transições de status controladas |
| Cliente | Endereço, perfil editável e rastreamento periódico somente de seus pedidos |
| Equipe | Perfis separados; cozinheiro tem turno/especialidade; criação de contas restrita ao administrador |
| Reservas | Horários reais por bancada, filtro por proprietário, cancelamento, bloqueio de sobreposição também por trigger |
| Relatórios | Vendas, estoque e ocupação de bancadas via queries SQL e interface |
| Interface | CSS puro responsivo, cartões e navegação inferior; feedback de carregamento, sucesso e erro, sem recarga para atualizar dados |

## Arquitetura e arquivos

```text
app/
  controllers/  rotas, validação de requisições e respostas JSON
  models/       consultas parametrizadas, persistência e transações
  middleware/   autenticação, perfis, CSRF e cabeçalhos
  templates/    HTML das telas
  static/       CSS puro, modelos ES6, API e scripts das telas
sql/            modelo físico, dados mínimos, relatórios e triggers
tests/          regressões Python e execução JavaScript/DOM
docs/           documentação, apresentação, DER e dicionário
```

O banco é acessado pelo backend. A interface usa `fetch` e JSON nas operações; os formulários de login/cadastro/equipe também possuem fallback de POST no servidor. A navegação entre páginas continua normal. Classes JavaScript usam atributos privados `#`, validações estáticas e herança para os perfis.

## Reproduzir o banco por SQL

Em banco **novo**, execute na ordem:

1. `sql/01_modelo_fisico.sql`;
2. `sql/02_insercoes_basicas.sql` (duas bancadas de referência, sem usuários/senhas);
3. `sql/20_triggers.sql`.

`sql/11_queries_relatorios.sql` contém as consultas de vendas, estoque e ocupação. A inicialização do aplicativo usa o mesmo modelo físico e aplica migrações aditivas para o legado. Não execute manualmente scripts de reconstrução sobre o único banco existente.

## Segurança e limites

As rotas verificam autenticação, perfil e propriedade no servidor. Senhas são armazenadas com hash Werkzeug; sessões expiram em 30 minutos desde o login e seus tokens são revogados no logout. Mudanças de perfil/status são consideradas em cada requisição. CSRF protege mutações; consultas usam parâmetros e a interface insere dados como texto.

Há limite de login por e-mail (5 tentativas) e IP (30 tentativas) em janela de 15 minutos. Corpo da requisição limitado a 64 KiB; pedidos com até 100 pratos distintos e de 1 a 99 unidades por item. Preço positivo de até R$ 1 milhão e duas casas decimais. Endereço tem 5 a 200 caracteres. Reserva deve começar no futuro, em até 90 dias, durar no máximo 12 horas e informar fuso horário. O armazenamento usa UTC e a interface mostra o horário local.

Estoque é de **porções prontas**, não de ingredientes. A ficha técnica é um texto de referência; não há decomposição automática de receitas nem compra de insumos. Essa decisão atende à baixa automática solicitada sem inventar uma modelagem de ingredientes que não foi definida no enunciado.

Quantias são calculadas com Decimal, mantendo a coluna monetária SQLite do projeto original. Não há pagamento real, gateway, envio de e-mail ou serviço de entrega integrado no enunciado. Antes de uso comercial, revisar também implantação, backup, monitoramento e testes de infraestrutura.

Para uso local, uma chave aleatória persistente é criada em `instance/secret_key`; não acompanha o ZIP. Para publicação, configure `SABOR_ENV=production`, `SABOR_SECRET_KEY` com chave aleatória própria de pelo menos 32 caracteres e, se necessário, `SABOR_DATABASE` com caminho absoluto. Não há carregamento automático de `.env`.

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Use HTTPS e servidor WSGI apropriado em produção. O modo produção recusa HTTP e usa cookie Secure; `python run.py` é para desenvolvimento local. Cabeçalhos de proxy devem ser configurados somente quando originados do proxy confiável; o código não confia automaticamente em `X-Forwarded-*` de visitantes.

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Modelos JavaScript:

```bash
node tests/test_front_models.cjs
```

Fluxos das telas em DOM (Node.js 22.13 ou superior e npm):

```bash
npm install --prefix tests
python tests/run_frontend.py
```

O executor usa porta local 5001, banco descartável e contas fictícias exclusivas dos testes. Ele não modifica o banco do projeto. O DOM executa scripts e requisições HTTP reais, mas não substitui verificação visual em navegador, comportamento real de CSP ou testes de carga. Resultado exato em `docs/VERIFICACAO.md`.

## Materiais e conferência acadêmica

Em `docs/`: documentação PDF e texto editável, apresentação PDF e roteiro, dicionário de dados DOCX, DER de referência e arquivo nativo `DER_SABOR_CLIC.brM3`, guia de estilos e matriz dos requisitos.

Preencha os nomes e a turma, revise os materiais e ensaie a explicação do código. O Figma original não foi enviado, então não foi possível atestar fidelidade ao protótipo aprovado. O DER nativo fornecido foi reaberto pelo leitor oficial; o grupo deve revisar sua modelagem/cardinalidades no brModelo. Os commits reais dos integrantes também devem ser conferidos conforme a matriz. A submissão no Moodle depende do grupo. Esses itens não são substituídos por testes do código.
