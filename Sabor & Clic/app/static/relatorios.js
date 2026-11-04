"use strict";
function tabela(titulo, colunas, linhas) {
  const section = SaborUI.el("section", undefined, "card");
  section.append(SaborUI.el("h3", titulo));
  if (!linhas.length) {
    section.append(SaborUI.el("p", "Sem registros."));
    return section;
  }
  const wrap = SaborUI.el("div", undefined, "table-wrap"),
    table = SaborUI.el("table"),
    head = SaborUI.el("thead"),
    tr = SaborUI.el("tr");
  colunas.forEach(([nome]) => {
    const th = SaborUI.el("th", nome);
    th.scope = "col";
    tr.append(th);
  });
  head.append(tr);
  table.append(head);
  const body = SaborUI.el("tbody");
  linhas.forEach((l) => {
    const row = SaborUI.el("tr");
    colunas.forEach(([, key, format]) =>
      row.append(
        SaborUI.el("td", format ? format(l[key]) : String(l[key] ?? "")),
      ),
    );
    body.append(row);
  });
  table.append(body);
  wrap.append(table);
  section.append(wrap);
  return section;
}
async function carregarRelatorios() {
  await SaborUI.action(
    document.getElementById("atualizar-relatorios"),
    "mensagem-relatorios",
    async () => {
      const r = await SaborAPI.request("/api/relatorios");
      const d = r.dados,
        container = document.getElementById("relatorios");
      container.replaceChildren(
        SaborUI.el(
          "p",
          `${d.totais.pedidos} pedidos · ${SaborUI.money(d.totais.faturamento)} em vendas · ${d.totais.reservas} reservas`,
        ),
        tabela(
          "Vendas",
          [
            ["Data", "data"],
            ["Pedidos", "pedidos"],
            ["Faturamento", "faturamento", SaborUI.money],
          ],
          d.vendas,
        ),
        tabela(
          "Estoque (porções)",
          [
            ["Prato", "nome"],
            ["Porções", "estoque"],
            ["Status", "status"],
          ],
          d.estoque,
        ),
        tabela(
          "Ocupação das bancadas",
          [
            ["Bancada", "nome"],
            ["Reservas", "reservas"],
            ["Minutos reservados", "minutos_reservados"],
          ],
          d.ocupacao,
        ),
      );
      SaborUI.message("mensagem-relatorios", "Relatórios atualizados.");
    },
  );
}
document
  .getElementById("atualizar-relatorios")
  ?.addEventListener("click", carregarRelatorios);
carregarRelatorios();
