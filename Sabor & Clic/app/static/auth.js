"use strict";
const authForm = document.getElementById("auth-form");
authForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  SaborUI.action(
    authForm.querySelector("button"),
    "mensagem-auth",
    async () => {
      const data = Object.fromEntries(new FormData(authForm));
      delete data.csrf_token;
      if (data.nome) new Usuario(data.nome, data.email);
      const r = await SaborAPI.request(authForm.dataset.api, {
        method: "POST",
        data,
      });
      SaborUI.message("mensagem-auth", r.mensagem || "Operação concluída.");
      if (authForm.dataset.api === "/api/funcionarios") authForm.reset();
      else
        location.assign(
          r.destino ||
            (authForm.dataset.api === "/api/cadastro" ? "/login" : "/"),
        );
    },
  );
});
