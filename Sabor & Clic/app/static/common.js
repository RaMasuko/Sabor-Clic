"use strict";
window.SaborUI = {
  el(tag, text, cls) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  },
  money(value) {
    return Number(value).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  },
  date(value) {
    return value ? new Date(value).toLocaleString("pt-BR") : "Não definido";
  },
  message(id, text, error = false) {
    const e = document.getElementById(id);
    if (e) {
      e.textContent = text;
      e.className = error ? "error" : "success";
    }
  },
  async action(button, id, task) {
    if (button) button.disabled = true;
    this.message(id, "Processando…");
    try {
      await task();
    } catch (e) {
      this.message(id, e.message, true);
    } finally {
      if (button) button.disabled = false;
    }
  },
  button(text, action) {
    const b = this.el("button", text);
    b.type = "button";
    b.addEventListener("click", action);
    return b;
  },
};
document
  .getElementById("logout-form")
  ?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const b = form.querySelector("button");
    b.disabled = true;
    try {
      await SaborAPI.request("/api/logout", { method: "POST" });
      location.assign("/login");
    } catch (e) {
      b.disabled = false;
      let msg = form.querySelector("[role=status]");
      if (!msg) {
        msg = SaborUI.el("p");
        msg.setAttribute("role", "status");
        form.append(msg);
      }
      msg.textContent = e.message;
    }
  });
document.querySelectorAll("nav a").forEach((a) => {
  if (a.pathname === location.pathname) {
    a.classList.add("active");
    a.setAttribute("aria-current", "page");
  }
});
