-- Sem clientes, funcionários, senhas ou estoque fictício. Reexecução segura.
INSERT INTO bancadas (nome, localizacao)
SELECT 'Bancada 1', 'Salão principal'
WHERE NOT EXISTS (
    SELECT 1 FROM bancadas WHERE nome = 'Bancada 1'
);

INSERT INTO bancadas (nome, localizacao)
SELECT 'Bancada 2', 'Salão principal'
WHERE NOT EXISTS (
    SELECT 1 FROM bancadas WHERE nome = 'Bancada 2'
);
