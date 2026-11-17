# Modelagem do sistema

Os diagramas abaixo usam Mermaid e aparecem desenhados direto no GitHub.

## Diagrama de classes (UML)

```mermaid
classDiagram
    class Modelo {
        +CAMPOS_ENTRADA
        +de_dict(dados)$ Modelo
        +de_linha(linha)$ Modelo
        +para_dict() dict
        +validar() Modelo
    }
    class Usuario {
        +id_usuario
        +nome_completo
        +email
        +matricula
        +perfil
        +situacao
        +data_cadastro
    }
    class Equipamento {
        +id_equipamento
        +nome
        +descricao
        +categoria
        +codigo_identificacao
        +qr_code_uuid
        +estado_conservacao
        +status_operacional
        +ativo
        +data_cadastro
    }
    class Emprestimo {
        +id_emprestimo
        +id_usuario
        +id_equipamento
        +data_retirada
        +data_prevista_devolucao
        +data_devolucao
        +status_emprestimo
        +observacoes
    }
    class Manutencao {
        +id_manutencao
        +id_equipamento
        +id_usuario_responsavel
        +tipo_manutencao
        +descricao_problema
        +situacao_manutencao
        +data_abertura
        +data_conclusao
        +observacoes
    }
    Modelo <|-- Usuario
    Modelo <|-- Equipamento
    Modelo <|-- Emprestimo
    Modelo <|-- Manutencao

    class BaseDAO {
        #_consultar(sql, params)
        #_transacao()
    }
    class UsuarioDAO {
        +cadastrar(usuario)
        +listar(perfil, situacao)
        +buscar_por_id(id)
        +desativar(id)
    }
    class EquipamentoDAO {
        +cadastrar(equipamento)
        +listar(categoria, status, ativo)
        +buscar_por_id(id)
        +buscar_por_qr(uuid)
        +baixar(id)
    }
    class EmprestimoDAO {
        +emprestar(emprestimo)
        +listar(status, id_usuario, id_equipamento, atrasados)
        +buscar_por_id(id)
        +devolver(id)
    }
    class ManutencaoDAO {
        +abrir(manutencao)
        +listar(id_equipamento, situacao)
        +buscar_por_id(id)
        +concluir(id)
    }
    BaseDAO <|-- UsuarioDAO
    BaseDAO <|-- EquipamentoDAO
    BaseDAO <|-- EmprestimoDAO
    BaseDAO <|-- ManutencaoDAO

    UsuarioDAO ..> Usuario
    EquipamentoDAO ..> Equipamento
    EmprestimoDAO ..> Emprestimo
    ManutencaoDAO ..> Manutencao

    Usuario "1" --> "0..*" Emprestimo : realiza
    Equipamento "1" --> "0..*" Emprestimo : é emprestado em
    Equipamento "1" --> "0..*" Manutencao : recebe
    Usuario "0..1" --> "0..*" Manutencao : é responsável por
```

### Exceções

| Classe | Código HTTP | Quando acontece |
|---|---|---|
| `ErroValidacao` | 400 | Dados ausentes ou inválidos |
| `NaoEncontrado` | 404 | O registro não existe |
| `Conflito` | 409 | Uma regra de negócio impede a operação (ex.: equipamento já emprestado) |

## Diagrama entidade-relacionamento

```mermaid
erDiagram
    Usuarios ||--o{ Historico_de_Emprestimos : realiza
    Equipamentos ||--o{ Historico_de_Emprestimos : "é emprestado em"
    Equipamentos ||--o{ Logs_de_Manutencao : recebe
    Usuarios |o--o{ Logs_de_Manutencao : "é responsável por"

    Usuarios {
        INTEGER id_usuario PK
        TEXT nome_completo
        TEXT email UK
        TEXT matricula UK
        TEXT perfil
        TEXT situacao
        TEXT data_cadastro
    }
    Equipamentos {
        INTEGER id_equipamento PK
        TEXT nome
        TEXT descricao
        TEXT categoria
        TEXT codigo_identificacao UK
        TEXT qr_code_uuid UK
        TEXT estado_conservacao
        TEXT status_operacional
        INTEGER ativo
        TEXT data_cadastro
    }
    Historico_de_Emprestimos {
        INTEGER id_emprestimo PK
        INTEGER id_usuario FK
        INTEGER id_equipamento FK
        TEXT data_retirada
        TEXT data_prevista_devolucao
        TEXT data_devolucao
        TEXT status_emprestimo
        TEXT observacoes
    }
    Logs_de_Manutencao {
        INTEGER id_manutencao PK
        INTEGER id_equipamento FK
        INTEGER id_usuario_responsavel FK
        TEXT tipo_manutencao
        TEXT descricao_problema
        TEXT situacao_manutencao
        TEXT data_abertura
        TEXT data_conclusao
        TEXT observacoes
    }
```

## Valores aceitos nos campos de texto

| Campo | Valores |
|---|---|
| `Usuarios.perfil` | ALUNO, PROFESSOR, ADMINISTRADOR |
| `Usuarios.situacao` | ATIVO, INATIVO |
| `Equipamentos.estado_conservacao` | OTIMO, BOM, REGULAR, RUIM, DANIFICADO |
| `Equipamentos.status_operacional` | DISPONIVEL, EM_USO, EM_MANUTENCAO |
| `Historico_de_Emprestimos.status_emprestimo` | ATIVO, DEVOLVIDO, CANCELADO |
| `Logs_de_Manutencao.tipo_manutencao` | PREVENTIVA, CORRETIVA |
| `Logs_de_Manutencao.situacao_manutencao` | ABERTA, AGUARDANDO_REPARO, CONCLUIDA |

## Regras de negócio

- Só empresta para usuário **ATIVO** e equipamento **ativo** e **DISPONIVEL**; a data prevista de devolução precisa ser futura.
- Ao emprestar, o equipamento passa para **EM_USO**; ao devolver, volta para **DISPONIVEL**.
- Não é possível desativar usuário com empréstimo ativo, nem dar baixa em equipamento emprestado.
- Abrir manutenção coloca o equipamento em **EM_MANUTENCAO** (não é permitido se estiver emprestado); concluir a última manutenção aberta o libera.
- Usuários e equipamentos nunca são apagados (desativação e baixa), para preservar o histórico.
- Cada operação que altera mais de uma tabela roda em uma transação (tudo ou nada).
