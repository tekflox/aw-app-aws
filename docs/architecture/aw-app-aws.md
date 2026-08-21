---
repo: architecture
path: docs/architecture/aw-app-aws.md
source: generated
edited: false
checksum: sha256:582e1af9be6cf994cb741642ad01b9426d5614bfb1a968ac84c4806fb57e7688
---
# AWS CLI

- **repo**: aw-app-aws
- **layer**: app
- **technologies**: python
- **health** (derived): planned

Installs the AWS CLI v2 into the workspace and provides a settings panel for AWS credentials (access key, secret key, region, session token — applied via `aws configure`).

## Connections
- `http` → **aw-workspace** — routes mounted at /api/apps/aws

## MCP tools
_none exposed_

## Requirements
### Salvar credenciais grava no cofre e aplica traduzindo o nome do campo
- Given a janela de config do workspace posta um subconjunto qualquer dos quatro campos (access key, secret key, região, session token)
- When a rota de settings grava cada valor via ctx.secrets.write e repassa (repos/aw-app-aws/aws_app/plugin.py::AwsAppPlugin._build_routes.save_settings:77 → repos/aw-app-aws/aws_app/aws_configure.py::apply_credentials:36)
- Then só os campos preenchidos são aplicados, um POST vazio é no-op devolvendo applied=[], e o nome do campo é traduzido pelo mapa _FIELD_TO_AWS_KEY (repos/aw-app-aws/aws_app/aws_configure.py:12) — aws_default_region vira region, que é como a CLI a chama. Sem a tradução o `aws configure set aws_default_region` grava uma chave que a AWS CLI simplesmente ignora depois, sem reclamar de nada
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-aws/tests/test_aws_configure.py` (passing), `repos/aw-app-aws/tests/test_plugin_routes.py` (passing)

### Falha do aws configure não perde a credencial já guardada
- Given os segredos já foram escritos no cofre e o binário `aws` falha ao aplicá-los (ausente, quebrado, ou perfil inválido)
- When AwsConfigureError sobe de apply_credentials e é capturada na rota (repos/aw-app-aws/aws_app/plugin.py::AwsAppPlugin._build_routes.save_settings:93)
- Then a resposta é ok=True com applied=[] e o texto do erro em "error", e não um 500 — a gravação no cofre já aconteceu antes do try, então o valor da pessoa não se perde por causa de uma CLI quebrada, e a próxima ativação reaplica. O preço é que a UI recebe ok=True num caminho de falha: quem consome precisa olhar "error", e um cliente que só testa ok mostra sucesso para uma configuração que não foi aplicada
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-aws/tests/test_plugin_routes.py` (passing)

### O status inspeciona a config local e nunca chama a AWS
- Given alguém abre a janela do app para saber se as credenciais estão configuradas
- When o status é montado a partir de `aws configure list` (repos/aw-app-aws/aws_app/aws_configure.py::status:49) somado ao que está no cofre (repos/aw-app-aws/aws_app/plugin.py::AwsAppPlugin._build_routes.status:96)
- Then configured sai True só quando a linha access_key existe e não é "&lt;not set&gt;", sem nenhuma chamada de rede à AWS — abrir uma janela de settings não deve custar uma chamada de API nem depender de a conta estar viva. A consequência aceita é que "configured" quer dizer "tem chave escrita aqui", não "a chave funciona": uma credencial revogada segue reportando configured=True
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-aws/tests/test_aws_configure.py` (passing), `repos/aw-app-aws/tests/test_plugin_routes.py` (passing)

### Logout apaga os segredos e deliberadamente não desfaz o profile local
- Given credenciais configuradas e a pessoa clica em Logout/Clear na janela
- When a rota apaga os quatro campos do cofre (repos/aw-app-aws/aws_app/plugin.py::AwsAppPlugin._build_routes.logout:106)
- Then nada resta no cofre, e o profile em ~/.aws fica como está — de propósito, porque o activate só reaplica a partir do cofre, que agora está vazio, e limpar o arquivo seria mexer em algo que o app não escreveu sozinho. É uma escolha com custo real e vale saber dela: depois do logout o `aws` na linha de comando continua autenticado com o que sobrou em disco, então logout aqui não é revogação
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: `repos/aw-app-aws/tests/test_plugin_routes.py` (passing)

### A credencial guardada é reaplicada em toda ativação, não só quando alguém salva
- Given o workspace foi recriado e o container do app subiu limpo, sem ~/.aws, mas com o cofre intacto
- When o app ativa e lê o que está guardado antes de registrar qualquer rota (repos/aw-app-aws/aws_app/plugin.py::AwsAppPlugin.activate:57)
- Then apply_credentials roda com o conteúdo do cofre e uma AwsConfigureError vira log.warning em vez de derrubar a ativação (repos/aw-app-aws/aws_app/plugin.py:62) — é o que faz a credencial sobreviver a uma recriação sem ninguém reabrir a janela, e falhar aqui de forma dura deixaria o app inteiro fora do ar por causa de uma CLI ausente. ATENÇÃO: este caminho não tem teste nenhum — a suíte exercita _build_routes e aws_configure, nunca activate
- intended_status: `not_implemented` · derived health: `not_implemented`
- tests: _none linked_
