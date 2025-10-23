// static/js/app.js — versão com botões de download e limpar palpites

window.ULTIMOS_PALPITES = {};

async function fetchJson(url, opts) {
  const res = await fetch(url, opts);
  const data = await res.json();
  if (data && data.erro) throw new Error(data.erro);
  return data;
}

// ----------------------
// Últimos resultados
// ----------------------
async function carregarUltimosHome() {
  const container = document.getElementById("ultimos_container");
  if (!container) return;
  container.innerHTML = "";
  const lotes = ["lotofacil", "megasena", "quina", "maismilionaria", "diadesorte"];
  for (const l of lotes) {
    try {
      const data = await fetchJson(`/api/ultimos/${encodeURIComponent(l)}?n=2`);
      if (!data.ultimos || data.ultimos.length === 0) continue;
      const box = document.createElement("div");
      box.className = "news-item";
      let html = `<h4>${l.toUpperCase()}</h4>`;
      data.ultimos.forEach(item => {
        const concurso = item.concurso || "";
        const numeros = (item.numeros || []).map(n => String(n).padStart(2, "0")).join(",");
        const ganhadores = item.ganhadores || "Sem ganhador";
        const data_s = item.data || "";
        html += `<p>Concurso ${concurso} — Números: ${numeros} — Ganhadores: ${ganhadores} — Data:${data_s}</p>`;
      });
      box.innerHTML = html;
      container.appendChild(box);
    } catch (err) {
      const box = document.createElement("div");
      box.className = "news-item";
      box.innerHTML = `<h4>${l.toUpperCase()}</h4><p class="erro">Erro: ${err.message}</p>`;
      container.appendChild(box);
    }
  }
}

// ----------------------
// Análise matemática
// ----------------------
async function carregarAnalise(loteria) {
  const target = document.getElementById(`analise_content_${loteria}`);
  if (!target) return;
  target.innerHTML = "Carregando análise...";
  try {
    const data = await fetchJson(`/api/analisar/${encodeURIComponent(loteria)}`);
    let html = `<p><b>Total concursos:</b> ${data.total_concursos}</p>`;
    if (data.top10 && data.top10.length) {
      html += `<p><b>TOP 10:</b> ${data.top10.map(n => String(n).padStart(2,'0')).join(', ')}</p>`;
    }
    if (data.numeros_mais_atrasados && data.numeros_mais_atrasados.length) {
      html += `<p><b>Números mais atrasados:</b> ${data.numeros_mais_atrasados.map(n => String(n).padStart(2,'0')).join(', ')}</p>`;
    }
    if (loteria === "lotofacil" && data.media_pares !== undefined) {
      html += `<p><b>Média pares:</b> ${data.media_pares} — <b>Média ímpares:</b> ${data.media_impares}</p>`;
    }
    target.innerHTML = html;
  } catch (err) {
    target.innerHTML = `<p class="erro">Erro ao carregar análise: ${err.message}</p>`;
  }
}

// ----------------------
// Gerador de palpites
// ----------------------
async function gerarPalpites(loteria) {
  const qtdEl = document.getElementById(`palpites_${loteria}`);
  const dezEl = document.getElementById(`dezenas_${loteria}`);
  const target = document.getElementById(`resultado_${loteria}`);
  const qtd = qtdEl ? parseInt(qtdEl.value || 5) : 5;
  const dez = dezEl ? parseInt(dezEl.value || 0) : undefined;
  target.innerHTML = "Gerando palpites...";
  try {
    const url = `/api/palpite/${encodeURIComponent(loteria)}?quantidade=${qtd}` + (dez ? `&dezenas_por_jogo=${dez}` : '');
    const data = await fetchJson(url);
    const jogos = data.jogos || [];
    if (!Array.isArray(jogos) || jogos.length === 0) {
      target.innerHTML = "<p>Nenhum palpite gerado.</p>";
      return;
    }
    window.ULTIMOS_PALPITES[loteria] = jogos;

    let html = "<h4>Palpites gerados</h4>";
    jogos.forEach((j, i) => {
      html += `<p><b>Jogo ${i+1}:</b> ${j.map(n => String(n).padStart(2,'0')).join(', ')}</p>`;
    });

    // Botões extras
    html += `
      <div style="margin-top:10px;">
        <button onclick="baixarPalpites('${loteria}')">⬇️ Baixar Palpites (.TXT)</button>
        <button onclick="limparPalpites('${loteria}')">🗑️ Limpar</button>
      </div>
    `;

    target.innerHTML = html;
  } catch (err) {
    target.innerHTML = `<p class="erro">Erro ao gerar palpites: ${err.message}</p>`;
  }
}

// ----------------------
// Função para baixar palpites em TXT
// ----------------------
function baixarPalpites(loteria) {
  const jogos = window.ULTIMOS_PALPITES[loteria] || [];
  if (!jogos.length) {
    alert("Nenhum palpite disponível para download.");
    return;
  }
  let txt = `Palpites gerados - ${loteria.toUpperCase()}\n\n`;
  jogos.forEach((j, i) => {
    txt += `Jogo ${i+1}: ${j.map(n => String(n).padStart(2, '0')).join(', ')}\n`;
  });

  const blob = new Blob([txt], {type: 'text/plain'});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `palpites_${loteria}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ----------------------
// Função para limpar palpites da tela
// ----------------------
function limparPalpites(loteria) {
  if (confirm("Deseja realmente limpar os palpites desta loteria?")) {
    window.ULTIMOS_PALPITES[loteria] = [];
    const target = document.getElementById(`resultado_${loteria}`);
    if (target) target.innerHTML = "<p>Palpites limpos.</p>";
  }
}

// ----------------------
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("ultimos_container")) carregarUltimosHome();
});
