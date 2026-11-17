-- Projeto Integrado - Modelo Fisico (SQLite)
-- Sistema de Gerenciamento de Emprestimos de Equipamentos Escolares

CREATE TABLE IF NOT EXISTS Usuarios (
  id_usuario    INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_completo TEXT NOT NULL,
  email         TEXT NOT NULL UNIQUE,
  matricula     TEXT NOT NULL UNIQUE,
  perfil        TEXT NOT NULL DEFAULT 'ALUNO',
  situacao      TEXT NOT NULL DEFAULT 'ATIVO',
  data_cadastro TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS Equipamentos (
  id_equipamento       INTEGER PRIMARY KEY AUTOINCREMENT,
  nome                 TEXT NOT NULL,
  descricao            TEXT,
  categoria            TEXT NOT NULL,
  codigo_identificacao TEXT NOT NULL UNIQUE,
  qr_code_uuid         TEXT NOT NULL UNIQUE,
  estado_conservacao   TEXT NOT NULL DEFAULT 'BOM',
  status_operacional   TEXT NOT NULL DEFAULT 'DISPONIVEL',
  ativo                INTEGER NOT NULL DEFAULT 1,
  data_cadastro        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS Historico_de_Emprestimos (
  id_emprestimo           INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario              INTEGER NOT NULL,
  id_equipamento          INTEGER NOT NULL,
  data_retirada           TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  data_prevista_devolucao TEXT NOT NULL,
  data_devolucao          TEXT,
  status_emprestimo       TEXT NOT NULL DEFAULT 'ATIVO',
  observacoes             TEXT,
  FOREIGN KEY (id_usuario)     REFERENCES Usuarios (id_usuario),
  FOREIGN KEY (id_equipamento) REFERENCES Equipamentos (id_equipamento)
);

CREATE TABLE IF NOT EXISTS Logs_de_Manutencao (
  id_manutencao          INTEGER PRIMARY KEY AUTOINCREMENT,
  id_equipamento         INTEGER NOT NULL,
  id_usuario_responsavel INTEGER,
  tipo_manutencao        TEXT NOT NULL,
  descricao_problema     TEXT NOT NULL,
  situacao_manutencao    TEXT NOT NULL DEFAULT 'ABERTA',
  data_abertura          TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  data_conclusao         TEXT,
  observacoes            TEXT,
  FOREIGN KEY (id_equipamento)         REFERENCES Equipamentos (id_equipamento),
  FOREIGN KEY (id_usuario_responsavel) REFERENCES Usuarios (id_usuario)
);
