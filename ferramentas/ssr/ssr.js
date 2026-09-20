// SSR da primeira tela (20/09/2026). Le o HTML montado pelo publicador no
// stdin, roda O PROPRIO SCRIPT da pagina num DOM de mentira (jsdom) e devolve
// no stdout o mesmo HTML com prova, chips, vitrine e os primeiros cartoes ja
// dentro — o que o Safari pinta antes de o script grande chegar.
//
// Por que assim e nao em Python: o cartao existiria em dois lugares e todo
// ajuste teria de ser feito duas vezes, identicas. Aqui o markup vem do
// mesmo codigo que roda no telefone; o script vivo troca ao chegar
// (montarProva limpa as celas, montarChips/desenhar limpam as caixas).
//
// Uso: node ssr.js < entrada.html > saida.html   (falhou = exit 1, sem saida)
"use strict";
const { JSDOM, VirtualConsole } = require("jsdom");

const CARTOES = 8;

function lerTudo() {
  return new Promise((res) => {
    const partes = [];
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (d) => partes.push(d));
    process.stdin.on("end", () => res(partes.join("")));
  });
}

// o cartao vivo tem <a> dentro de <a> (feito via DOM); o parser de HTML nao
// aceita. A copia e' so' visual: links internos viram <span>.
function inerte(win, n) {
  const c = n.cloneNode(true);
  for (const a of c.querySelectorAll("a")) {
    const s = win.document.createElement("span");
    s.className = a.className; s.innerHTML = a.innerHTML;
    a.parentNode.replaceChild(s, a);
  }
  for (const cv of c.querySelectorAll("canvas")) { cv.remove(); }
  return c.outerHTML;
}

async function main() {
  const html = await lerTudo();
  if (!html.includes('id="grade"')) { throw new Error("entrada sem #grade"); }

  const vc = new VirtualConsole();
  const erros = [];
  vc.on("jsdomError", (e) => { if (!/not implemented/i.test(String(e.message))) { erros.push(String(e.message)); } });
  vc.on("error", (m) => erros.push(String(m)));

  const dom = new JSDOM(html, {
    url: "https://achadinhototal.com.br/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
    virtualConsole: vc,
  });
  const win = dom.window;
  // o que o jsdom nao tem e a pagina usa (tudo guardado ou irrelevante aqui)
  // reduced-motion = SIM: os numeros da prova contam 700 ms ate' o valor
  // final e a captura pegava o meio da contagem (1.324 no lugar de 1.666).
  win.matchMedia = (q) => ({ matches: /reduced-motion/.test(String(q)), media: String(q), addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  win.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };
  win.fetch = () => Promise.reject(new Error("ssr: sem rede"));
  win.HTMLCanvasElement.prototype.getContext = () => null;
  win.scrollTo = () => {};
  win.requestIdleCallback = (f) => win.setTimeout(f, 0);

  // executa os scripts inline na ordem do documento (runScripts outside-only
  // nao roda os <script> do HTML sozinho: assim controlamos o que roda)
  const scripts = Array.from(win.document.querySelectorAll("script"));
  for (const s of scripts) {
    if (s.src) { continue; }
    if (s.type && s.type !== "text/javascript" && s.type !== "module") { continue; }
    try { win.eval(s.textContent); } catch (e) { erros.push("script: " + (e && e.stack || e)); }
  }
  // deixa timers curtos (a pagina monta sincrono; o herois digitando usa rAF)
  await new Promise((r) => win.setTimeout(r, 1000));

  const q = (id) => win.document.getElementById(id);
  const prova = q("prova"), chips = q("chips"), vit = q("vitrine"), grade = q("grade");
  const celas = prova ? Array.from(prova.querySelectorAll(".cela, .fim")).map((n) => inerte(win, n)).join("") : "";
  const chipsHtml = chips ? Array.from(chips.children).map((n) => inerte(win, n)).join("") : "";
  const vitHtml = vit ? Array.from(vit.children).map((n) => inerte(win, n)).join("") : "";
  const cartoes = grade ? Array.from(grade.querySelectorAll(":scope > .item")).slice(0, CARTOES).map((n) => inerte(win, n)).join("") : "";
  const n = grade ? grade.querySelectorAll(":scope > .item").length : 0;

  if (!cartoes || !chipsHtml || !celas) {
    throw new Error(`ssr: montou pouco (celas=${celas.length} chips=${chipsHtml.length} cartoes=${n})` + (erros.length ? "\n" + erros.join("\n") : ""));
  }

  // cola no HTML ORIGINAL (texto), nao no DOM do jsdom: o jsdom reescreveria o
  // documento inteiro (entidades, atributos) e o carimbo e' do byte.
  let saida = html;
  const troca = (alvo, novo) => {
    if (saida.indexOf(alvo) < 0) { throw new Error("ssr: marcador sumiu -> " + alvo); }
    saida = saida.replace(alvo, novo);
  };
  troca('<div class="prova" id="prova"><div class="economia" id="economia" hidden></div></div>',
        '<div class="prova" id="prova"><div class="economia" id="economia" hidden></div>' + celas + '</div>');
  troca('<div class="filtros" id="chips"></div>', '<div class="filtros" id="chips">' + chipsHtml + '</div>');
  troca('<div id="vitrine"></div>', '<div id="vitrine">' + vitHtml + '</div>');
  troca('<div class="grade" id="grade"></div>', '<div class="grade" id="grade">' + cartoes + '</div>');

  // ⭐ O TOPO TAMBEM (20/09/2026, video do Bryan as 02:24). O SSR cobria
  // prova, chips, vitrine e cartoes — e deixava de fora as DUAS coisas mais
  // altas da pagina: o brasao (`#logo`) e a linha viva (`#vivo`), ambas
  // escritas pelo motor. MEDIDO no video: com o motor agora em `defer`, a
  // primeira pintura sai cedo e correta, mas com dois buracos no cabecalho
  // — o espaco ja' reservado, sem conteudo — ate' o motor chegar. Era a
  // piscada que sobrou.
  //
  // ⚠️ O `<a class="vivo">` VAI COM OS ATRIBUTOS DE DEPOIS, href inclusive:
  // o link do topo e' um dos poucos que continuam embutidos no HTML, e sem
  // ele a primeira tela teria um produto que nao abre.
  // Repintar por cima nao duplica: `animarVivo` escreve por innerHTML/texto
  // nos mesmos tres spans (diferente de `montarProva`, que anexa celas).
  const logo = q("logo"), vivo = q("vivo");
  if (logo && logo.children.length) {
    // ⚠️ `decoding="sync"`: o brasao e' um data: URI de 86 px ja' dentro do
    // HTML; sem isto o Safari pode pintar a pagina e decodificar depois, que
    // e' exatamente o buraco redondo do video.
    troca('<span class="marca-logo" id="logo"></span>',
          inerte(win, logo).replace("<img ", '<img decoding="sync" fetchpriority="high" '));
  }
  if (vivo && !vivo.hidden) {
    // ⛔ `data-mede` NAO VAI JUNTO. `animarVivo` usa esse atributo como
    // "ja' liguei o clique aqui" (`if (!alvo.dataset.mede)`). Congelado no
    // HTML, o motor pularia a linha e o produto do topo — o mais visivel da
    // pagina — ficaria para sempre sem o registro do clique. Defeito que nao
    // aparece na tela: o link abre igual, so' a medicao some.
    const atrs = Array.from(vivo.attributes)
      .filter((a) => a.name !== "data-mede")
      .map((a) => ` ${a.name}="${String(a.value).replace(/"/g, "&quot;")}"`).join("");
    troca('<a class="vivo" id="vivo" rel="noopener">', "<a" + atrs + ">");
    // ⭐ `vivo_cta` entra junto (20/09): a pilula "Comprar agora" e' a
    // affordance do topo; se ela so' aparecesse com o motor, a primeira
    // tela voltaria a ter um buraco — o defeito que o SSR existe pra evitar.
    for (const id of ["vivo_nome", "vivo_preco", "vivo_dica", "vivo_cta"]) {
      const e = q(id);
      const vazio = `<span class="${id.replace("_", "-")}" id="${id}"></span>`;
      if (e && e.innerHTML && saida.indexOf(vazio) >= 0) { troca(vazio, inerte(win, e)); }
    }
  }

  process.stderr.write(`ssr: ${celas.split('class="cela').length - 1} celas, ${chipsHtml.length} B de chips, vitrine ${vitHtml ? "sim" : "nao"}, ${Math.min(n, CARTOES)} de ${n} cartoes` + (erros.length ? ` (avisos: ${erros.length})` : "") + "\n");
  if (erros.length) { process.stderr.write(erros.slice(0, 5).join("\n") + "\n"); }
  process.stdout.write(saida);
  win.close();
}

main().catch((e) => { process.stderr.write(String(e && e.stack || e) + "\n"); process.exit(1); });
