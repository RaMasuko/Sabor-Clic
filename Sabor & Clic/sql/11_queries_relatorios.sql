-- Vendas diárias: todos os pedidos; não há cancelamento no fluxo de pedidos.
SELECT date(data_pedido) AS data,
    COUNT(*) AS pedidos,
    ROUND(SUM(valor_total), 2) AS faturamento
FROM pedidos
GROUP BY date(data_pedido)
ORDER BY data;

-- Estoque em porções de pratos não excluídos.
SELECT id_prato, nome, estoque, status
FROM pratos
WHERE excluido = 0
ORDER BY nome;

-- Ocupação reservada em minutos; reservas canceladas não ocupam a bancada.
SELECT b.id_bancada, b.nome,
    COUNT(r.id_reserva) AS reservas,
    COALESCE(
        ROUND(SUM((julianday(r.fim) - julianday(r.inicio)) * 1440), 2),
        0
    ) AS minutos_reservados
FROM bancadas b
LEFT JOIN reservas r
    ON r.id_bancada = b.id_bancada AND r.status = 'confirmada'
GROUP BY b.id_bancada;

SELECT COUNT(*) AS pedidos, COALESCE(SUM(valor_total), 0) AS faturamento
FROM pedidos;

SELECT COUNT(*) AS reservas
FROM reservas
WHERE status = 'confirmada';
