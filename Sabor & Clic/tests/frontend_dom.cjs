/* Fluxos HTTP + scripts reais em DOM de teste; não equivale a navegador visual. */
const { JSDOM, CookieJar, VirtualConsole } = require('jsdom');
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:5001';
const jar = new CookieJar();
const errors = [];
let current;
const checks = [];
async function http(path, options = {}) {
  const url = new URL(path, base).href;
  const headers = { ...options.headers, Cookie: jar.getCookieStringSync(url) };
  const res = await fetch(url, { ...options, headers, redirect: 'manual' });
  for (const cookie of res.headers.getSetCookie()) jar.setCookieSync(cookie, url);
  return res;
}
async function wait(condition, message) {
  for (let i = 0; i < 200; i++) {
    if (await condition()) return;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  throw new Error(message);
}
async function load(path) {
  current?.window.close();
  const res = await http(path);
  assert.equal(res.status, 200, `GET ${path}`);
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => {
    // O DOM não implementa navegação; o próximo GET é realizado pelo harness.
    if (!/Not implemented: navigation/.test(error.message)) errors.push(error.message);
  });
  current = new JSDOM(await res.text(), {
    url: new URL(path, base).href,
    runScripts: 'dangerously', resources: 'usable', cookieJar: jar, virtualConsole,
    beforeParse(window) {
      window.fetch = http;
      window.confirm = () => true;
      // Método de layout não implementado no DOM, sem substituir a lógica da tela.
      window.HTMLElement.prototype.scrollIntoView = function () {};
      window.console.error = (...args) => errors.push(args.join(' '));
    },
  });
  await new Promise(resolve => current.window.addEventListener('load', resolve, { once: true }));
  return current.window.document;
}
async function login(email) {
  const page = await http('/login');
  const html = await page.text();
  const token = html.match(/name="csrf-token"\s+content="([^"]+)"/)[1];
  const res = await http('/api/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
    body: JSON.stringify({ email, senha: 'TesteSeguro123!' }),
  });
  assert.equal(res.status, 200, `Login ${email}: ${await res.clone().text()}`);
}
function submit(doc, selector) {
  doc.querySelector(selector).dispatchEvent(new current.window.Event('submit', { bubbles: true, cancelable: true }));
}
function button(scope, label) {
  const found = [...scope.querySelectorAll('button')].find(b => b.textContent.trim() === label);
  assert.ok(found, `Botão ${label} ausente`);
  return found;
}
function localDate(date) {
  const pad = n => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
(async () => {
  try {
    // As telas públicas não oferecem compra com perfil inadequado.
    let doc = await load('/');
    assert.equal(doc.getElementById('finalizar-pedido'), null);
    checks.push('visitante sem checkout');

    await login('admin.browser@teste.com');
    doc = await load('/adicionar-prato');
    const name = '<img src=x onerror="window.invaded=true">';
    doc.getElementById('nome').value = name;
    doc.getElementById('preco').value = '25.50';
    doc.getElementById('estoque').value = '4';
    doc.getElementById('descricao').value = 'Prato de teste.';
    doc.getElementById('ficha_tecnica').value = 'Porção de 300g.';
    submit(doc, '#form-novo-prato');
    await wait(() => doc.getElementById('mensagem').textContent.includes('salvo'), 'Cadastro do prato falhou');
    button(doc.querySelector('#catalogo-admin article'), 'Editar').click();
    doc.getElementById('preco').value = '26.50';
    submit(doc, '#form-novo-prato');
    await wait(() => doc.getElementById('mensagem').textContent.includes('salvo') && !doc.getElementById('prato-id').value, 'Edição do prato falhou');
    checks.push('CRUD administrativo com estoque e ficha técnica');

    await login('browser@teste.com');
    doc = await load('/');
    await wait(() => doc.querySelector('[data-prato-id]'), 'Cardápio não carregou');
    await wait(() => doc.getElementById('endereco-entrega').value.includes('123'), 'Endereço não foi carregado');
    doc.querySelector('[data-prato-id]').click();
    doc.querySelector('[data-prato-id]').click();
    assert.ok(doc.getElementById('itens-carrinho').textContent.includes(name));
    assert.equal(doc.querySelector('#itens-carrinho img'), null);
    doc.getElementById('finalizar-pedido').click();
    await wait(() => doc.getElementById('mensagem-pedido').textContent.includes('53,00'), 'Pedido não confirmado: ' + doc.getElementById('mensagem-pedido').textContent);
    checks.push('carrinho e compra por fetch com total do servidor');

    doc = await load('/perfil');
    await wait(() => doc.getElementById('meus-pedidos').textContent.includes('Pedido #1'), 'Histórico não carregou');
    await wait(() => doc.getElementById('nome').value.length > 0, 'Perfil não carregou');
    doc.getElementById('endereco').value = 'Rua Atualizada, 456';
    submit(doc, '#form-perfil');
    await wait(() => doc.getElementById('mensagem-perfil').textContent.includes('atualizado'), 'Perfil não salvou');
    assert.equal(doc.querySelector('#meus-pedidos img'), null);
    checks.push('perfil, endereço e histórico protegido');

    const inicio = localDate(new Date(Date.now() + 24*3600000));
    const fim = localDate(new Date(Date.now() + 26*3600000));
    doc = await load('/reservas');
    await wait(() => doc.getElementById('id_bancada').value, 'Bancadas não carregaram');
    doc.getElementById('inicio').value = inicio;
    doc.getElementById('fim').value = fim;
    submit(doc, '#form-reserva');
    await wait(() => doc.getElementById('mensagem-reservas').textContent.includes('confirmada'), 'Reserva não confirmou');

    await login('outro@teste.com');
    doc = await load('/perfil');
    await wait(() => doc.getElementById('mensagem-pedidos').textContent.includes('ainda não'), 'Histórico de outro cliente exposto');
    doc = await load('/reservas');
    await wait(() => doc.getElementById('id_bancada').value, 'Bancadas não carregaram');
    assert.equal(doc.querySelector('#lista-reservas article'), null);
    doc.getElementById('inicio').value = inicio;
    doc.getElementById('fim').value = fim;
    submit(doc, '#form-reserva');
    await wait(() => doc.getElementById('mensagem-reservas').className === 'error', 'Conflito de reserva não bloqueado');
    await login('browser@teste.com');
    doc = await load('/reservas');
    await wait(() => doc.querySelector('#lista-reservas article button'), 'Reserva própria não apareceu');
    button(doc.querySelector('#lista-reservas'), 'Cancelar reserva').click();
    await wait(() => doc.getElementById('mensagem-reservas').textContent.includes('cancelada'), 'Cancelamento não funcionou');
    checks.push('reservas reais, isolamento, conflito e cancelamento por DELETE');

    await login('cozinha.browser@teste.com');
    doc = await load('/kds');
    await wait(() => doc.querySelector('.card-pedido'), 'KDS não carregou');
    assert.ok(doc.querySelector('.card-pedido').textContent.includes(name));
    assert.equal(doc.querySelector('.card-pedido img'), null);
    assert.equal(current.window.invaded, undefined);
    doc.getElementById('estimativa-1').value = '30';
    submit(doc, '.card-pedido form');
    await wait(() => doc.querySelector('.card-pedido').textContent.includes('Previsão'), 'Estimativa não apareceu');
    button(doc.querySelector('.card-pedido'), 'Iniciando Preparo').click();
    await wait(() => [...doc.querySelectorAll('.card-pedido button')].some(b => b.textContent === 'Pronto para Entrega'), 'Primeiro status não atualizou');
    button(doc.querySelector('.card-pedido'), 'Pronto para Entrega').click();
    await wait(() => !doc.querySelector('.card-pedido'), 'Pedido pronto não saiu da fila pendente');
    checks.push('KDS, estimativa, status e saída literal de HTML');

    await login('admin.browser@teste.com');
    doc = await load('/relatorios');
    await wait(() => doc.getElementById('relatorios').textContent.includes('53,00'), 'Relatórios não carregaram vendas');
    assert.ok(doc.getElementById('relatorios').textContent.includes('Estoque'));
    checks.push('relatórios de vendas, estoque e ocupação');
    doc = await load('/adicionar-prato');
    await wait(() => doc.querySelector('#catalogo-admin article'), 'Catálogo admin não carregou');
    button(doc.querySelector('#catalogo-admin article'), 'Excluir').click();
    await wait(() => !doc.querySelector('#catalogo-admin article'), 'Exclusão lógica por DELETE falhou');
    checks.push('exclusão lógica sem perder histórico');

    doc = await load('/funcionarios/novo');
    for (const [key,value] of Object.entries({nome:'Chef Novo',email:'chef.novo@teste.com',cpf:'33333333333',senha:'TesteSeguro123!',perfil:'cozinheiro',turno:'Noite',especialidade:'Massas'})) {
      doc.querySelector(`[name="${key}"]`).value = value;
    }
    submit(doc, '#auth-form');
    await wait(() => doc.getElementById('mensagem-auth').textContent.includes('sucesso'), 'Cadastro da equipe falhou');
    checks.push('cadastro de equipe por JSON');

    // Testar o próprio script de login, inclusive token renovado e navegação desejada.
    doc = await load('/login');
    doc.querySelector('[name=email]').value = 'browser@teste.com';
    doc.querySelector('[name=senha]').value = 'errada';
    submit(doc, '#auth-form');
    await wait(() => doc.getElementById('mensagem-auth').className === 'error', 'Falha do login não tratada');
    doc.querySelector('[name=senha]').value = 'TesteSeguro123!';
    submit(doc, '#auth-form');
    await wait(() => doc.getElementById('mensagem-auth').textContent.includes('sucesso'), 'Login JSON não funcionou');
    doc = await load('/perfil');
    await wait(() => doc.getElementById('meus-pedidos').textContent.includes('Pronto para Entrega'), 'Histórico final não preservado');
    submit(doc, '#logout-form');
    await wait(async () => (await http('/api/perfil')).status === 401, 'Logout não revogou a sessão');
    checks.push('login JSON com erro/sucesso e logout revogável');
    assert.deepEqual(errors, []);
    console.log(`PASS DOM: ${checks.length} fluxos integrados: ${checks.join('; ')}.`);
  } finally {
    current?.window.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
