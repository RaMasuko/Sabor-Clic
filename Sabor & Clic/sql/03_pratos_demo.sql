BEGIN IMMEDIATE;

INSERT INTO pratos (nome, descricao, preco, estoque, ficha_tecnica)
SELECT 'Coxinha', 'Coxinha crocante recheada com frango.', 10.00, 20, 'Massa empanada e frango desfiado.'
WHERE NOT EXISTS (SELECT 1 FROM pratos WHERE lower(nome) = 'coxinha' AND excluido = 0);

INSERT INTO pratos (nome, descricao, preco, estoque, ficha_tecnica)
SELECT 'Hambúrguer', 'Hambúrguer com queijo, alface e tomate.', 24.90, 20, 'Pão, carne, queijo, alface e tomate.'
WHERE NOT EXISTS (SELECT 1 FROM pratos WHERE lower(nome) IN ('hambúrguer', 'hamburguer') AND excluido = 0);

COMMIT;
