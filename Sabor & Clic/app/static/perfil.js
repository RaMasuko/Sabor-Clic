"use strict";
let carregandoPedidos = false;
async function carregarMeusPedidos() {
  const container = document.getElementById("meus-pedidos");
  if (!container || carregandoPedidos) return;
  carregandoPedidos = true;
  try {
    const r = await SaborAPI.request("/api/pedidos");
    container.replaceChildren();
    r.dados.forEach((p) => {
      const c = SaborUI.el("article", undefined, "card");
      c.append(
        SaborUI.el("h4", `Pedido #${p.id_pedido} — ${p.status}`),
        SaborUI.el(
          "p",
          `${SaborUI.date(p.data)} · ${SaborUI.money(p.valor_total)}`,
        ),
        SaborUI.el("p", "Entrega: " + p.endereco_entrega),
        SaborUI.el(
          "p",
          p.tempo_estimado_min
            ? `Estimativa: ${p.tempo_estimado_min} minutos · previsão ${SaborUI.date(p.data_previsao)}`
            : "Estimativa ainda não definida.",
        ),
      );
      const ul = SaborUI.el("ul");
      p.itens.forEach((i) =>
        ul.append(
          SaborUI.el(
            "li",
            `${i.quantidade}× ${i.nome} — ${SaborUI.money(i.preco_unitario)}`,
          ),
        ),
      );
      c.append(ul);
      container.append(c);
    });
    SaborUI.message(
      "mensagem-pedidos",
      r.dados.length
        ? "Atualizado automaticamente a cada 10 segundos."
        : "Você ainda não tem pedidos.",
    );
  } catch (e) {
    SaborUI.message("mensagem-pedidos", e.message, true);
  } finally {
    carregandoPedidos = false;
  }
}
async function carregarPerfil() {
  try {
    const r = await SaborAPI.request("/api/perfil");
    const p = r.dados;
    document.getElementById("perfil-email").textContent = "E-mail: " + p.email;
    document.getElementById("perfil-tipo").textContent = "Perfil: " + p.perfil;
    ["nome", "endereco", "turno", "especialidade"].forEach(
      (k) => (document.getElementById(k).value = p[k] || ""),
    );
    document.getElementById("campos-cliente").hidden = p.perfil !== "cliente";
    document.getElementById("campos-equipe").hidden = p.perfil === "cliente";
    document.getElementById("endereco").disabled = p.perfil !== "cliente";
    ["turno", "especialidade"].forEach((campo) => {
      const input = document.getElementById(campo);
      input.disabled = p.perfil === "cliente";
      input.required = p.perfil === "cozinheiro";
    });
    document.getElementById("form-perfil").dataset.perfil = p.perfil;
  } catch (e) {
    SaborUI.message("mensagem-perfil", e.message, true);
  }
}
document.getElementById("form-perfil")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const f = event.currentTarget;
  SaborUI.action(f.querySelector("button"), "mensagem-perfil", async () => {
    const keys =
      f.dataset.perfil === "cliente"
        ? ["nome", "endereco"]
        : ["nome", "turno", "especialidade"];
    const data = Object.fromEntries(
      keys.map((k) => [k, document.getElementById(k).value]),
    );
    await SaborAPI.request("/api/perfil", { method: "PUT", data });
    SaborUI.message("mensagem-perfil", "Perfil atualizado.");
  });
});
document
  .getElementById("atualizar-pedidos")
  ?.addEventListener("click", carregarMeusPedidos);
carregarPerfil();
carregarMeusPedidos();
setInterval(() => {
  if (!document.hidden) carregarMeusPedidos();
}, 10000);
