# API (rotas Flask)

Todas as respostas são JSON. Datas no formato `AAAA-MM-DD HH:MM` ao enviar (ex.: `2026-11-20 14:30`).
Erros voltam como `{"erro": "mensagem"}` com o código HTTP correspondente (400, 404 ou 409).

| Método | Rota | O que faz |
|---|---|---|
| GET | `/saude` | Confirma que a API fala com o banco |
| POST | `/usuarios` | Cadastra usuário (`nome_completo`, `email`, `matricula`, `perfil`) |
| GET | `/usuarios` | Lista (filtros: `?perfil=`, `?situacao=`) |
| GET | `/usuarios/<id>` | Consulta por id |
| PATCH | `/usuarios/<id>/desativar` | Desativa (não apaga) |
| POST | `/equipamentos` | Cadastra equipamento (`nome`, `categoria`, `codigo_identificacao`, `descricao`, `estado_conservacao`); o UUID do QR Code é gerado sozinho |
| GET | `/equipamentos` | Lista (filtros: `?categoria=`, `?status=`, `?ativo=0\|1`) |
| GET | `/equipamentos/<id>` | Consulta por id |
| GET | `/equipamentos/qr/<uuid>` | Consulta pelo QR Code |
| PATCH | `/equipamentos/<id>/baixar` | Dá baixa (`ativo = 0`) |
| POST | `/emprestimos` | Empresta (`id_usuario`, `id_equipamento` **ou** `qr_code_uuid`, `data_prevista_devolucao`, `observacoes`) |
| GET | `/emprestimos` | Lista (filtros: `?status=`, `?id_usuario=`, `?id_equipamento=`, `?atrasados=1`) |
| GET | `/emprestimos/<id>` | Consulta por id |
| PATCH | `/emprestimos/<id>/devolver` | Registra a devolução |
| POST | `/manutencoes` | Abre manutenção (`id_equipamento`, `tipo_manutencao`, `descricao_problema`, `id_usuario_responsavel`) |
| GET | `/manutencoes` | Lista (filtros: `?id_equipamento=`, `?situacao=`) |
| GET | `/manutencoes/<id>` | Consulta por id |
| PATCH | `/manutencoes/<id>/concluir` | Conclui a manutenção |

## Páginas

| Rota | Página |
|---|---|
| `/` | `index.html` (sistema) |
| `/etiqueta/<id_equipamento>` | Etiqueta imprimível com o QR Code (`templates/etiqueta.html`) |

## Exemplo

```
POST /emprestimos
{"id_usuario": 2, "id_equipamento": 5, "data_prevista_devolucao": "2026-11-20 14:30"}

201 Created
{"id_emprestimo": 6, "id_usuario": 2, "id_equipamento": 5, "status_emprestimo": "ATIVO", ...}
```
