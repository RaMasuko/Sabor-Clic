"use strict";
let pratosAdmin = [];
const pratoForm = document.getElementById("form-novo-prato");
function limparPrato() {
  pratoForm?.reset();
  if (pratoForm) {
    document.getElementById("prato-id").value = "";
    document.getElementById("versao").value = "";
  }
}
async function carregarCatalogo() {
  try {
    const r = await SaborAPI.request("/api/cardapio?todos=1");
    pratosAdmin = r.dados;
    const container = document.getElementById("catalogo-admin");
    container.replaceChildren();
    pratosAdmin.forEach((p) => {
      const card = SaborUI.el("article", undefined, "card");
      card.append(
        SaborUI.el("h3", p.nome),
        SaborUI.el(
          "p",
          `${SaborUI.money(p.preco)} · ${p.estoque} porções · ${p.status}`,
        ),
        SaborUI.el("p", p.descricao || ""),
        SaborUI.el(
          "p",
          "Ficha técnica: " + (p.ficha_tecnica || "Não informada"),
        ),
      );
      if (pratoForm) {
        card.append(
          SaborUI.button("Editar", () => {
            document.getElementById("prato-id").value = p.id;
            [
              "nome",
              "preco",
              "descricao",
              "estoque",
              "status",
              "versao",
              "ficha_tecnica",
            ].forEach((k) => (document.getElementById(k).value = p[k] ?? ""));
            pratoForm.scrollIntoView({ behavior: "smooth" });
            document.getElementById("nome").focus();
          }),
          SaborUI.button("Excluir", async (event) => {
            if (
              !confirm(
                "Excluir " +
                  p.nome +
                  " do catálogo? O histórico será preservado.",
              )
            )
              return;
            await SaborUI.action(event.currentTarget, "mensagem", async () => {
              await SaborAPI.request("/api/cardapio/" + p.id, {
                method: "DELETE",
                data: { versao: p.versao },
              });
              await carregarCatalogo();
              SaborUI.message("mensagem", "Prato excluído.");
            });
          }),
        );
      }
      container.append(card);
    });
    if (!r.dados.length)
      container.append(SaborUI.el("p", "Nenhum prato cadastrado."));
  } catch (e) {
    SaborUI.message("mensagem", e.message, true);
  }
}
pratoForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  SaborUI.action(pratoForm.querySelector("button"), "mensagem", async () => {
    const data = {};
    [
      "nome",
      "preco",
      "descricao",
      "estoque",
      "status",
      "ficha_tecnica",
    ].forEach((k) => (data[k] = document.getElementById(k).value));
    data.preco = Number(data.preco);
    data.estoque = Number(data.estoque);
    const id = document.getElementById("prato-id").value;
    if (id) data.versao = Number(document.getElementById("versao").value);
    await SaborAPI.request("/api/cardapio" + (id ? "/" + id : ""), {
      method: id ? "PUT" : "POST",
      data,
    });
    limparPrato();
    await carregarCatalogo();
    SaborUI.message("mensagem", "Prato salvo.");
  });
});
document
  .getElementById("cancelar-edicao")
  ?.addEventListener("click", limparPrato);
carregarCatalogo();
