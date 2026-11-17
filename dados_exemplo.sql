-- Dados de exemplo para a apresentacao (datas relativas a "agora")
-- Carregados com:  python python/app.py --exemplo   (somente se o banco estiver vazio)

INSERT INTO Usuarios (nome_completo, email, matricula, perfil) VALUES
  ('Ana Beatriz Souza',   'ana.souza@escola.edu.br',    '2026001', 'ALUNO'),
  ('Carlos Eduardo Lima', 'carlos.lima@escola.edu.br',  '2026002', 'ALUNO'),
  ('Mariana Costa',       'mariana.costa@escola.edu.br','2026003', 'ALUNO'),
  ('Prof. Ricardo Alves', 'ricardo.alves@escola.edu.br','P1001',   'PROFESSOR'),
  ('Prof. Juliana Rocha', 'juliana.rocha@escola.edu.br','P1002',   'PROFESSOR'),
  ('Fernando Martins',    'fernando.martins@escola.edu.br','A0001','ADMINISTRADOR');

INSERT INTO Equipamentos (nome, descricao, categoria, codigo_identificacao, qr_code_uuid, estado_conservacao, status_operacional) VALUES
  ('Notebook Dell Inspiron 15', 'Notebook para aulas de programacao', 'Informatica', 'NB-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0001', 'BOM',    'EM_USO'),
  ('Notebook Lenovo IdeaPad',   'Notebook com Linux instalado',       'Informatica', 'NB-002', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0002', 'OTIMO',  'DISPONIVEL'),
  ('Projetor Epson X49',        'Projetor para salas de aula',        'Audiovisual', 'PJ-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0003', 'BOM',    'EM_USO'),
  ('Projetor BenQ MS535',       'Projetor do auditorio',              'Audiovisual', 'PJ-002', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0004', 'REGULAR','EM_MANUTENCAO'),
  ('Caixa de Som JBL',          'Caixa de som bluetooth',             'Audiovisual', 'CS-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0005', 'BOM',    'DISPONIVEL'),
  ('Kit Arduino Uno',           'Kit com sensores e protoboard',      'Eletronica',  'AR-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0006', 'OTIMO',  'DISPONIVEL'),
  ('Kit ESP32',                 'Placa ESP32 com display',            'Eletronica',  'ES-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0007', 'OTIMO',  'DISPONIVEL'),
  ('Camera Canon T7',           'Camera para o clube de fotografia',  'Audiovisual', 'CM-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0008', 'BOM',    'DISPONIVEL'),
  ('Tablet Samsung Tab A',      'Tablet para atividades em sala',     'Informatica', 'TB-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0009', 'BOM',    'DISPONIVEL'),
  ('Microfone sem fio',         'Microfone de mao com receptor',      'Audiovisual', 'MC-001', '3f0c1b52-8d1a-4c0e-9a55-1d2f6a7b0010', 'RUIM',   'DISPONIVEL');

-- Equipamento 1: emprestimo atrasado | Equipamento 3: emprestimo no prazo
INSERT INTO Historico_de_Emprestimos (id_usuario, id_equipamento, data_retirada, data_prevista_devolucao, status_emprestimo, observacoes) VALUES
  (1, 1, datetime('now','localtime','-4 days'),  datetime('now','localtime','-1 days'), 'ATIVO', 'Trabalho de programacao'),
  (4, 3, datetime('now','localtime','-2 hours'), datetime('now','localtime','+1 days'), 'ATIVO', 'Aula de historia');

-- Emprestimos ja devolvidos (historico)
INSERT INTO Historico_de_Emprestimos (id_usuario, id_equipamento, data_retirada, data_prevista_devolucao, data_devolucao, status_emprestimo) VALUES
  (2, 6, datetime('now','localtime','-9 days'), datetime('now','localtime','-7 days'), datetime('now','localtime','-7 days'), 'DEVOLVIDO'),
  (3, 8, datetime('now','localtime','-6 days'), datetime('now','localtime','-5 days'), datetime('now','localtime','-5 days'), 'DEVOLVIDO'),
  (5, 2, datetime('now','localtime','-5 days'), datetime('now','localtime','-3 days'), datetime('now','localtime','-3 days'), 'DEVOLVIDO');

INSERT INTO Logs_de_Manutencao (id_equipamento, id_usuario_responsavel, tipo_manutencao, descricao_problema, situacao_manutencao, data_abertura, data_conclusao) VALUES
  (4, 6, 'CORRETIVA',  'Lampada queimada, imagem escura',  'ABERTA',    datetime('now','localtime','-1 days'),  NULL),
  (2, 6, 'PREVENTIVA', 'Limpeza e atualizacao do sistema', 'CONCLUIDA', datetime('now','localtime','-10 days'), datetime('now','localtime','-9 days'));
