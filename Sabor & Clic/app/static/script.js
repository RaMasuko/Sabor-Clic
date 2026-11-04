"use strict";
class AppController {
  #carrinho = new Carrinho();
  #cardapio = [];
  #chave = null;
  #assinatura = null;
  async init() {
    // Bind checkout before the first fetch, so slow requests cannot lose clicks.
    this.bindEvents();
    await this.carregarCardapio();
    if (document.getElementById("endereco-entrega"))
      try {
        const r = await SaborAPI.request("/api/perfil");
        document.getElementById("endereco-entrega").value =
          r.dados.endereco || "";
      } catch {
        // The address remains editable if the optional profile lookup fails.
      }
  }
  async carregarCardapio() {
    try {
      const res = await SaborAPI.request("/api/cardapio");
      this.#cardapio = res.dados.map((p) => new Prato(p));
      const container = document.getElementById("cardapio-container");
      container.replaceChildren();
      this.#cardapio.forEach((p) => {
        const c = SaborUI.el("article", undefined, "card");
        c.append(
          SaborUI.el("h3", p.nome, "card-title"),
          SaborUI.el("p", p.descricao),
          SaborUI.el("p", SaborUI.money(p.preco), "card-price"),
          SaborUI.el("p", `Estoque: ${p.estoque} porções`),
        );
        if (p.fichaTecnica)
          c.append(SaborUI.el("p", "Ficha técnica: " + p.fichaTecnica));
        const b = SaborUI.button("ADICIONAR", () => this.adicionarItem(p.id));
        b.dataset.pratoId = p.id;
        b.disabled = p.estoque < 1 || p.status !== "disponivel";
        if (container.dataset.cliente === "sim") c.append(b);
        container.append(c);
      });
      SaborUI.message(
        "mensagem-cardapio",
        this.#cardapio.length ? "" : "Nenhum prato disponível.",
      );
    } catch (e) {
      SaborUI.message("mensagem-cardapio", e.message, true);
    }
  }
  adicionarItem(id) {
    try {
      const p = this.#cardapio.find((p) => p.id === id);
      if (p) this.#carrinho.adicionarPrato(p);
      this.renderizarCarrinho();
      SaborUI.message("mensagem-pedido", "Item adicionado.");
    } catch (e) {
      SaborUI.message("mensagem-pedido", e.message, true);
    }
  }
  renderizarCarrinho() {
    const lista = document.getElementById("itens-carrinho");
    lista.replaceChildren();
    this.#carrinho.itens.forEach((i) => {
      const li = SaborUI.el("li");
      li.append(
        SaborUI.el("span", `${i.prato.nome} — ${SaborUI.money(i.subtotal)} `),
      );
      const q = document.createElement("input");
      q.type = "number";
      q.min = "1";
      q.max = Math.min(99, i.prato.estoque);
      q.value = i.quantidade;
      q.setAttribute("aria-label", "Quantidade de " + i.prato.nome);
      q.addEventListener("change", () => {
        try {
          this.#carrinho.alterarQuantidade(i.prato.id, Number(q.value));
          this.renderizarCarrinho();
        } catch (e) {
          q.value = i.quantidade;
          SaborUI.message("mensagem-pedido", e.message, true);
        }
      });
      li.append(
        q,
        SaborUI.button("Remover", () => {
          this.#carrinho.remover(i.prato.id);
          this.renderizarCarrinho();
        }),
      );
      lista.append(li);
    });
    document.getElementById("total-carrinho").textContent =
      "Total: " + SaborUI.money(this.#carrinho.total);
  }
  async finalizarPedido() {
    await SaborUI.action(
      document.getElementById("finalizar-pedido"),
      "mensagem-pedido",
      async () => {
        if (!this.#carrinho.itens.length)
          throw new Error("Seu carrinho está vazio!");
        const endereco = document
          .getElementById("endereco-entrega")
          .value.trim();
        if (!Pedido.validarEndereco(endereco))
          throw new Error(
            "Informe um endereço de entrega entre 5 e 200 caracteres.",
          );
        const payload = {
          itens: this.#carrinho.toJSON(),
          endereco_entrega: endereco,
        };
        const assinatura = JSON.stringify(payload);
        if (assinatura !== this.#assinatura) {
          this.#assinatura = assinatura;
          if (!globalThis.crypto?.getRandomValues) {
            throw new Error(
              "Use um navegador atualizado para enviar pedidos com segurança.",
            );
          }
          // Hexadecimal also works on HTTP localhost where randomUUID may be absent.
          const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16));
          this.#chave = Array.from(bytes, (byte) =>
            byte.toString(16).padStart(2, "0"),
          ).join("");
        }
        let r;
        try {
          r = await SaborAPI.request("/api/pedidos", {
            method: "POST",
            data: payload,
            headers: { "X-Idempotency-Key": this.#chave },
          });
        } catch (error) {
          await this.carregarCardapio();
          if (/estoque|versão|versao|indispon|alterad/i.test(error.message)) {
            throw new Error(
              error.message +
                " Remova os itens alterados do carrinho e adicione novamente pelo catálogo atualizado.",
            );
          }
          throw error;
        }
        const d = r.dados || r;
        this.#carrinho.limpar();
        this.#assinatura = null;
        this.renderizarCarrinho();
        SaborUI.message(
          "mensagem-pedido",
          `Pedido #${d.id_pedido} enviado! Total confirmado: ${SaborUI.money(d.valor_total)}. Acompanhe no perfil.`,
        );
        await this.carregarCardapio();
      },
    );
  }
  bindEvents() {
    document
      .getElementById("finalizar-pedido")
      ?.addEventListener("click", () => this.finalizarPedido());
  }
}
const appInstance = new AppController();
document.addEventListener("DOMContentLoaded", () => appInstance.init());
// Refresh menu availability without changing the cart's price/version snapshots.
setInterval(() => {
  if (!document.hidden) appInstance.carregarCardapio();
}, 30000);
function adicionarAoCarrinho(id) {
  appInstance.adicionarItem(id);
}
