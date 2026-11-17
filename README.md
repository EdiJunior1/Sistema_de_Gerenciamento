# Sistema de Empréstimos de Equipamentos Escolares

Projeto Integrado (DWS + POO + BD) — 2º TI.

Sistema web para controlar o empréstimo de equipamentos da escola (notebooks, projetores, kits de eletrônica etc.), com identificação por QR Code, controle de devoluções e atrasos e registro de manutenções.

- **Banco de dados:** SQLite (`schema/emprestimos.db`), criado a partir de `schema/banco.sql`
- **Back-end:** Python 3 com POO (models, DAOs) e Flask
- **Front-end:** HTML, CSS e JavaScript (fetch) consumindo as rotas Flask

## Como rodar

Na pasta raiz do projeto:

```
python -m venv venv
venv\Scripts\activate          (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python python/app.py
```

Abra **http://127.0.0.1:5000** no navegador.

O banco já vem com dados de exemplo. Para recomeçar do zero, apague `schema/emprestimos.db` e rode `python python/app.py --exemplo` (cria o banco e carrega os dados de exemplo) ou apenas `python python/app.py` (banco vazio).

## Estrutura do repositório

```
index.html              página principal do sistema (front-end)
requirements.txt        dependências (Flask, segno)
README.md
docs/                   modelagem (diagramas) e documentação da API
python/
  app.py                aplicação Flask: rotas e tratamento de erros
  dao.py                conexão com o banco e DAOs (todo o SQL fica aqui)
  models.py             classes das entidades, validações e exceções
schema/
  banco.sql             modelo físico (CREATE TABLE)
  dados_exemplo.sql     dados para a apresentação
  emprestimos.db        banco SQLite
static/
  css/estilo.css        estilos do front-end
  js/app.js             lógica do front-end (fetch nas rotas Flask)
templates/
  etiqueta.html         página imprimível com o QR Code do equipamento
```

Fluxo de uma requisição: **front-end (fetch)** → **rota Flask** → **model** (valida) → **DAO** (SQL) → **JSON** → front-end.

## Funcionalidades

- Cadastro de usuários (aluno, professor, administrador) e desativação sem perder o histórico
- Cadastro de equipamentos com QR Code gerado automaticamente e etiqueta para impressão
- Empréstimo por seleção na lista ou pelo código lido do QR Code, com regras: usuário ativo, equipamento disponível e data de devolução futura
- Devolução, controle de atrasos e histórico completo
- Abertura e conclusão de manutenções, que bloqueiam e liberam o equipamento
- Baixa de equipamentos (não apaga, preserva o histórico)
- Painel com resumo da situação geral

Os diagramas (classes e entidade-relacionamento) estão em [`docs/modelagem.md`](docs/modelagem.md) e a lista de rotas em [`docs/api.md`](docs/api.md).
