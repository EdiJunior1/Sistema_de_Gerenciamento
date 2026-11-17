"use strict";

/* Front-end do sistema: consome as rotas Flask via fetch.
   Quando o index.html é aberto direto do disco (file://), chama o servidor local. */
const API = location.protocol === "file:" ? "http://127.0.0.1:5000" : "";

/* ===================== Utilitários ===================== */

const ROTULOS = {
  DISPONIVEL: "Disponível", EM_USO: "Em uso", EM_MANUTENCAO: "Em manutenção",
  OTIMO: "Ótimo", BOM: "Bom", REGULAR: "Regular", RUIM: "Ruim", DANIFICADO: "Danificado",
  ALUNO: "Aluno", PROFESSOR: "Professor", ADMINISTRADOR: "Administrador",
  ATIVO: "Ativo", INATIVO: "Inativo", DEVOLVIDO: "Devolvido", CANCELADO: "Cancelado",
  PREVENTIVA: "Preventiva", CORRETIVA: "Corretiva",
  ABERTA: "Aberta", AGUARDANDO_REPARO: "Aguardando reparo", CONCLUIDA: "Concluída",
};
const rotulo = (v) => ROTULOS[v] || v || "";

const esc = (texto) =>
  String(texto ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function formatarData(texto) {
  if (!texto) return "—";
  const [data, hora = ""] = texto.split(" ");
  const [ano, mes, dia] = data.split("-");
  return `${dia}/${mes}/${ano} ${hora.slice(0, 5)}`.trim();
}

const badge = (texto, cor) => `<span class="badge ${cor}">${esc(texto)}</span>`;

function dataParaInput(data) {
  const p = (n) => String(n).padStart(2, "0");
  return `${data.getFullYear()}-${p(data.getMonth() + 1)}-${p(data.getDate())}T${p(data.getHours())}:${p(data.getMinutes())}`;
}

async function api(caminho, metodo = "GET", corpo) {
  let resposta;
  try {
    resposta = await fetch(API + caminho, {
      method: metodo,
      headers: corpo ? { "Content-Type": "application/json" } : {},
      body: corpo ? JSON.stringify(corpo) : undefined,
    });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Verifique se o app.py está rodando.");
  }
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(dados.erro || "Erro inesperado.");
  return dados;
}

function avisar(mensagem, erro = false) {
  const aviso = document.createElement("div");
  aviso.className = "aviso" + (erro ? " erro" : "");
  aviso.textContent = mensagem;
  document.getElementById("avisos").appendChild(aviso);
  setTimeout(() => aviso.remove(), 4000);
}

/* ===================== Dados ===================== */

const dados = { usuarios: [], equipamentos: [], emprestimos: [], manutencoes: [] };
const filtros = {
  equipamentos: { busca: "", status: "" },
  usuarios: { busca: "", perfil: "" },
  emprestimos: { situacao: "" },
  manutencoes: { situacao: "" },
};

async function carregar() {
  try {
    const [usuarios, equipamentos, emprestimos, manutencoes] = await Promise.all([
      api("/usuarios"), api("/equipamentos"), api("/emprestimos"), api("/manutencoes"),
    ]);
    Object.assign(dados, { usuarios, equipamentos, emprestimos, manutencoes });
    desenhar();
  } catch (erro) {
    document.getElementById("visao").innerHTML = `<div class="cartao vazio">${esc(erro.message)}</div>`;
  }
}

/* ===================== Tabelas ===================== */

function tabela(colunas, linhas, vazio) {
  if (!linhas.length) return `<div class="tabela-caixa"><div class="vazio">${esc(vazio)}</div></div>`;
  const cabecalho = colunas.map((c) => `<th>${c}</th>`).join("");
  const corpo = linhas.map((l) => `<tr class="${l.classe || ""}">${l.celulas.map((c) => `<td${c.acoes ? ' class="acoes"' : ""}>${c.html ?? c}</td>`).join("")}</tr>`).join("");
  return `<div class="tabela-caixa"><table><thead><tr>${cabecalho}</tr></thead><tbody>${corpo}</tbody></table></div>`;
}

const botao = (texto, acao, id, classe = "") =>
  `<button class="mini ${classe}" data-acao="${acao}" data-id="${id}">${texto}</button>`;

function selo(equipamento) {
  if (!equipamento.ativo) return badge("Baixado", "cinza");
  const cores = { DISPONIVEL: "verde", EM_USO: "azul", EM_MANUTENCAO: "amarelo" };
  return badge(rotulo(equipamento.status_operacional), cores[equipamento.status_operacional]);
}

function seloEmprestimo(e) {
  if (e.status_emprestimo === "DEVOLVIDO") return badge("Devolvido", "verde");
  if (e.status_emprestimo === "CANCELADO") return badge("Cancelado", "cinza");
  return e.atrasado ? badge("Atrasado", "vermelho") : badge("Em andamento", "azul");
}

/* ===================== Visões ===================== */

const VISOES = {
  painel: {
    titulo: "Painel", subtitulo: "Resumo geral do sistema.",
    acao: ["Novo empréstimo", () => formEmprestimo()],
    render() {
      const ativos = dados.equipamentos.filter((e) => e.ativo);
      const contar = (s) => ativos.filter((e) => e.status_operacional === s).length;
      const disponiveis = contar("DISPONIVEL"), emUso = contar("EM_USO"), manut = contar("EM_MANUTENCAO");
      const andamento = dados.emprestimos.filter((e) => e.status_emprestimo === "ATIVO");
      const atrasados = andamento.filter((e) => e.atrasado).length;
      const abertas = dados.manutencoes.filter((m) => m.situacao_manutencao !== "CONCLUIDA");
      const usuariosAtivos = dados.usuarios.filter((u) => u.situacao === "ATIVO").length;
      const total = ativos.length || 1;
      const pct = (n) => ((n / total) * 100).toFixed(1);

      const tabEmprestimos = tabela(
        ["Equipamento", "Usuário", "Devolução prevista", "Situação"],
        andamento.slice(0, 6).map((e) => ({ celulas: [
          `<strong>${esc(e.nome_equipamento)}</strong>`, esc(e.nome_usuario),
          formatarData(e.data_prevista_devolucao), seloEmprestimo(e)] })),
        "Nenhum empréstimo em andamento.");
      const tabManut = tabela(
        ["Equipamento", "Tipo", "Problema"],
        abertas.slice(0, 6).map((m) => ({ celulas: [
          `<strong>${esc(m.nome_equipamento)}</strong>`, badge(rotulo(m.tipo_manutencao), "amarelo"),
          esc(m.descricao_problema)] })),
        "Nenhuma manutenção aberta.");

      return `
        <div class="estatisticas">
          <div class="estatistica"><span>Equipamentos ativos</span><strong>${ativos.length}</strong></div>
          <div class="estatistica"><span>Disponíveis</span><strong>${disponiveis}</strong></div>
          <div class="estatistica"><span>Em uso</span><strong>${emUso}</strong></div>
          <div class="estatistica"><span>Em manutenção</span><strong>${manut}</strong></div>
          <div class="estatistica ${atrasados ? "alerta" : ""}"><span>Empréstimos atrasados</span><strong>${atrasados}</strong></div>
          <div class="estatistica"><span>Usuários ativos</span><strong>${usuariosAtivos}</strong></div>
        </div>
        <div class="cartao">
          <h2>Situação dos equipamentos</h2>
          <div class="distribuicao">
            <i class="c-verde" style="width:${pct(disponiveis)}%"></i>
            <i class="c-azul" style="width:${pct(emUso)}%"></i>
            <i class="c-amarelo" style="width:${pct(manut)}%"></i>
          </div>
          <div class="legenda">
            <span><i class="ponto c-verde"></i>Disponíveis <b>${disponiveis}</b></span>
            <span><i class="ponto c-azul"></i>Em uso <b>${emUso}</b></span>
            <span><i class="ponto c-amarelo"></i>Em manutenção <b>${manut}</b></span>
          </div>
        </div>
        <div class="grade-2">
          <div class="cartao"><h2>Empréstimos em andamento</h2>${tabEmprestimos}</div>
          <div class="cartao"><h2>Manutenções abertas</h2>${tabManut}</div>
        </div>`;
    },
  },

  equipamentos: {
    titulo: "Equipamentos", subtitulo: "Cadastro e situação de cada equipamento.",
    acao: ["Novo equipamento", () => formEquipamento()],
    render() {
      return `
        <div class="ferramentas">
          <input type="search" id="f-busca" placeholder="Buscar por nome, código ou categoria" value="${esc(filtros.equipamentos.busca)}">
          <select id="f-status">
            ${opcoesFiltro(filtros.equipamentos.status, [["", "Todas as situações"], ["DISPONIVEL", "Disponíveis"],
              ["EM_USO", "Em uso"], ["EM_MANUTENCAO", "Em manutenção"], ["BAIXADO", "Baixados"]])}
          </select>
        </div>
        <div id="tabela"></div>`;
    },
    tabela() {
      const { busca, status } = filtros.equipamentos;
      const lista = dados.equipamentos.filter((e) => {
        const texto = `${e.nome} ${e.codigo_identificacao} ${e.categoria}`.toLowerCase();
        const passaStatus = !status ? true : status === "BAIXADO" ? !e.ativo : e.ativo && e.status_operacional === status;
        return texto.includes(busca.toLowerCase()) && passaStatus;
      });
      return tabela(
        ["Código", "Equipamento", "Conservação", "Situação", ""],
        lista.map((e) => ({
          classe: e.ativo ? "" : "linha-inativa",
          celulas: [
            `<strong>${esc(e.codigo_identificacao)}</strong>`,
            `${esc(e.nome)}<small>${esc(e.categoria)}</small>`,
            esc(rotulo(e.estado_conservacao)),
            selo(e),
            { acoes: true, html:
              (e.ativo && e.status_operacional === "DISPONIVEL" ? botao("Emprestar", "emprestar", e.id_equipamento, "destaque") : "") +
              (e.ativo && e.status_operacional !== "EM_MANUTENCAO" && e.status_operacional !== "EM_USO" ? botao("Manutenção", "manutencao", e.id_equipamento) : "") +
              `<a class="mini" href="${API}/etiqueta/${e.id_equipamento}" target="_blank" rel="noopener">QR Code</a>` +
              (e.ativo && e.status_operacional !== "EM_USO" ? botao("Dar baixa", "baixar", e.id_equipamento, "perigo") : "") },
          ],
        })),
        "Nenhum equipamento encontrado.");
    },
    eventos() {
      ligar("f-busca", "input", (v) => (filtros.equipamentos.busca = v));
      ligar("f-status", "change", (v) => (filtros.equipamentos.status = v));
    },
  },

  emprestimos: {
    titulo: "Empréstimos", subtitulo: "Retiradas, devoluções e histórico.",
    acao: ["Novo empréstimo", () => formEmprestimo()],
    render() {
      return `
        <div class="ferramentas">
          <select id="f-situacao">
            ${opcoesFiltro(filtros.emprestimos.situacao, [["", "Todos"], ["ATIVO", "Em andamento"],
              ["ATRASADO", "Atrasados"], ["DEVOLVIDO", "Devolvidos"]])}
          </select>
        </div>
        <div id="tabela"></div>`;
    },
    tabela() {
      const s = filtros.emprestimos.situacao;
      const lista = dados.emprestimos.filter((e) =>
        !s ? true : s === "ATRASADO" ? e.atrasado : e.status_emprestimo === s);
      return tabela(
        ["Nº", "Equipamento", "Usuário", "Retirada", "Prevista", "Devolução", "Situação", ""],
        lista.map((e) => ({ celulas: [
          `#${e.id_emprestimo}`,
          `<strong>${esc(e.nome_equipamento)}</strong><small>${esc(e.codigo_identificacao)}</small>`,
          esc(e.nome_usuario),
          formatarData(e.data_retirada), formatarData(e.data_prevista_devolucao), formatarData(e.data_devolucao),
          seloEmprestimo(e),
          { acoes: true, html: e.status_emprestimo === "ATIVO" ? botao("Registrar devolução", "devolver", e.id_emprestimo, "destaque") : "" },
        ] })),
        "Nenhum empréstimo encontrado.");
    },
    eventos() { ligar("f-situacao", "change", (v) => (filtros.emprestimos.situacao = v)); },
  },

  usuarios: {
    titulo: "Usuários", subtitulo: "Alunos, professores e administradores.",
    acao: ["Novo usuário", () => formUsuario()],
    render() {
      return `
        <div class="ferramentas">
          <input type="search" id="f-busca" placeholder="Buscar por nome, e-mail ou matrícula" value="${esc(filtros.usuarios.busca)}">
          <select id="f-perfil">
            ${opcoesFiltro(filtros.usuarios.perfil, [["", "Todos os perfis"], ["ALUNO", "Alunos"],
              ["PROFESSOR", "Professores"], ["ADMINISTRADOR", "Administradores"]])}
          </select>
        </div>
        <div id="tabela"></div>`;
    },
    tabela() {
      const { busca, perfil } = filtros.usuarios;
      const lista = dados.usuarios.filter((u) =>
        `${u.nome_completo} ${u.email} ${u.matricula}`.toLowerCase().includes(busca.toLowerCase()) &&
        (!perfil || u.perfil === perfil));
      return tabela(
        ["Matrícula", "Nome", "Perfil", "Situação", "Cadastro", ""],
        lista.map((u) => ({
          classe: u.situacao === "ATIVO" ? "" : "linha-inativa",
          celulas: [
            `<strong>${esc(u.matricula)}</strong>`,
            `${esc(u.nome_completo)}<small>${esc(u.email)}</small>`,
            esc(rotulo(u.perfil)),
            badge(rotulo(u.situacao), u.situacao === "ATIVO" ? "verde" : "cinza"),
            formatarData(u.data_cadastro),
            { acoes: true, html: u.situacao === "ATIVO" ? botao("Desativar", "desativar", u.id_usuario, "perigo") : "" },
          ],
        })),
        "Nenhum usuário encontrado.");
    },
    eventos() {
      ligar("f-busca", "input", (v) => (filtros.usuarios.busca = v));
      ligar("f-perfil", "change", (v) => (filtros.usuarios.perfil = v));
    },
  },

  manutencoes: {
    titulo: "Manutenções", subtitulo: "Registro de reparos e revisões.",
    acao: ["Abrir manutenção", () => formManutencao()],
    render() {
      return `
        <div class="ferramentas">
          <select id="f-situacao">
            ${opcoesFiltro(filtros.manutencoes.situacao, [["", "Todas"], ["ABERTA", "Abertas"], ["CONCLUIDA", "Concluídas"]])}
          </select>
        </div>
        <div id="tabela"></div>`;
    },
    tabela() {
      const s = filtros.manutencoes.situacao;
      const lista = dados.manutencoes.filter((m) =>
        !s ? true : s === "ABERTA" ? m.situacao_manutencao !== "CONCLUIDA" : m.situacao_manutencao === s);
      return tabela(
        ["Nº", "Equipamento", "Tipo", "Problema", "Responsável", "Abertura", "Situação", ""],
        lista.map((m) => ({ celulas: [
          `#${m.id_manutencao}`,
          `<strong>${esc(m.nome_equipamento)}</strong><small>${esc(m.codigo_identificacao)}</small>`,
          esc(rotulo(m.tipo_manutencao)), esc(m.descricao_problema), esc(m.nome_responsavel || "—"),
          formatarData(m.data_abertura),
          badge(rotulo(m.situacao_manutencao), m.situacao_manutencao === "CONCLUIDA" ? "verde" : "amarelo"),
          { acoes: true, html: m.situacao_manutencao !== "CONCLUIDA" ? botao("Concluir", "concluir", m.id_manutencao, "destaque") : "" },
        ] })),
        "Nenhuma manutenção encontrada.");
    },
    eventos() { ligar("f-situacao", "change", (v) => (filtros.manutencoes.situacao = v)); },
  },
};

function opcoesFiltro(atual, opcoes) {
  return opcoes.map(([valor, texto]) => `<option value="${valor}" ${valor === atual ? "selected" : ""}>${texto}</option>`).join("");
}

/* Liga um campo de filtro: atualiza o estado e redesenha só a tabela (o campo não perde o foco). */
function ligar(id, evento, definir) {
  document.getElementById(id).addEventListener(evento, (e) => {
    definir(e.target.value);
    document.getElementById("tabela").innerHTML = VISOES[visaoAtual()].tabela();
  });
}

/* ===================== Navegação e desenho ===================== */

const visaoAtual = () => (VISOES[location.hash.slice(1)] ? location.hash.slice(1) : "painel");

function desenhar() {
  const nome = visaoAtual();
  const visao = VISOES[nome];
  document.getElementById("titulo").textContent = visao.titulo;
  document.getElementById("subtitulo").textContent = visao.subtitulo;
  const botaoAcao = document.getElementById("botao-acao");
  botaoAcao.textContent = visao.acao[0];
  botaoAcao.onclick = visao.acao[1];
  document.querySelectorAll("#navegacao a").forEach((a) => a.classList.toggle("ativo", a.dataset.visao === nome));

  document.getElementById("visao").innerHTML = visao.render();
  if (visao.tabela) {
    document.getElementById("tabela").innerHTML = visao.tabela();
    visao.eventos();
  }
}

window.addEventListener("hashchange", desenhar);

/* ===================== Modal ===================== */

const modal = document.getElementById("modal");

function campoHtml(c) {
  const id = `campo-${c.nome}`;
  let entrada;
  if (c.tipo === "select") {
    entrada = `<select id="${id}" name="${c.nome}" ${c.obrigatorio ? "required" : ""}>${c.opcoes.map(([v, t]) =>
      `<option value="${esc(v)}" ${String(v) === String(c.valor ?? "") ? "selected" : ""}>${esc(t)}</option>`).join("")}</select>`;
  } else if (c.tipo === "textarea") {
    entrada = `<textarea id="${id}" name="${c.nome}" ${c.obrigatorio ? "required" : ""}>${esc(c.valor || "")}</textarea>`;
  } else {
    entrada = `<input id="${id}" name="${c.nome}" type="${c.tipo || "text"}" value="${esc(c.valor || "")}" ${c.obrigatorio ? "required" : ""} ${c.placeholder ? `placeholder="${esc(c.placeholder)}"` : ""}>`;
  }
  return `<div class="campo"><label for="${id}">${esc(c.rotulo)}</label>${entrada}${c.ajuda ? `<small>${esc(c.ajuda)}</small>` : ""}</div>`;
}

function abrirFormulario({ titulo, texto = "", campos = [], botao: textoBotao = "Salvar", perigo = false, enviar }) {
  modal.innerHTML = `
    <form class="modal-corpo" novalidate>
      <h2>${esc(titulo)}</h2>
      ${texto ? `<p class="modal-texto">${esc(texto)}</p>` : ""}
      <div id="erro-form" class="erro-form" hidden></div>
      ${campos.map(campoHtml).join("")}
      <div class="modal-botoes">
        <button type="button" class="botao secundario" id="cancelar">Cancelar</button>
        <button type="submit" class="botao ${perigo ? "perigo" : ""}">${esc(textoBotao)}</button>
      </div>
    </form>`;
  const form = modal.querySelector("form");
  modal.querySelector("#cancelar").onclick = () => modal.close();
  form.onsubmit = async (evento) => {
    evento.preventDefault();
    if (!form.reportValidity()) return;
    const valores = Object.fromEntries(new FormData(form).entries());
    try {
      const mensagem = await enviar(valores);
      modal.close();
      avisar(mensagem);
      await carregar();
    } catch (erro) {
      const caixa = modal.querySelector("#erro-form");
      caixa.textContent = erro.message;
      caixa.hidden = false;
    }
  };
  modal.showModal();
}

/* ===================== Formulários ===================== */

function formUsuario() {
  abrirFormulario({
    titulo: "Novo usuário",
    campos: [
      { nome: "nome_completo", rotulo: "Nome completo", obrigatorio: true },
      { nome: "email", rotulo: "E-mail", tipo: "email", obrigatorio: true },
      { nome: "matricula", rotulo: "Matrícula", obrigatorio: true },
      { nome: "perfil", rotulo: "Perfil", tipo: "select", valor: "ALUNO",
        opcoes: [["ALUNO", "Aluno"], ["PROFESSOR", "Professor"], ["ADMINISTRADOR", "Administrador"]] },
    ],
    enviar: async (v) => { await api("/usuarios", "POST", v); return "Usuário cadastrado."; },
  });
}

function formEquipamento() {
  abrirFormulario({
    titulo: "Novo equipamento",
    texto: "O QR Code é gerado automaticamente ao salvar.",
    campos: [
      { nome: "nome", rotulo: "Nome", obrigatorio: true },
      { nome: "categoria", rotulo: "Categoria", obrigatorio: true, placeholder: "Ex.: Informática, Audiovisual" },
      { nome: "codigo_identificacao", rotulo: "Código de identificação", obrigatorio: true, placeholder: "Ex.: NB-003" },
      { nome: "estado_conservacao", rotulo: "Estado de conservação", tipo: "select", valor: "BOM",
        opcoes: [["OTIMO", "Ótimo"], ["BOM", "Bom"], ["REGULAR", "Regular"], ["RUIM", "Ruim"], ["DANIFICADO", "Danificado"]] },
      { nome: "descricao", rotulo: "Descrição", tipo: "textarea" },
    ],
    enviar: async (v) => { await api("/equipamentos", "POST", v); return "Equipamento cadastrado."; },
  });
}

function formEmprestimo(idEquipamento = "") {
  const amanha = new Date(Date.now() + 24 * 3600 * 1000);
  abrirFormulario({
    titulo: "Novo empréstimo",
    campos: [
      { nome: "id_usuario", rotulo: "Usuário", tipo: "select", obrigatorio: true,
        opcoes: [["", "Selecione..."], ...dados.usuarios.filter((u) => u.situacao === "ATIVO")
          .map((u) => [u.id_usuario, `${u.nome_completo} (${u.matricula})`])] },
      { nome: "id_equipamento", rotulo: "Equipamento", tipo: "select", valor: idEquipamento,
        opcoes: [["", "Selecione..."], ...dados.equipamentos.filter((e) => e.ativo && e.status_operacional === "DISPONIVEL")
          .map((e) => [e.id_equipamento, `${e.nome} (${e.codigo_identificacao})`])] },
      { nome: "qr_code_uuid", rotulo: "Ou leia o QR Code do equipamento", placeholder: "Código lido pelo leitor",
        ajuda: "Se preencher o QR Code, ele tem prioridade sobre a lista acima." },
      { nome: "data_prevista_devolucao", rotulo: "Devolução prevista", tipo: "datetime-local",
        obrigatorio: true, valor: dataParaInput(amanha) },
      { nome: "observacoes", rotulo: "Observações", tipo: "textarea" },
    ],
    botao: "Registrar empréstimo",
    enviar: async (v) => {
      const corpo = { id_usuario: v.id_usuario, data_prevista_devolucao: v.data_prevista_devolucao.replace("T", " "),
                      observacoes: v.observacoes };
      if (v.qr_code_uuid.trim()) corpo.qr_code_uuid = v.qr_code_uuid.trim();
      else if (v.id_equipamento) corpo.id_equipamento = v.id_equipamento;
      await api("/emprestimos", "POST", corpo);
      return "Empréstimo registrado.";
    },
  });
}

function formManutencao(idEquipamento = "") {
  abrirFormulario({
    titulo: "Abrir manutenção",
    texto: "O equipamento fica indisponível até a manutenção ser concluída.",
    campos: [
      { nome: "id_equipamento", rotulo: "Equipamento", tipo: "select", obrigatorio: true, valor: idEquipamento,
        opcoes: [["", "Selecione..."], ...dados.equipamentos.filter((e) => e.ativo && e.status_operacional === "DISPONIVEL")
          .map((e) => [e.id_equipamento, `${e.nome} (${e.codigo_identificacao})`])] },
      { nome: "tipo_manutencao", rotulo: "Tipo", tipo: "select", valor: "CORRETIVA",
        opcoes: [["CORRETIVA", "Corretiva"], ["PREVENTIVA", "Preventiva"]] },
      { nome: "descricao_problema", rotulo: "Descrição do problema", tipo: "textarea", obrigatorio: true },
      { nome: "id_usuario_responsavel", rotulo: "Responsável", tipo: "select",
        opcoes: [["", "Não definido"], ...dados.usuarios.filter((u) => u.situacao === "ATIVO" && u.perfil !== "ALUNO")
          .map((u) => [u.id_usuario, u.nome_completo])] },
    ],
    botao: "Abrir manutenção",
    enviar: async (v) => {
      await api("/manutencoes", "POST", { ...v, id_usuario_responsavel: v.id_usuario_responsavel || null });
      return "Manutenção aberta.";
    },
  });
}

function confirmar({ titulo, texto, botao, perigo, requisicao, sucesso }) {
  abrirFormulario({ titulo, texto, botao, perigo, enviar: async () => { await requisicao(); return sucesso; } });
}

/* ===================== Ações dos botões das tabelas ===================== */

const ACOES = {
  emprestar: (id) => formEmprestimo(id),
  manutencao: (id) => formManutencao(id),
  baixar: (id) => confirmar({ titulo: "Dar baixa no equipamento",
    texto: "O equipamento deixa de aparecer para empréstimo, mas o histórico é preservado.",
    botao: "Dar baixa", perigo: true, requisicao: () => api(`/equipamentos/${id}/baixar`, "PATCH"), sucesso: "Baixa registrada." }),
  devolver: (id) => confirmar({ titulo: "Registrar devolução",
    texto: "Confirma que o equipamento foi devolvido?",
    botao: "Confirmar devolução", requisicao: () => api(`/emprestimos/${id}/devolver`, "PATCH"), sucesso: "Devolução registrada." }),
  desativar: (id) => confirmar({ titulo: "Desativar usuário",
    texto: "O usuário não poderá mais pegar equipamentos emprestados. O histórico é mantido.",
    botao: "Desativar", perigo: true, requisicao: () => api(`/usuarios/${id}/desativar`, "PATCH"), sucesso: "Usuário desativado." }),
  concluir: (id) => confirmar({ titulo: "Concluir manutenção",
    texto: "O equipamento volta a ficar disponível.",
    botao: "Concluir", requisicao: () => api(`/manutencoes/${id}/concluir`, "PATCH"), sucesso: "Manutenção concluída." }),
};

document.addEventListener("click", (evento) => {
  const alvo = evento.target.closest("[data-acao]");
  if (alvo) ACOES[alvo.dataset.acao](alvo.dataset.id);
});

carregar();
