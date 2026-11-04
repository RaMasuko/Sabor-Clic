"use strict";
const containerKDS = document.getElementById("pedidos-container");
let carregandoKDS = false;
async function carregarKDS() {
  if (carregandoKDS) return;
  carregandoKDS = true;
  try {
    const r = await SaborAPI.request("/api/pedidos?pendentes=1");
    containerKDS.replaceChildren();
    r.dados.forEach((p) => {
      const c = SaborUI.el("article", undefined, "card-pedido");
      c.append(
        SaborUI.el("h3", `Pedido #${p.id_pedido} — ${p.cliente}`),
        SaborUI.el("p", p.status),
        SaborUI.el("p", `Recebido: ${SaborUI.date(p.data)}`),
        SaborUI.el("p", `Entrega: ${p.endereco_entrega}`),
      );
      const ul = SaborUI.el("ul");
      p.itens.forEach((i) =>
        ul.append(SaborUI.el("li", `${i.quantidade}× ${i.nome}`)),
      );
      c.append(ul);
      if (p.data_previsao)
        c.append(SaborUI.el("p", "Previsão: " + SaborUI.date(p.data_previsao)));
      const form = SaborUI.el("form");
      const label = SaborUI.el("label", "Tempo estimado (minutos)");
      const input = document.createElement("input");
      input.type = "number";
      input.min = "1";
      input.max = "1440";
      input.required = true;
      input.value = p.tempo_estimado_min || "";
      input.id = "estimativa-" + p.id_pedido;
      label.htmlFor = input.id;
      const save = SaborUI.el("button", "Salvar estimativa");
      save.type = "submit";
      form.append(label, input, save);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        SaborUI.action(save, "mensagem-kds", async () => {
          await SaborAPI.request(`/api/pedidos/${p.id_pedido}/estimativa`, {
            method: "PUT",
            data: { minutos: Number(input.value) },
          });
          await carregarKDS();
          SaborUI.message("mensagem-kds", "Estimativa atualizada.");
        });
      });
      c.append(form);
      const next = {
        Aguardando: "Iniciando Preparo",
        "Iniciando Preparo": "Pronto para Entrega",
      }[p.status];
      if (next)
        c.append(
          SaborUI.button(next, async (event) => {
            await SaborUI.action(
              event.currentTarget,
              "mensagem-kds",
              async () => {
                await SaborAPI.request(`/api/pedidos/${p.id_pedido}/status`, {
                  method: "PUT",
                  data: { status: next },
                });
                await carregarKDS();
                SaborUI.message("mensagem-kds", "Status atualizado.");
              },
            );
          }),
        );
      containerKDS.append(c);
    });
    SaborUI.message(
      "mensagem-kds",
      r.dados.length
        ? "Fila atualizada automaticamente a cada 5 segundos."
        : "Nenhum pedido pendente.",
    );
  } catch (e) {
    SaborUI.message("mensagem-kds", e.message, true);
  } finally {
    carregandoKDS = false;
  }
}
document
  .getElementById("atualizar-kds")
  ?.addEventListener("click", carregarKDS);
carregarKDS();
setInterval(() => {
  if (!document.hidden && !containerKDS.contains(document.activeElement))
    carregarKDS();
}, 5000);
