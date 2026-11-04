"use strict";
window.SaborAPI = {
  async request(url, { method = "GET", data, headers = {} } = {}) {
    const all = { Accept: "application/json", ...headers };
    if (!["GET", "HEAD"].includes(method.toUpperCase()))
      all["X-CSRFToken"] =
        document.querySelector('meta[name="csrf-token"]')?.content || "";
    if (data !== undefined) all["Content-Type"] = "application/json";
    const response = await fetch(url, {
      method,
      headers: all,
      credentials: "same-origin",
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    let result;
    try {
      result = await response.json();
    } catch {
      throw new Error("Resposta inválida do servidor. Tente novamente.");
    }
    // Authentication may rotate the token even when credentials are rejected.
    if (result.csrf_token) {
      const meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) meta.content = result.csrf_token;
      document
        .querySelectorAll('[name="csrf_token"]')
        .forEach((input) => (input.value = result.csrf_token));
    }
    if (!response.ok || !result.sucesso)
      throw new Error(
        result.mensagem ||
          result.erro ||
          "Não foi possível concluir a operação.",
      );
    return result;
  },
};
