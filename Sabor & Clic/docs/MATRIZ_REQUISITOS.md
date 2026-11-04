# Matriz de requisitos Sabor & Clic

A evidência indica onde revisar o requisito. Não constitui declaração antecipada de aprovação dos testes ou da avaliação acadêmica. O resultado efetivo consta em VERIFICACAO.md após a execução final.

| ID | Requisito | Evidência | Critério e situação |
| --- | --- | --- | --- |
| AV01 | Figma e wireframes | Figma original e protótipo navegável | Pendente externo: grupo deve fornecer e revisar |
| AV02 | Paleta, tipografia e guia | GUIA_ESTILOS.md e HTML/CSS | Referência documentada; revisão visual pelo grupo |
| AV03 | KDS, cardápio e responsividade | app/templates e estilos CSS puros | Verificar telas e larguras no teste de navegador |
| JS01 | DOM, arrays e cálculo do carrinho | app/static, modelos e scripts de tela | Verificar testes DOM e demonstração |
| JS02 | Classes ES6, #, herança e estáticos | app/static/models.js | Conferir código e explicar entidades oralmente |
| JS03 | Fetch, JSON e GET/POST/PUT/DELETE | app/static/api.js e scripts de tela | Verificar testes e erros HTTP sem recarga |
| JS04 | Loading, sucesso, erro e try/catch | Scripts de interface e feedback | Revisar falha de rede e resposta inválida |
| PY01 | Flask e MVC | app/models, app/controllers, app/templates | Conferir separação de responsabilidades |
| PY02 | Sessões, cookies, middleware e flash | Autenticação, middleware e mensagens | Consultar VERIFICACAO.md após execução |
| BD01 | DER no brModelo | DER_REFERENCIA.pdf e DER_SABOR_CLIC.brM3 | Arquivo nativo fornecido; revisão conceitual pelo grupo |
| BD02 | Dicionário de dados DOCX | DICIONARIO_DADOS.docx | Revisar campos com schema entregue |
| BD03 | Modelo físico e dados mínimos | sql/01_modelo_fisico.sql e 02_insercoes_basicas.sql | Reproduzir banco vazio e preservar banco legado |
| BD04 | Relatórios e triggers | sql/11_queries_relatorios.sql e 20_triggers.sql | Verificar estoque, auditoria e ocupação |
| SEG01 | RBAC e propriedade | Middleware, controllers e modelos | Testar cliente, cozinheiro, administrador e anônimo |
| SEG02 | Autenticação, CSRF e entrada | Hash, sessão, token e SQL parametrizado | Consultar verificações e limites de implantação |
| RF01 | CRUD do catálogo e controle de estoque | API de cardápio e gestão administrativa | Testar preço, versão, exclusão lógica e estoque |
| RF02 | Carrinho, compra e rastreamento | API de pedidos e telas do cliente | Testar total do servidor, histórico e status |
| RF03 | Fila e estimativa de produção | KDS e API de pedidos | Testar fluxo de status e previsão |
| RF04 | Locação de bancadas | API e tela de reservas | Testar sobreposição, UTC e cancelamento |
| DOC01 | Reflexões e documentação ABNT | DOCUMENTACAO.pdf | Minuta A4 para revisão acadêmica |
| DOC02 | Apresentação em PDF | APRESENTACAO.pdf | Preencher nomes/turma e ensaiar demonstração |
| ENT01 | Histórico Git de integrantes | Repositório real do grupo | Pendente externo; não fabricar contribuições |
| ENT02 | Submissão Moodle | PDFs e ZIP ou link do repositório | Pendente externo: responsabilidade do grupo |

## Pendências antes da entrega

Nomes completos e turma; revisão integral da documentação; Figma original e comparação visual; revisão do arquivo nativo DER_SABOR_CLIC.brM3 no brModelo; histórico real de commits de todos os integrantes; submissão no Moodle. Conferir também orientações e datas atualizadas dos professores.
