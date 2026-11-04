"use strict";
class Usuario {
  #nome;
  #email;
  constructor(nome, email) {
    if (!Usuario.validar(nome, email))
      throw new Error("Nome ou e-mail inválido.");
    this.#nome = nome.trim();
    this.#email = email.trim();
  }
  static validar(nome, email) {
    return (
      typeof nome === "string" &&
      nome.trim().length >= 3 &&
      nome.trim().length <= 100 &&
      typeof email === "string" &&
      email.length <= 120 &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    );
  }
  get nome() {
    return this.#nome;
  }
  get email() {
    return this.#email;
  }
  get perfil() {
    return "usuario";
  }
  pode(acao) {
    return acao === "perfil";
  }
}
class Cliente extends Usuario {
  #endereco;
  constructor(nome, email, endereco = "") {
    super(nome, email);
    this.#endereco = endereco;
  }
  get endereco() {
    return this.#endereco;
  }
  get perfil() {
    return "cliente";
  }
  pode(acao) {
    return super.pode(acao) || ["pedido", "reserva"].includes(acao);
  }
}
class Cozinheiro extends Usuario {
  #turno;
  #especialidade;
  constructor(nome, email, turno = "", especialidade = "") {
    super(nome, email);
    this.#turno = turno;
    this.#especialidade = especialidade;
  }
  get turno() {
    return this.#turno;
  }
  get especialidade() {
    return this.#especialidade;
  }
  get perfil() {
    return "cozinheiro";
  }
  pode(acao) {
    return super.pode(acao) || acao === "cozinha";
  }
}
class Administrador extends Cozinheiro {
  get perfil() {
    return "administrador";
  }
  pode(acao) {
    return (
      super.pode(acao) ||
      ["catalogo", "equipe", "relatorios", "bancadas"].includes(acao)
    );
  }
}
class Prato {
  #dados;
  constructor(
    id,
    nome,
    preco,
    descricao = "",
    estoque = 0,
    versao = 1,
    status = "disponivel",
    ficha_tecnica = "",
  ) {
    const dados =
      typeof id === "object"
        ? id
        : {
            id,
            nome,
            preco,
            descricao,
            estoque,
            versao,
            status,
            ficha_tecnica,
          };
    if (!Prato.validar(dados)) throw new Error("Prato inválido.");
    this.#dados = {
      ...dados,
      id: Number(dados.id),
      preco: Number(dados.preco),
      estoque: Number(dados.estoque || 0),
    };
  }
  static validar(d) {
    return (
      !!d &&
      Number.isInteger(Number(d.id)) &&
      Number(d.id) > 0 &&
      typeof d.nome === "string" &&
      d.nome.trim().length > 0 &&
      Number.isFinite(Number(d.preco)) &&
      Number(d.preco) > 0 &&
      Number.isInteger(Number(d.estoque || 0)) &&
      Number(d.estoque || 0) >= 0
    );
  }
  get id() {
    return this.#dados.id;
  }
  get nome() {
    return this.#dados.nome;
  }
  get preco() {
    return this.#dados.preco;
  }
  get descricao() {
    return this.#dados.descricao || "";
  }
  get estoque() {
    return this.#dados.estoque;
  }
  get versao() {
    return this.#dados.versao;
  }
  get status() {
    return this.#dados.status || "disponivel";
  }
  get fichaTecnica() {
    return this.#dados.ficha_tecnica || "";
  }
}
class ItemPedido {
  #prato;
  #quantidade;
  constructor(prato, quantidade = 1) {
    this.#prato = prato;
    this.quantidade = quantidade;
  }
  static validarQuantidade(n) {
    return Number.isInteger(Number(n)) && Number(n) > 0 && Number(n) <= 99;
  }
  set quantidade(n) {
    if (!ItemPedido.validarQuantidade(n))
      throw new Error("Quantidade deve ser um inteiro entre 1 e 99.");
    if (Number(n) > this.#prato.estoque)
      throw new Error("Quantidade excede o estoque disponível.");
    this.#quantidade = Number(n);
  }
  incrementar() {
    this.quantidade = this.#quantidade + 1;
  }
  get prato() {
    return this.#prato;
  }
  get quantidade() {
    return this.#quantidade;
  }
  get subtotal() {
    return this.#prato.preco * this.#quantidade;
  }
}
class Carrinho {
  #itens = [];
  adicionarPrato(prato) {
    if (prato.status !== "disponivel" || prato.estoque < 1)
      throw new Error("Prato indisponível.");
    const item = this.#itens.find((i) => i.prato.id === prato.id);
    if (item) item.incrementar();
    else this.#itens.push(new ItemPedido(prato));
  }
  alterarQuantidade(id, n) {
    const i = this.#itens.find((i) => i.prato.id === id);
    if (i) i.quantidade = n;
  }
  remover(id) {
    this.#itens = this.#itens.filter((i) => i.prato.id !== id);
  }
  limpar() {
    this.#itens = [];
  }
  get itens() {
    return [...this.#itens];
  }
  get total() {
    return this.#itens.reduce((a, i) => a + i.subtotal, 0);
  }
  toJSON() {
    return this.#itens.map((i) => ({
      idPrato: i.prato.id,
      quantidade: i.quantidade,
      versao: i.prato.versao,
    }));
  }
}
class Pedido {
  #dados;
  constructor(dados) {
    this.#dados = Object.freeze({ ...dados });
  }
  static validarEndereco(e) {
    return (
      typeof e === "string" && e.trim().length >= 5 && e.trim().length <= 200
    );
  }
  get dados() {
    return this.#dados;
  }
  get pendente() {
    return ["Aguardando", "Iniciando Preparo"].includes(this.#dados.status);
  }
}
class Reserva {
  #inicio;
  #fim;
  constructor(inicio, fim) {
    if (!Reserva.validar(inicio, fim))
      throw new Error(
        "Reserva deve começar no futuro (até 90 dias) e durar no máximo 12 horas.",
      );
    this.#inicio = new Date(inicio).toISOString();
    this.#fim = new Date(fim).toISOString();
  }
  static validar(a, b) {
    const inicio = new Date(a).getTime(),
      fim = new Date(b).getTime(),
      agora = Date.now();
    return (
      Number.isFinite(inicio) &&
      Number.isFinite(fim) &&
      inicio > agora &&
      inicio <= agora + 90 * 86400000 &&
      fim > inicio &&
      fim - inicio <= 12 * 3600000
    );
  }
  get inicio() {
    return this.#inicio;
  }
  get fim() {
    return this.#fim;
  }
}
window.SaborModels = {
  Usuario,
  Cliente,
  Cozinheiro,
  Administrador,
  Prato,
  ItemPedido,
  Carrinho,
  Pedido,
  Reserva,
};
Object.assign(window, window.SaborModels);
