"""DAOs: único lugar do sistema que fala com o banco (SQLite).

O banco é o arquivo schema/emprestimos.db, criado a partir do schema/banco.sql.
Todos os valores vão como parâmetros (?), nunca concatenados no SQL (evita SQL Injection).
"""
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from models import (Conflito, Emprestimo, Equipamento, ErroValidacao, Manutencao,
                    NaoEncontrado, Usuario)

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_DB = RAIZ / "schema" / "emprestimos.db"
ARQUIVO_SQL = RAIZ / "schema" / "banco.sql"
ARQUIVO_EXEMPLO = RAIZ / "schema" / "dados_exemplo.sql"

AGORA = "datetime('now','localtime')"

STATUS_LEGIVEL = {"EM_USO": "em uso", "EM_MANUTENCAO": "em manutenção", "DISPONIVEL": "disponível"}
CAMPOS_UNICOS = {"email": "e-mail", "matricula": "matrícula",
                 "codigo_identificacao": "código de identificação", "qr_code_uuid": "QR Code"}


# =====================================================================
# Conexão e criação do banco
# =====================================================================

def conectar():
    """Abre uma conexão (cada operação abre e fecha a sua)."""
    con = sqlite3.connect(ARQUIVO_DB, timeout=10, isolation_level=None)  # transações manuais
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")  # o SQLite só respeita FK se pedir
    return con


def preparar_banco(com_exemplo=False):
    """Executa o banco.sql (IF NOT EXISTS: cria o que falta, não apaga nada).

    Com com_exemplo=True, carrega os dados de exemplo se não houver nenhum usuário.
    """
    con = conectar()
    try:
        con.executescript(ARQUIVO_SQL.read_text(encoding="utf-8"))
        vazio = con.execute("SELECT COUNT(*) FROM Usuarios").fetchone()[0] == 0
        if com_exemplo and vazio:
            con.executescript(ARQUIVO_EXEMPLO.read_text(encoding="utf-8"))
    finally:
        con.close()


def traduzir_erro(erro):
    """Converte erros de integridade do SQLite em mensagens para o usuário."""
    texto = str(erro)
    if "UNIQUE" in texto:
        campo = texto.rsplit(".", 1)[-1]
        return Conflito(f"O campo {CAMPOS_UNICOS.get(campo, campo)} já está cadastrado.")
    if "FOREIGN KEY" in texto:
        return NaoEncontrado("Registro relacionado não encontrado.")
    return ErroValidacao("Dados inválidos para o banco.")


class BaseDAO:
    """Classe-base: executa SELECTs e transações. Os filhos só escrevem o SQL."""

    def _consultar(self, sql, params=(), um=False):
        con = conectar()
        try:
            cursor = con.execute(sql, params)
            if um:
                linha = cursor.fetchone()
                return dict(linha) if linha else None
            return [dict(linha) for linha in cursor.fetchall()]
        finally:
            con.close()

    @contextmanager
    def _transacao(self):
        """Commit se tudo der certo, rollback se algo falhar.

        BEGIN IMMEDIATE reserva o banco para escrita já no início, então duas
        retiradas simultâneas do mesmo equipamento não passam juntas.
        """
        con = conectar()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.execute("COMMIT")
        except BaseException as erro:
            if con.in_transaction:
                con.execute("ROLLBACK")
            if isinstance(erro, sqlite3.IntegrityError):
                raise traduzir_erro(erro) from erro
            raise
        finally:
            con.close()


def _linha(con, sql, params, mensagem):
    """SELECT de uma linha dentro de uma transação; NaoEncontrado se não existir."""
    linha = con.execute(sql, params).fetchone()
    if linha is None:
        raise NaoEncontrado(mensagem)
    return linha


# =====================================================================
# Usuários
# =====================================================================

class UsuarioDAO(BaseDAO):

    def cadastrar(self, usuario):
        with self._transacao() as con:
            cursor = con.execute(
                "INSERT INTO Usuarios (nome_completo, email, matricula, perfil) VALUES (?, ?, ?, ?)",
                (usuario.nome_completo, usuario.email, usuario.matricula, usuario.perfil))
            novo_id = cursor.lastrowid
        return self.buscar_por_id(novo_id)

    def listar(self, perfil=None, situacao=None):
        sql, params = "SELECT * FROM Usuarios WHERE 1=1", []
        if perfil:
            sql += " AND perfil = ?"
            params.append(perfil.upper())
        if situacao:
            sql += " AND situacao = ?"
            params.append(situacao.upper())
        return [Usuario.de_linha(l) for l in self._consultar(sql + " ORDER BY nome_completo", params)]

    def buscar_por_id(self, id_usuario):
        linha = self._consultar("SELECT * FROM Usuarios WHERE id_usuario = ?", (id_usuario,), um=True)
        if linha is None:
            raise NaoEncontrado("Usuário não encontrado.")
        return Usuario.de_linha(linha)

    def desativar(self, id_usuario):
        with self._transacao() as con:
            _linha(con, "SELECT 1 FROM Usuarios WHERE id_usuario = ?", (id_usuario,),
                   "Usuário não encontrado.")
            ativos = con.execute(
                "SELECT COUNT(*) FROM Historico_de_Emprestimos "
                "WHERE id_usuario = ? AND status_emprestimo = 'ATIVO'", (id_usuario,)).fetchone()[0]
            if ativos:
                raise Conflito("O usuário tem empréstimo ativo. Registre a devolução antes de desativar.")
            con.execute("UPDATE Usuarios SET situacao = 'INATIVO' WHERE id_usuario = ?", (id_usuario,))
        return self.buscar_por_id(id_usuario)


# =====================================================================
# Equipamentos
# =====================================================================

class EquipamentoDAO(BaseDAO):

    def cadastrar(self, equipamento):
        qr = str(uuid.uuid4())  # identificador único gravado no QR Code
        with self._transacao() as con:
            cursor = con.execute(
                "INSERT INTO Equipamentos (nome, descricao, categoria, codigo_identificacao, "
                "qr_code_uuid, estado_conservacao) VALUES (?, ?, ?, ?, ?, ?)",
                (equipamento.nome, equipamento.descricao, equipamento.categoria,
                 equipamento.codigo_identificacao, qr, equipamento.estado_conservacao))
            novo_id = cursor.lastrowid
        return self.buscar_por_id(novo_id)

    def listar(self, categoria=None, status=None, ativo=None):
        sql, params = "SELECT * FROM Equipamentos WHERE 1=1", []
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if status:
            sql += " AND status_operacional = ?"
            params.append(status.upper())
        if ativo in (0, 1):
            sql += " AND ativo = ?"
            params.append(ativo)
        return [Equipamento.de_linha(l) for l in self._consultar(sql + " ORDER BY nome", params)]

    def buscar_por_id(self, id_equipamento):
        linha = self._consultar("SELECT * FROM Equipamentos WHERE id_equipamento = ?",
                                (id_equipamento,), um=True)
        if linha is None:
            raise NaoEncontrado("Equipamento não encontrado.")
        return Equipamento.de_linha(linha)

    def buscar_por_qr(self, qr_code_uuid):
        linha = self._consultar("SELECT * FROM Equipamentos WHERE qr_code_uuid = ?",
                                (qr_code_uuid,), um=True)
        if linha is None:
            raise NaoEncontrado("Nenhum equipamento com esse QR Code.")
        return Equipamento.de_linha(linha)

    def baixar(self, id_equipamento):
        """Dá baixa (ativo = 0). Não apaga, para preservar o histórico."""
        with self._transacao() as con:
            equipamento = _linha(con, "SELECT * FROM Equipamentos WHERE id_equipamento = ?",
                                 (id_equipamento,), "Equipamento não encontrado.")
            if equipamento["status_operacional"] == "EM_USO":
                raise Conflito("O equipamento está emprestado. Registre a devolução antes da baixa.")
            con.execute("UPDATE Equipamentos SET ativo = 0 WHERE id_equipamento = ?", (id_equipamento,))
        return self.buscar_por_id(id_equipamento)


# =====================================================================
# Empréstimos
# =====================================================================

class EmprestimoDAO(BaseDAO):

    SELECT = f"""
        SELECT h.*, u.nome_completo AS nome_usuario, e.nome AS nome_equipamento,
               e.codigo_identificacao,
               CASE WHEN h.status_emprestimo = 'ATIVO'
                     AND h.data_prevista_devolucao < {AGORA} THEN 1 ELSE 0 END AS atrasado
          FROM Historico_de_Emprestimos h
          JOIN Usuarios u     ON u.id_usuario = h.id_usuario
          JOIN Equipamentos e ON e.id_equipamento = h.id_equipamento
    """

    def emprestar(self, emprestimo):
        with self._transacao() as con:
            usuario = _linha(con, "SELECT * FROM Usuarios WHERE id_usuario = ?",
                             (emprestimo.id_usuario,), "Usuário não encontrado.")
            if usuario["situacao"] != "ATIVO":
                raise Conflito("O usuário está inativo.")

            if emprestimo.id_equipamento is not None:
                equipamento = _linha(con, "SELECT * FROM Equipamentos WHERE id_equipamento = ?",
                                     (emprestimo.id_equipamento,), "Equipamento não encontrado.")
            else:
                equipamento = _linha(con, "SELECT * FROM Equipamentos WHERE qr_code_uuid = ?",
                                     (emprestimo.qr_code_uuid,), "Nenhum equipamento com esse QR Code.")
            if not equipamento["ativo"]:
                raise Conflito("O equipamento foi baixado e não pode ser emprestado.")
            if equipamento["status_operacional"] != "DISPONIVEL":
                raise Conflito("O equipamento não está disponível: "
                               f"{STATUS_LEGIVEL.get(equipamento['status_operacional'])}.")

            cursor = con.execute(
                "INSERT INTO Historico_de_Emprestimos (id_usuario, id_equipamento, "
                "data_prevista_devolucao, observacoes) VALUES (?, ?, ?, ?)",
                (emprestimo.id_usuario, equipamento["id_equipamento"],
                 emprestimo.data_prevista_devolucao, emprestimo.observacoes))
            novo_id = cursor.lastrowid
            con.execute("UPDATE Equipamentos SET status_operacional = 'EM_USO' "
                        "WHERE id_equipamento = ?", (equipamento["id_equipamento"],))
        return self.buscar_por_id(novo_id)

    def listar(self, status=None, id_usuario=None, id_equipamento=None, atrasados=False):
        sql, params = self.SELECT + " WHERE 1=1", []
        if status:
            sql += " AND h.status_emprestimo = ?"
            params.append(status.upper())
        if id_usuario:
            sql += " AND h.id_usuario = ?"
            params.append(id_usuario)
        if id_equipamento:
            sql += " AND h.id_equipamento = ?"
            params.append(id_equipamento)
        if atrasados:
            sql += f" AND h.status_emprestimo = 'ATIVO' AND h.data_prevista_devolucao < {AGORA}"
        return [Emprestimo.de_linha(l) for l in self._consultar(sql + " ORDER BY h.id_emprestimo DESC", params)]

    def buscar_por_id(self, id_emprestimo):
        linha = self._consultar(self.SELECT + " WHERE h.id_emprestimo = ?", (id_emprestimo,), um=True)
        if linha is None:
            raise NaoEncontrado("Empréstimo não encontrado.")
        return Emprestimo.de_linha(linha)

    def devolver(self, id_emprestimo):
        with self._transacao() as con:
            emprestimo = _linha(con, "SELECT * FROM Historico_de_Emprestimos WHERE id_emprestimo = ?",
                                (id_emprestimo,), "Empréstimo não encontrado.")
            if emprestimo["status_emprestimo"] != "ATIVO":
                raise Conflito("Este empréstimo já foi encerrado.")
            con.execute(f"UPDATE Historico_de_Emprestimos SET status_emprestimo = 'DEVOLVIDO', "
                        f"data_devolucao = {AGORA} WHERE id_emprestimo = ?", (id_emprestimo,))
            con.execute("UPDATE Equipamentos SET status_operacional = 'DISPONIVEL' "
                        "WHERE id_equipamento = ? AND status_operacional = 'EM_USO'",
                        (emprestimo["id_equipamento"],))
        return self.buscar_por_id(id_emprestimo)


# =====================================================================
# Manutenções
# =====================================================================

class ManutencaoDAO(BaseDAO):

    SELECT = """
        SELECT m.*, e.nome AS nome_equipamento, e.codigo_identificacao,
               u.nome_completo AS nome_responsavel
          FROM Logs_de_Manutencao m
          JOIN Equipamentos e ON e.id_equipamento = m.id_equipamento
          LEFT JOIN Usuarios u ON u.id_usuario = m.id_usuario_responsavel
    """

    def abrir(self, manutencao):
        with self._transacao() as con:
            equipamento = _linha(con, "SELECT * FROM Equipamentos WHERE id_equipamento = ?",
                                 (manutencao.id_equipamento,), "Equipamento não encontrado.")
            if not equipamento["ativo"]:
                raise Conflito("O equipamento foi baixado.")
            if equipamento["status_operacional"] == "EM_USO":
                raise Conflito("O equipamento está emprestado. Registre a devolução antes.")
            if manutencao.id_usuario_responsavel is not None:
                _linha(con, "SELECT 1 FROM Usuarios WHERE id_usuario = ?",
                       (manutencao.id_usuario_responsavel,), "Usuário responsável não encontrado.")

            cursor = con.execute(
                "INSERT INTO Logs_de_Manutencao (id_equipamento, id_usuario_responsavel, "
                "tipo_manutencao, descricao_problema, observacoes) VALUES (?, ?, ?, ?, ?)",
                (manutencao.id_equipamento, manutencao.id_usuario_responsavel,
                 manutencao.tipo_manutencao, manutencao.descricao_problema, manutencao.observacoes))
            novo_id = cursor.lastrowid
            con.execute("UPDATE Equipamentos SET status_operacional = 'EM_MANUTENCAO' "
                        "WHERE id_equipamento = ?", (manutencao.id_equipamento,))
        return self.buscar_por_id(novo_id)

    def listar(self, id_equipamento=None, situacao=None):
        sql, params = self.SELECT + " WHERE 1=1", []
        if id_equipamento:
            sql += " AND m.id_equipamento = ?"
            params.append(id_equipamento)
        if situacao:
            sql += " AND m.situacao_manutencao = ?"
            params.append(situacao.upper())
        return [Manutencao.de_linha(l) for l in self._consultar(sql + " ORDER BY m.id_manutencao DESC", params)]

    def buscar_por_id(self, id_manutencao):
        linha = self._consultar(self.SELECT + " WHERE m.id_manutencao = ?", (id_manutencao,), um=True)
        if linha is None:
            raise NaoEncontrado("Manutenção não encontrada.")
        return Manutencao.de_linha(linha)

    def concluir(self, id_manutencao):
        with self._transacao() as con:
            manutencao = _linha(con, "SELECT * FROM Logs_de_Manutencao WHERE id_manutencao = ?",
                                (id_manutencao,), "Manutenção não encontrada.")
            if manutencao["situacao_manutencao"] == "CONCLUIDA":
                raise Conflito("Esta manutenção já foi concluída.")
            con.execute(f"UPDATE Logs_de_Manutencao SET situacao_manutencao = 'CONCLUIDA', "
                        f"data_conclusao = {AGORA} WHERE id_manutencao = ?", (id_manutencao,))
            abertas = con.execute(
                "SELECT COUNT(*) FROM Logs_de_Manutencao "
                "WHERE id_equipamento = ? AND situacao_manutencao != 'CONCLUIDA'",
                (manutencao["id_equipamento"],)).fetchone()[0]
            if abertas == 0:  # sem outras manutenções abertas, o equipamento volta a ficar disponível
                con.execute("UPDATE Equipamentos SET status_operacional = 'DISPONIVEL' "
                            "WHERE id_equipamento = ? AND status_operacional = 'EM_MANUTENCAO'",
                            (manutencao["id_equipamento"],))
        return self.buscar_por_id(id_manutencao)
