"""Back-end Flask do Sistema de Empréstimos de Equipamentos Escolares.

Como rodar (na pasta raiz do projeto):
    pip install -r requirements.txt
    python python/app.py            (use --exemplo para carregar dados de exemplo no banco vazio)

Depois abra http://127.0.0.1:5000 no navegador.

Fluxo de uma requisição: rota (recebe o JSON) -> model (valida) -> DAO (SQL) -> JSON.
"""
import sqlite3
import sys

import segno
from flask import Flask, jsonify, render_template, request, send_from_directory

from dao import (RAIZ, EmprestimoDAO, EquipamentoDAO, ManutencaoDAO, UsuarioDAO,
                 preparar_banco)
from models import (Emprestimo, Equipamento, ErroDeNegocio, ErroValidacao, Manutencao,
                    Usuario)

app = Flask(__name__,
            static_folder=str(RAIZ / "static"),
            template_folder=str(RAIZ / "templates"))
app.json.ensure_ascii = False  # acentos legíveis no JSON
app.json.sort_keys = False     # mantém a ordem das colunas

usuarios = UsuarioDAO()
equipamentos = EquipamentoDAO()
emprestimos = EmprestimoDAO()
manutencoes = ManutencaoDAO()


def corpo_json():
    """Devolve o JSON recebido (precisa ser um objeto)."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroValidacao("Envie um JSON válido no corpo da requisição.")
    return dados


def como_json(objeto, status=200):
    return jsonify(objeto.para_dict()), status


def lista_json(objetos):
    return jsonify([o.para_dict() for o in objetos])


# =====================================================================
# Páginas (front-end)
# =====================================================================

@app.get("/")
def pagina_inicial():
    return send_from_directory(RAIZ, "index.html")


@app.get("/etiqueta/<int:id_equipamento>")
def etiqueta(id_equipamento):
    """Página imprimível com o QR Code do equipamento."""
    equipamento = equipamentos.buscar_por_id(id_equipamento)
    qr = segno.make(equipamento.qr_code_uuid, error="m")
    return render_template("etiqueta.html", equipamento=equipamento,
                           qr_svg=qr.svg_inline(scale=6, border=2, dark="#111827"))


@app.get("/saude")
def saude():
    """Confirma que a API consegue falar com o banco."""
    usuarios.listar()
    return jsonify(api="ok", banco="ok")


# =====================================================================
# Rotas da API
# =====================================================================

# ---- Usuários ----
@app.post("/usuarios")
def cadastrar_usuario():
    usuario = Usuario.de_dict(corpo_json()).validar()
    return como_json(usuarios.cadastrar(usuario), 201)


@app.get("/usuarios")
def listar_usuarios():
    return lista_json(usuarios.listar(request.args.get("perfil"), request.args.get("situacao")))


@app.get("/usuarios/<int:id_usuario>")
def buscar_usuario(id_usuario):
    return como_json(usuarios.buscar_por_id(id_usuario))


@app.patch("/usuarios/<int:id_usuario>/desativar")
def desativar_usuario(id_usuario):
    return como_json(usuarios.desativar(id_usuario))


# ---- Equipamentos ----
@app.post("/equipamentos")
def cadastrar_equipamento():
    equipamento = Equipamento.de_dict(corpo_json()).validar()
    return como_json(equipamentos.cadastrar(equipamento), 201)


@app.get("/equipamentos")
def listar_equipamentos():
    return lista_json(equipamentos.listar(request.args.get("categoria"),
                                          request.args.get("status"),
                                          request.args.get("ativo", type=int)))


@app.get("/equipamentos/qr/<qr_code_uuid>")
def buscar_equipamento_por_qr(qr_code_uuid):
    return como_json(equipamentos.buscar_por_qr(qr_code_uuid))


@app.get("/equipamentos/<int:id_equipamento>")
def buscar_equipamento(id_equipamento):
    return como_json(equipamentos.buscar_por_id(id_equipamento))


@app.patch("/equipamentos/<int:id_equipamento>/baixar")
def baixar_equipamento(id_equipamento):
    return como_json(equipamentos.baixar(id_equipamento))


# ---- Empréstimos ----
@app.post("/emprestimos")
def emprestar():
    emprestimo = Emprestimo.de_dict(corpo_json()).validar()
    return como_json(emprestimos.emprestar(emprestimo), 201)


@app.get("/emprestimos")
def listar_emprestimos():
    return lista_json(emprestimos.listar(
        status=request.args.get("status"),
        id_usuario=request.args.get("id_usuario", type=int),
        id_equipamento=request.args.get("id_equipamento", type=int),
        atrasados=request.args.get("atrasados") == "1"))


@app.get("/emprestimos/<int:id_emprestimo>")
def buscar_emprestimo(id_emprestimo):
    return como_json(emprestimos.buscar_por_id(id_emprestimo))


@app.patch("/emprestimos/<int:id_emprestimo>/devolver")
def devolver_emprestimo(id_emprestimo):
    return como_json(emprestimos.devolver(id_emprestimo))


# ---- Manutenções ----
@app.post("/manutencoes")
def abrir_manutencao():
    manutencao = Manutencao.de_dict(corpo_json()).validar()
    return como_json(manutencoes.abrir(manutencao), 201)


@app.get("/manutencoes")
def listar_manutencoes():
    return lista_json(manutencoes.listar(request.args.get("id_equipamento", type=int),
                                         request.args.get("situacao")))


@app.get("/manutencoes/<int:id_manutencao>")
def buscar_manutencao(id_manutencao):
    return como_json(manutencoes.buscar_por_id(id_manutencao))


@app.patch("/manutencoes/<int:id_manutencao>/concluir")
def concluir_manutencao(id_manutencao):
    return como_json(manutencoes.concluir(id_manutencao))


# =====================================================================
# Tratamento de erros (a API sempre responde JSON)
# =====================================================================

@app.after_request
def liberar_cors(resposta):
    """Permite abrir o index.html direto do disco (file://) e chamar a API."""
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resposta


@app.errorhandler(ErroDeNegocio)
def erro_de_negocio(erro):
    return jsonify(erro=str(erro)), erro.status


@app.errorhandler(sqlite3.Error)
def erro_de_banco(erro):
    app.logger.exception(erro)
    return jsonify(erro="Erro ao acessar o banco de dados."), 500


@app.errorhandler(404)
def rota_inexistente(_erro):
    return jsonify(erro="Rota não encontrada."), 404


@app.errorhandler(405)
def metodo_invalido(_erro):
    return jsonify(erro="Método não permitido para esta rota."), 405


if __name__ == "__main__":
    preparar_banco(com_exemplo="--exemplo" in sys.argv)
    print("\n  Sistema de Empréstimos: http://127.0.0.1:5000\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
