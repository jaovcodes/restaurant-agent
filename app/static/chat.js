/*!
 * Sabor & Arte: chat de cardápio e reservas, com a assistente Lucia.
 *
 * Em qualquer site (botão flutuante no canto da tela):
 *   <script src="https://SEU-SERVIDOR/static/chat.js"
 *           data-api="https://SEU-SERVIDOR" defer></script>
 *
 * Embutido em uma página (como no index.html deste projeto):
 *   <div id="sabor-arte-chat"></div>
 *   <script src="/static/chat.js" data-modo="embutido"
 *           data-alvo="#sabor-arte-chat" defer></script>
 *
 * Atributos:
 *   data-api        endereço do servidor (vazio = mesmo domínio da página)
 *   data-modo       "flutuante" (padrão) ou "embutido"
 *   data-alvo       seletor do elemento onde embutir (só no modo embutido)
 *   data-nome       nome do restaurante (padrão: Sabor & Arte)
 *   data-assistente nome da assistente (padrão: Lucia)
 *
 * Usa Shadow DOM: o CSS do site não altera o chat e o CSS do chat não altera o site.
 */
(function () {
  "use strict";

  const script = document.currentScript;
  const dados = script ? script.dataset : {};
  const config = {
    api: (dados.api || "").replace(/\/+$/, ""),
    modo: dados.modo === "embutido" ? "embutido" : "flutuante",
    alvo: dados.alvo || "#sabor-arte-chat",
    nome: dados.nome || "Sabor & Arte",
    assistente: dados.assistente || "Lucia",
  };

  const FONTES =
    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500" +
    "&family=Hanken+Grotesk:wght@400;500;600&display=swap";

  // Ícone da assistente: silhueta simples, usa a cor do texto (currentColor).
  const ICONE =
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">' +
    '<path fill-rule="evenodd" d="M12 3C7.9 3 5.4 5.8 5.4 9.6c0 2.3-.4 4-1.5 5.6 1.5.5 3.1.1 4.3-1V9.9' +
    "c0-2 1.4-3.5 3.8-3.5s3.8 1.5 3.8 3.5v4.3c1.2 1.1 2.8 1.5 4.3 1-1.1-1.6-1.5-3.3-1.5-5.6" +
    'C18.6 5.8 16.1 3 12 3Z"/>' +
    '<circle cx="12" cy="10.1" r="2.5"/>' +
    '<path d="M5.4 21c.7-2.6 3.3-4.1 6.6-4.1s5.9 1.5 6.6 4.1Z"/></svg>';

  const SUGESTOES = [
    ["Ver o cardápio", "Quero ver o cardápio"],
    ["Horários", "Quais são os horários de funcionamento?"],
    ["Reservar uma mesa", "Quero reservar uma mesa"],
  ];

  const CSS = `
    :host { all: initial; display: block; }
    *, *::before, *::after { box-sizing: border-box; }

    .app {
      /* Corta toda herança vinda do site que hospeda o chat
         (text-transform, letter-spacing etc.). Tem de vir antes do resto. */
      all: initial;
      display: block;
      --vinho: #3b1521;
      --vinho-medio: #5b2436;
      --papel: #fafaf8;
      --tinta: #2a2226;
      --cinza: #6f6569;
      --linha: #ded9db;
      --latao: #9a7433;
      --rosado: #efe4e7;
      --alerta: #a4372a;
      --serifa: "Cormorant Garamond", Georgia, "Times New Roman", serif;
      font-family: "Hanken Grotesk", system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 16px;
      line-height: 1.55;
      color: var(--tinta);
    }

    button, input { font: inherit; }
    button:focus-visible, input:focus-visible {
      outline: 2px solid var(--vinho);
      outline-offset: 2px;
    }

    svg { display: block; }

    /* ---------- estrutura comum ---------- */
    .painel { display: flex; flex-direction: column; background: var(--papel); }

    /* ---------- cabeçalho com a Lucia ---------- */
    .topo {
      flex: none;
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 16px 20px;
    }

    .avatar {
      flex: none;
      width: 48px;
      height: 48px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      background: var(--rosado);
      color: var(--vinho);
      box-shadow: 0 0 0 1px var(--latao);
    }
    .avatar svg { width: 30px; height: 30px; }

    .identidade { flex: 1; min-width: 0; display: flex; flex-direction: column; }

    .quem {
      font-family: var(--serifa);
      font-weight: 600;
      font-size: 30px;
      line-height: 1;
    }

    .subtitulo { margin-top: 5px; font-size: 13px; color: var(--cinza); }

    .fechar {
      background: none;
      border: 0;
      border-radius: 4px;
      color: var(--papel);
      font-size: 28px;
      line-height: 1;
      padding: 2px 10px 6px;
      cursor: pointer;
    }
    .fechar:hover { background: rgba(255, 255, 255, 0.14); }
    .fechar:focus-visible { outline-color: var(--papel); }

    /* ---------- conversa ---------- */
    .conversa {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
      padding: 28px max(20px, calc((100% - 640px) / 2));
    }

    .abertura .ola {
      margin: 0 0 10px;
      font-family: var(--serifa);
      font-weight: 500;
      font-size: 38px;
      line-height: 1.05;
      color: var(--vinho);
    }
    .abertura .apoio { margin: 0 0 20px; max-width: 48ch; color: var(--cinza); }

    .sugestoes { display: flex; flex-wrap: wrap; gap: 8px; }

    .sugestoes button {
      background: transparent;
      color: var(--vinho);
      border: 1px solid var(--vinho);
      border-radius: 4px;
      padding: 9px 16px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }
    .sugestoes button:hover { background: var(--vinho); color: var(--papel); }

    /* ---------- mensagens ---------- */
    .msg.cliente {
      align-self: flex-end;
      max-width: 85%;
      background: var(--rosado);
      padding: 10px 14px;
      border-radius: 6px 6px 2px 6px;
      overflow-wrap: anywhere;
    }

    .msg.assistente {
      align-self: stretch;
      padding-left: 16px;
      border-left: 2px solid var(--latao);
    }
    .msg.assistente.erro { border-left-color: var(--alerta); }

    .rotulo { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
    .rotulo svg { width: 18px; height: 18px; flex: none; color: var(--vinho); }
    .rotulo span {
      font-family: var(--serifa);
      font-style: italic;
      font-weight: 500;
      font-size: 19px;
      line-height: 1;
      color: var(--cinza);
    }

    .corpo p { margin: 0 0 8px; }
    .corpo p:last-child { margin-bottom: 0; }
    .corpo strong { font-weight: 600; }

    .corpo ul.lista { margin: 4px 0 8px; padding-left: 20px; }
    .corpo ul.lista li { margin-bottom: 2px; }

    /* títulos de seção (categorias do cardápio, "Reserva confirmada" etc.) */
    .corpo .secao {
      margin: 18px 0 6px;
      font-family: var(--serifa);
      font-weight: 600;
      font-size: 24px;
      line-height: 1.15;
      color: var(--vinho);
    }
    .corpo .secao:first-child { margin-top: 0; }
    .corpo .secao::after {
      content: "";
      display: block;
      width: 28px;
      height: 1px;
      margin-top: 6px;
      background: var(--latao);
    }

    /* cardápio: nome ...... preço, como num menu impresso */
    .corpo ul.cardapio { list-style: none; margin: 0 0 6px; padding: 0; }
    .prato { display: flex; align-items: baseline; gap: 8px; padding: 3px 0; }
    .prato .nome { min-width: 0; font-weight: 500; }
    .prato .fio {
      flex: 1;
      min-width: 12px;
      border-bottom: 1px dotted #b3a6ab;
      transform: translateY(-3px);
    }
    .prato .preco {
      font-family: var(--serifa);
      font-weight: 600;
      font-size: 20px;
      line-height: 1;
      color: var(--vinho);
      white-space: nowrap;
      font-variant-numeric: lining-nums tabular-nums;
    }

    .bastidores { margin-top: 12px; font-size: 13px; color: var(--cinza); }
    .bastidores summary { cursor: pointer; color: var(--vinho); }
    .bastidores code {
      display: block;
      margin-top: 6px;
      font-family: ui-monospace, Consolas, "Courier New", monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .digitando { display: flex; gap: 5px; padding: 6px 16px; }
    .digitando span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--cinza);
      animation: pulsar 1.2s infinite;
    }
    .digitando span:nth-child(2) { animation-delay: 0.15s; }
    .digitando span:nth-child(3) { animation-delay: 0.3s; }
    @keyframes pulsar {
      0%, 60%, 100% { opacity: 0.25; }
      30% { opacity: 1; }
    }

    /* ---------- campo de escrita ---------- */
    .composicao {
      flex: none;
      display: flex;
      gap: 10px;
      padding: 14px max(20px, calc((100% - 640px) / 2)) 20px;
      border-top: 1px solid var(--linha);
      background: var(--papel);
    }

    .entrada {
      flex: 1;
      min-width: 0;
      padding: 12px 14px;
      border: 1px solid #c9c1c4;
      border-radius: 4px;
      background: #fff;
      color: var(--tinta);
    }
    .entrada::placeholder { color: var(--cinza); }

    .enviar {
      background: var(--vinho);
      color: var(--papel);
      border: 0;
      border-radius: 4px;
      padding: 12px 22px;
      font-weight: 600;
      cursor: pointer;
    }
    .enviar:hover { background: var(--vinho-medio); }
    .enviar:disabled { opacity: 0.5; cursor: not-allowed; }

    /* ---------- modo embutido ---------- */
    .modo-embutido { height: 100%; }
    .modo-embutido .painel { height: 100%; }
    .modo-embutido .abrir,
    .modo-embutido .fechar { display: none; }
    .modo-embutido .topo {
      padding: 18px max(20px, calc((100% - 640px) / 2));
      border-bottom: 1px solid var(--linha);
      color: var(--vinho);
    }

    /* ---------- modo flutuante ---------- */
    .modo-flutuante .topo {
      padding: 14px 14px 14px 20px;
      background: var(--vinho);
      color: var(--papel);
    }
    .modo-flutuante .avatar { background: rgba(250, 250, 248, 0.12); color: var(--papel); }
    .modo-flutuante .subtitulo { color: #d3c3c9; }

    .modo-flutuante .abrir {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 2147483000;
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--vinho);
      color: var(--papel);
      border: 0;
      border-radius: 4px;
      padding: 12px 22px 12px 16px;
      font-weight: 500;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(59, 21, 33, 0.28);
    }
    .modo-flutuante .abrir:hover { background: var(--vinho-medio); }
    .modo-flutuante .abrir .ic svg { width: 24px; height: 24px; }
    .modo-flutuante.aberto .abrir { display: none; }

    .modo-flutuante .painel {
      position: fixed;
      right: 20px;
      bottom: 20px;
      z-index: 2147483001;
      width: 392px;
      height: min(680px, calc(100dvh - 40px));
      border: 1px solid var(--linha);
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 18px 50px rgba(59, 21, 33, 0.28);
      visibility: hidden;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.18s ease, transform 0.18s ease, visibility 0s linear 0.18s;
    }
    .modo-flutuante.aberto .painel {
      visibility: visible;
      opacity: 1;
      transform: none;
      transition: opacity 0.18s ease, transform 0.18s ease, visibility 0s;
    }

    @media (max-width: 560px) {
      .modo-flutuante .abrir { right: 16px; bottom: 16px; }
      .modo-flutuante .painel {
        inset: 0;
        width: 100%;
        height: 100dvh;
        border: 0;
        border-radius: 0;
      }
      .abertura .ola { font-size: 34px; }
    }

    @media (prefers-reduced-motion: reduce) {
      .digitando span { animation: none; opacity: 0.6; }
      .modo-flutuante .painel { transition: none; }
    }
  `;

  const HTML = `
    <section class="app">
      <button class="abrir" type="button" aria-expanded="false">
        <span class="ic"></span><span class="txt"></span>
      </button>
      <div class="painel" role="region">
        <header class="topo">
          <span class="avatar"></span>
          <div class="identidade">
            <span class="quem"></span>
            <span class="subtitulo"></span>
          </div>
          <button class="fechar" type="button" aria-label="Fechar conversa">&times;</button>
        </header>
        <div class="conversa" aria-live="polite"></div>
        <form class="composicao" autocomplete="off">
          <input class="entrada" type="text" maxlength="1000"
                 placeholder="Escreva sua mensagem" aria-label="Sua mensagem">
          <button class="enviar" type="submit">Enviar</button>
        </form>
      </div>
    </section>
  `;

  // ------------------------------------------------------------------
  // Texto do assistente. Aceita só o que o agente costuma produzir:
  //   **negrito**, listas com hífen, títulos (# ou linha só em negrito)
  //   e linhas de cardápio no formato "- Nome — R$ 00,00".
  // Escapa o HTML primeiro, então nada vindo do modelo vira marcação.
  // ------------------------------------------------------------------
  function escapar(texto) {
    const div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  const LINHA_DE_PRECO =
    /^(.*?)(?:\s+[\u2014\u2013-]\s+|:\s+)(R\$\s?\d[\d.]*(?:,\d{1,2})?)\.?\s*$/;

  function formatar(texto) {
    const saida = [];
    let itens = [];

    const negrito = (t) => t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    function fecharLista() {
      if (!itens.length) return;
      // Só vira "menu com fio pontilhado" se TODOS os itens tiverem preço.
      const cardapio = itens.every((item) => item.preco);
      const lis = itens.map((item) =>
        cardapio
          ? '<li class="prato"><span class="nome">' + item.nome +
            '</span><span class="fio"></span><span class="preco">' + item.preco + "</span></li>"
          : "<li>" + negrito(item.texto) + "</li>"
      );
      saida.push('<ul class="' + (cardapio ? "cardapio" : "lista") + '">' + lis.join("") + "</ul>");
      itens = [];
    }

    for (const linha of escapar(texto).split("\n")) {
      const limpa = linha.trim();

      const item = limpa.match(/^[-*\u2022]\s+(.*)$/);
      if (item) {
        const preco = item[1].match(LINHA_DE_PRECO);
        itens.push({
          texto: item[1],
          nome: preco ? preco[1].replace(/\*\*/g, "") : "",
          preco: preco ? preco[2] : "",
        });
        continue;
      }

      fecharLista();
      if (!limpa) continue;

      const titulo =
        limpa.match(/^(?:#{1,6}\s+)?\*\*([^*]+)\*\*:?$/) || limpa.match(/^#{1,6}\s+(.+)$/);
      if (titulo) {
        saida.push('<p class="secao">' + titulo[1].replace(/\*\*/g, "").replace(/:$/, "") + "</p>");
      } else {
        saida.push("<p>" + negrito(limpa) + "</p>");
      }
    }

    fecharLista();
    return saida.join("");
  }

  // ------------------------------------------------------------------
  function carregarFontes() {
    if (document.getElementById("sa-fontes")) return;
    const link = document.createElement("link");
    link.id = "sa-fontes";
    link.rel = "stylesheet";
    link.href = FONTES;
    document.head.appendChild(link); // @font-face não funciona dentro do Shadow DOM
  }

  function montar() {
    carregarFontes();

    const host = document.createElement("div");
    host.id = "sabor-arte-chat-host";

    if (config.modo === "embutido") {
      const destino = document.querySelector(config.alvo);
      if (!destino) {
        console.warn("Sabor & Arte: elemento não encontrado para embutir o chat:", config.alvo);
        return;
      }
      host.style.cssText = "display:block;height:100%";
      destino.appendChild(host);
    } else {
      document.body.appendChild(host);
    }

    const raiz = host.attachShadow({ mode: "open" });
    raiz.innerHTML = "<style>" + CSS + "</style>" + HTML;

    const $ = (seletor) => raiz.querySelector(seletor);
    const app = $(".app");
    const abrir = $(".abrir");
    const fechar = $(".fechar");
    const conversa = $(".conversa");
    const form = $(".composicao");
    const entrada = $(".entrada");
    const botaoEnviar = $(".enviar");

    app.classList.add("modo-" + config.modo);
    $(".painel").setAttribute("aria-label", "Conversa com " + config.assistente);
    $(".avatar").innerHTML = ICONE;
    $(".quem").textContent = config.assistente;
    $(".subtitulo").textContent = "Assistente virtual do " + config.nome;
    $(".abrir .ic").innerHTML = ICONE;
    $(".abrir .txt").textContent = "Falar com a " + config.assistente;

    let sessionId = null;
    let ocupado = false;

    // ----- abrir e fechar (modo flutuante) -----
    function alternar(aberto) {
      app.classList.toggle("aberto", aberto);
      abrir.setAttribute("aria-expanded", String(aberto));
      if (aberto) entrada.focus();
      else abrir.focus();
    }
    abrir.addEventListener("click", () => alternar(true));
    fechar.addEventListener("click", () => alternar(false));
    raiz.addEventListener("keydown", (evento) => {
      if (evento.key === "Escape" && app.classList.contains("aberto")) alternar(false);
    });

    // ----- conversa -----
    function rolarParaOFim() {
      conversa.scrollTop = conversa.scrollHeight;
    }

    function adicionar(texto, autor, extras) {
      extras = extras || {};
      const bloco = document.createElement("div");
      bloco.className = "msg " + autor + (extras.erro ? " erro" : "");

      if (autor === "assistente") {
        const rotulo = document.createElement("div");
        rotulo.className = "rotulo";
        rotulo.innerHTML = ICONE;
        const nome = document.createElement("span");
        nome.textContent = config.assistente;
        rotulo.appendChild(nome);
        bloco.appendChild(rotulo);
      }

      const corpo = document.createElement("div");
      corpo.className = "corpo";
      if (autor === "assistente") corpo.innerHTML = formatar(texto);
      else corpo.textContent = texto;
      bloco.appendChild(corpo);

      if (extras.tools && extras.tools.length) {
        const detalhe = document.createElement("details");
        detalhe.className = "bastidores";
        const titulo = document.createElement("summary");
        titulo.textContent =
          extras.tools.length === 1
            ? "1 consulta ao sistema"
            : extras.tools.length + " consultas ao sistema";
        detalhe.appendChild(titulo);
        for (const linha of extras.tools) {
          const codigo = document.createElement("code");
          codigo.textContent = linha;
          detalhe.appendChild(codigo);
        }
        bloco.appendChild(detalhe);
      }

      conversa.appendChild(bloco);
      rolarParaOFim();
    }

    function mostrarDigitando() {
      const bloco = document.createElement("div");
      bloco.className = "digitando";
      bloco.setAttribute("role", "status");
      bloco.setAttribute("aria-label", config.assistente + " está escrevendo");
      bloco.innerHTML = "<span></span><span></span><span></span>";
      conversa.appendChild(bloco);
      rolarParaOFim();
      return bloco;
    }

    async function enviar(texto) {
      texto = texto.trim();
      if (!texto || ocupado) return;

      ocupado = true;
      botaoEnviar.disabled = true;
      const sugestoes = $(".sugestoes");
      if (sugestoes) sugestoes.remove();

      adicionar(texto, "cliente");
      entrada.value = "";
      const indicador = mostrarDigitando();

      try {
        const resposta = await fetch(config.api + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mensagem: texto, session_id: sessionId }),
        });
        if (!resposta.ok) throw new Error("HTTP " + resposta.status);
        const dadosResposta = await resposta.json();
        sessionId = dadosResposta.session_id;
        indicador.remove();
        adicionar(dadosResposta.resposta, "assistente", dadosResposta);
      } catch (falha) {
        indicador.remove();
        adicionar(
          "Não foi possível falar com o restaurante agora. Tente novamente em instantes.",
          "assistente",
          { erro: true }
        );
      } finally {
        ocupado = false;
        botaoEnviar.disabled = false;
        entrada.focus();
      }
    }

    form.addEventListener("submit", (evento) => {
      evento.preventDefault();
      enviar(entrada.value);
    });

    // ----- saudação inicial -----
    const abertura = document.createElement("div");
    abertura.className = "abertura";

    const ola = document.createElement("p");
    ola.className = "ola";
    ola.textContent = "Olá, eu sou a " + config.assistente + ".";
    abertura.appendChild(ola);

    const apoio = document.createElement("p");
    apoio.className = "apoio";
    apoio.textContent =
      "Assistente do " + config.nome +
      ". Posso mostrar o cardápio, informar os horários e cuidar da sua reserva.";
    abertura.appendChild(apoio);

    const atalhos = document.createElement("div");
    atalhos.className = "sugestoes";
    for (const [rotulo, mensagem] of SUGESTOES) {
      const botao = document.createElement("button");
      botao.type = "button";
      botao.textContent = rotulo;
      botao.addEventListener("click", () => enviar(mensagem));
      atalhos.appendChild(botao);
    }
    abertura.appendChild(atalhos);
    conversa.appendChild(abertura);

    if (config.modo === "embutido") entrada.focus();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", montar);
  } else {
    montar();
  }
})();
