"""Models: classes das entidades e das exceções do sistema (POO).

Cada model sabe ler os dados recebidos (de_dict), validar (validar) e se
transformar em dicionário para virar JSON (para_dict).
"""
import re
from datetime import datetime


# =====================================================================
# Exceções (o app.py transforma cada uma em uma resposta JSON)
# =====================================================================

class ErroDeNegocio(Exception):
    """Base das exceções do sistema. 'status' é o código HTTP da resposta."""
    status = 400


class ErroValidacao(ErroDeNegocio):
    status = 400  # dados inválidos


class NaoEncontrado(ErroDeNegocio):
    status = 404  # registro não existe


class Conflito(ErroDeNegocio):
    status = 409  # regra de negócio impede a operação


# =====================================================================
# Funções auxiliares de validação
# =====================================================================

FORMATOS_DATA = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S")
FORMATO_BANCO = "%Y-%m-%d %H:%M:%S"
REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def limpar(valor):
    """Tira espaços das pontas; texto vazio vira None."""
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def obrigatorio(valor, campo):
    if valor is None:
        raise ErroValidacao(f"O campo {campo} é obrigatório.")
    return valor


def inteiro(valor, campo, obrigatorio_=True):
    if valor is None:
        if obrigatorio_:
            raise ErroValidacao(f"O campo {campo} é obrigatório.")
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ErroValidacao(f"O campo {campo} deve ser um número inteiro.")


def escolha(valor, campo, opcoes):
    valor = str(obrigatorio(valor, campo)).upper()
    if valor not in opcoes:
        raise ErroValidacao(f"O campo {campo} deve ser um destes: {', '.join(opcoes)}.")
    return valor


def converter_data(valor, campo):
    valor = str(obrigatorio(valor, campo))
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue
    raise ErroValidacao(f"O campo {campo} deve estar no formato AAAA-MM-DD HH:MM.")


# =====================================================================
# Models
# =====================================================================

class Modelo:
    """Classe-base: converte entre dicionários e objetos."""
    CAMPOS_ENTRADA = ()  # campos que o cliente pode enviar

    @classmethod
    def de_dict(cls, dados):
        """Cria o objeto a partir do JSON recebido (ignora campos desconhecidos)."""
        objeto = cls()
        for campo in cls.CAMPOS_ENTRADA:
            setattr(objeto, campo, limpar(dados.get(campo)))
        return objeto

    @classmethod
    def de_linha(cls, linha):
        """Cria o objeto a partir de uma linha do banco (inclui colunas extras de JOIN)."""
        objeto = cls()
        objeto.__dict__.update(linha)
        return objeto

    def para_dict(self):
        return dict(vars(self))

    def validar(self):
        return self


class Usuario(Modelo):
    PERFIS = ("ALUNO", "PROFESSOR", "ADMINISTRADOR")
    CAMPOS_ENTRADA = ("nome_completo", "email", "matricula", "perfil")

    def validar(self):
        self.nome_completo = obrigatorio(self.nome_completo, "nome_completo")
        self.email = str(obrigatorio(self.email, "email")).lower()
        if not REGEX_EMAIL.match(self.email):
            raise ErroValidacao("O e-mail informado não é válido.")
        self.matricula = obrigatorio(self.matricula, "matricula")
        self.perfil = escolha(self.perfil or "ALUNO", "perfil", self.PERFIS)
        return self


class Equipamento(Modelo):
    ESTADOS = ("OTIMO", "BOM", "REGULAR", "RUIM", "DANIFICADO")
    CAMPOS_ENTRADA = ("nome", "descricao", "categoria", "codigo_identificacao", "estado_conservacao")

    def validar(self):
        self.nome = obrigatorio(self.nome, "nome")
        self.categoria = obrigatorio(self.categoria, "categoria")
        self.codigo_identificacao = obrigatorio(self.codigo_identificacao, "codigo_identificacao")
        self.estado_conservacao = escolha(self.estado_conservacao or "BOM", "estado_conservacao", self.ESTADOS)
        return self


class Emprestimo(Modelo):
    CAMPOS_ENTRADA = ("id_usuario", "id_equipamento", "qr_code_uuid",
                      "data_prevista_devolucao", "observacoes")

    def validar(self):
        self.id_usuario = inteiro(self.id_usuario, "id_usuario")
        self.id_equipamento = inteiro(self.id_equipamento, "id_equipamento", obrigatorio_=False)
        if self.id_equipamento is None and not self.qr_code_uuid:
            raise ErroValidacao("Informe id_equipamento ou qr_code_uuid.")
        prevista = converter_data(self.data_prevista_devolucao, "data_prevista_devolucao")
        if prevista <= datetime.now():
            raise ErroValidacao("A data prevista de devolução deve ser futura.")
        self.data_prevista_devolucao = prevista.strftime(FORMATO_BANCO)
        return self


class Manutencao(Modelo):
    TIPOS = ("PREVENTIVA", "CORRETIVA")
    CAMPOS_ENTRADA = ("id_equipamento", "tipo_manutencao", "descricao_problema",
                      "id_usuario_responsavel", "observacoes")

    def validar(self):
        self.id_equipamento = inteiro(self.id_equipamento, "id_equipamento")
        self.tipo_manutencao = escolha(self.tipo_manutencao, "tipo_manutencao", self.TIPOS)
        self.descricao_problema = obrigatorio(self.descricao_problema, "descricao_problema")
        self.id_usuario_responsavel = inteiro(self.id_usuario_responsavel,
                                              "id_usuario_responsavel", obrigatorio_=False)
        return self
