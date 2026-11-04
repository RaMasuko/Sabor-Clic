-- Fonte única do schema para bancos novos, também carregada por init_db.
-- Inicialização independente: executar 01, 02 (opcional) e 20, nessa ordem.
-- As migrações aditivas de bancos legados ficam em app/models/database.py.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    senha VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),
    endereco VARCHAR(200),
    status VARCHAR(20) DEFAULT 'ativo'
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id_funcionario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    senha VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),
    cargo VARCHAR(50) NOT NULL,
    salario MONEY,
    perfil TEXT NOT NULL DEFAULT 'cozinheiro',
    status TEXT NOT NULL DEFAULT 'ativo',
    turno TEXT NOT NULL DEFAULT '',
    especialidade TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pratos (
    id_prato INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(250),
    preco MONEY NOT NULL,
    status VARCHAR(20) DEFAULT 'disponivel',
    estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    excluido INTEGER NOT NULL DEFAULT 0 CHECK (excluido IN (0, 1)),
    versao INTEGER NOT NULL DEFAULT 1,
    ficha_tecnica TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INT NOT NULL,
    data_pedido DATETIME NOT NULL,
    valor_total MONEY NOT NULL,
    status VARCHAR(30) DEFAULT 'Aguardando',
    endereco_entrega TEXT NOT NULL DEFAULT '',
    tempo_estimado_min INTEGER,
    data_previsao TEXT,
    chave_requisicao TEXT,
    hash_requisicao TEXT,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INT NOT NULL,
    id_prato INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario MONEY NOT NULL,
    nome_prato TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
    FOREIGN KEY (id_prato) REFERENCES pratos(id_prato)
);

CREATE TABLE IF NOT EXISTS log_pedidos (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido INT NOT NULL,
    status_anterior VARCHAR(30),
    status_novo VARCHAR(30),
    data_alteracao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    usuario_id INTEGER NOT NULL,
    criada_em INTEGER NOT NULL,
    expira_em INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS login_attempts (
    chave TEXT PRIMARY KEY,
    tentativas INTEGER NOT NULL,
    inicio INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bancadas (
    id_bancada INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    localizacao TEXT NOT NULL DEFAULT '',
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS reservas (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
    id_bancada INTEGER NOT NULL REFERENCES bancadas(id_bancada),
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmada'
        CHECK (status IN ('confirmada', 'cancelada')),
    criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (inicio < fim)
);
