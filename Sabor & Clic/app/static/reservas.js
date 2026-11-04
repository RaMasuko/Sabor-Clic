"use strict";
async function carregarBancadas() {
  const select = document.getElementById("id_bancada");
  try {
    const r = await SaborAPI.request("/api/bancadas");
    if (select) {
      select.replaceChildren();
      r.dados.forEach((b) => {
        const option = SaborUI.el("option", `${b.nome} — ${b.localizacao}`);
        option.value = b.id_bancada;
        select.append(option);
      });
      if (!r.dados.length) {
        const o = SaborUI.el("option", "Nenhuma bancada disponível");
        o.value = "";
        select.append(o);
      }
    }
  } catch (e) {
    SaborUI.message("mensagem-reservas", e.message, true);
  }
}
async function carregarReservas() {
  try {
    const r = await SaborAPI.request("/api/reservas");
    const list = document.getElementById("lista-reservas");
    list.replaceChildren();
    r.dados.forEach((v) => {
      const c = SaborUI.el("article", undefined, "card");
      c.append(
        SaborUI.el("h4", v.bancada),
        SaborUI.el("p", `${SaborUI.date(v.inicio)} até ${SaborUI.date(v.fim)}`),
        SaborUI.el("p", `Status: ${v.status}`),
      );
      if (v.cliente) c.append(SaborUI.el("p", v.cliente));
      if (v.status === "confirmada" && new Date(v.inicio) > new Date())
        c.append(
          SaborUI.button("Cancelar reserva", (event) =>
            SaborUI.action(
              event.currentTarget,
              "mensagem-reservas",
              async () => {
                await SaborAPI.request(`/api/reservas/${v.id_reserva}`, {
                  method: "DELETE",
                });
                await carregarReservas();
                SaborUI.message("mensagem-reservas", "Reserva cancelada.");
              },
            ),
          ),
        );
      list.append(c);
    });
    if (!r.dados.length)
      list.append(SaborUI.el("p", "Nenhuma reserva registrada."));
  } catch (e) {
    SaborUI.message("mensagem-reservas", e.message, true);
  }
}
document.getElementById("form-reserva")?.addEventListener("submit", (event) => {
  event.preventDefault();
  SaborUI.action(
    event.currentTarget.querySelector("button"),
    "mensagem-reservas",
    async () => {
      const reserva = new Reserva(
        document.getElementById("inicio").value,
        document.getElementById("fim").value,
      );
      await SaborAPI.request("/api/reservas", {
        method: "POST",
        data: {
          id_bancada: Number(document.getElementById("id_bancada").value),
          inicio: reserva.inicio,
          fim: reserva.fim,
        },
      });
      await carregarReservas();
      SaborUI.message("mensagem-reservas", "Reserva confirmada.");
    },
  );
});
document.getElementById("form-bancada")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  SaborUI.action(
    form.querySelector("button"),
    "mensagem-reservas",
    async () => {
      await SaborAPI.request("/api/bancadas", {
        method: "POST",
        data: Object.fromEntries(new FormData(form)),
      });
      form.reset();
      await carregarBancadas();
      SaborUI.message("mensagem-reservas", "Bancada cadastrada.");
    },
  );
});
document
  .getElementById("atualizar-reservas")
  ?.addEventListener("click", carregarReservas);
carregarBancadas();
carregarReservas();
