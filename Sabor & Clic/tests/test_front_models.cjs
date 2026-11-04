const fs = require("fs");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "../app/static");
const context = { window: {}, Date, Number, Object, Error };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, "models.js"), "utf8"), context);
const { Prato, Carrinho, Cliente, Cozinheiro, Administrador, Reserva, Pedido } =
  context.window.SaborModels;
const prato = new Prato({
  id: 1,
  nome: "Arroz",
  preco: 12.5,
  estoque: 2,
  versao: 3,
  status: "disponivel",
});
const carrinho = new Carrinho();
carrinho.adicionarPrato(prato);
carrinho.adicionarPrato(prato);
assert.equal(carrinho.total, 25);
assert.throws(() => carrinho.adicionarPrato(prato), /estoque/);
carrinho.alterarQuantidade(1, 1);
assert.equal(carrinho.total, 12.5);
assert.equal(carrinho.toJSON()[0].versao, 3);
assert.throws(() => carrinho.alterarQuantidade(1, 1.5));
const snapshot = carrinho.itens;
snapshot.pop();
assert.equal(carrinho.itens.length, 1);
carrinho.remover(1);
assert.equal(carrinho.total, 0);
assert(new Cliente("Ana Silva", "ana@example.com").pode("pedido"));
assert(!new Cozinheiro("Ana Silva", "ana@example.com").pode("catalogo"));
assert(new Administrador("Ana Silva", "ana@example.com").pode("catalogo"));
assert(!Reserva.validar(Date.now() - 1000, Date.now() + 1000));
assert(Reserva.validar(Date.now() + 60000, Date.now() + 120000));
assert(!Reserva.validar(Date.now() + 60000, Date.now() + 13 * 3600000));
assert(Pedido.validarEndereco("Rua das Flores, 5"));
assert(!Pedido.validarEndereco(""));
assert.throws(() => new Prato({ id: 1, nome: "x", preco: -1 }));
const pratoGrande = new Prato({
  id: 2,
  nome: "Feijão",
  preco: 10,
  estoque: 150,
});
carrinho.adicionarPrato(pratoGrande);
carrinho.alterarQuantidade(2, 99);
assert.equal(carrinho.itens[0].quantidade, 99);
assert.throws(() => carrinho.alterarQuantidade(2, 100), /99/);
assert.throws(
  () =>
    carrinho.adicionarPrato(
      new Prato({ id: 3, nome: "Sem estoque", preco: 10, estoque: 0 }),
    ),
  /indisponível/,
);
console.log("Frontend models: 20 assertions passed.");
