-- Atualização atômica: nenhum pedido observa uma janela sem trigger de estoque.
BEGIN IMMEDIATE;

-- Executar após 01; init_db aplica a migração aditiva antes deste arquivo.
CREATE UNIQUE INDEX IF NOT EXISTS pedido_idempotencia
    ON pedidos (id_cliente, chave_requisicao)
    WHERE chave_requisicao IS NOT NULL;

CREATE INDEX IF NOT EXISTS reservas_intervalos
    ON reservas (id_bancada, status, inicio, fim);

CREATE TRIGGER IF NOT EXISTS estoque_nao_negativo_insert
BEFORE INSERT ON pratos
WHEN NEW.estoque < 0
BEGIN
    SELECT RAISE(ABORT, 'Estoque negativo');
END;

CREATE TRIGGER IF NOT EXISTS estoque_nao_negativo_update
BEFORE UPDATE OF estoque ON pratos
WHEN NEW.estoque < 0
BEGIN
    SELECT RAISE(ABORT, 'Estoque insuficiente');
END;

CREATE TRIGGER IF NOT EXISTS estoque_item_valido
BEFORE INSERT ON itens_pedido
BEGIN
    SELECT CASE
        WHEN NEW.quantidade <= 0 OR NEW.preco_unitario < 0
        THEN RAISE(ABORT, 'Item inválido')
    END;
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM pratos
            WHERE id_prato = NEW.id_prato
                AND status = 'disponivel'
                AND excluido = 0
                AND estoque >= NEW.quantidade
        )
        THEN RAISE(ABORT, 'Prato indisponível ou estoque insuficiente')
    END;
END;

-- Substituição idempotente também atualiza a versão anterior deste trigger.
-- A versão acompanha o estoque para impedir PUT administrativo desatualizado.
DROP TRIGGER IF EXISTS estoque_baixa;
CREATE TRIGGER estoque_baixa
AFTER INSERT ON itens_pedido
BEGIN
    UPDATE pratos
    SET estoque = estoque - NEW.quantidade,
        versao = versao + 1
    WHERE id_prato = NEW.id_prato;
END;

CREATE TRIGGER IF NOT EXISTS reserva_conflito_insert
BEFORE INSERT ON reservas
WHEN NEW.status = 'confirmada'
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM bancadas
            WHERE id_bancada = NEW.id_bancada AND ativo = 1
        )
        THEN RAISE(ABORT, 'Bancada inativa')
    END;
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM reservas
            WHERE id_bancada = NEW.id_bancada
                AND status = 'confirmada'
                AND NEW.inicio < fim
                AND NEW.fim > inicio
        )
        THEN RAISE(ABORT, 'Reserva sobreposta')
    END;
END;

CREATE TRIGGER IF NOT EXISTS reserva_conflito_update
BEFORE UPDATE ON reservas
WHEN NEW.status = 'confirmada'
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM bancadas
            WHERE id_bancada = NEW.id_bancada AND ativo = 1
        )
        THEN RAISE(ABORT, 'Bancada inativa')
    END;
    SELECT CASE
        WHEN EXISTS (
            SELECT 1 FROM reservas
            WHERE id_reserva <> NEW.id_reserva
                AND id_bancada = NEW.id_bancada
                AND status = 'confirmada'
                AND NEW.inicio < fim
                AND NEW.fim > inicio
        )
        THEN RAISE(ABORT, 'Reserva sobreposta')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_log_status_pedido
AFTER UPDATE OF status ON pedidos
WHEN NEW.status <> OLD.status
BEGIN
    INSERT INTO log_pedidos (id_pedido, status_anterior, status_novo)
    VALUES (OLD.id_pedido, OLD.status, NEW.status);
END;

COMMIT;
