# Assistente de restaurante com Mistral

Este projeto é um agente conversacional para atendimento de restaurante. Ele conversa no terminal, usa a API da Mistral para decidir quando chamar ferramentas, e executa ações no banco de dados como:

- consultar cardápio
- consultar preços
- verificar horários de funcionamento
- verificar disponibilidade de mesas
- criar, consultar e cancelar reservas

O objetivo é permitir uma experiência de atendimento natural, sem que o usuário precise lidar diretamente com o banco ou a lógica do restaurante.

## Estrutura do projeto

```text
projeto_Mistral/
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   ├── memory.py
│   │   ├── mistral_client.py
│   │   └── prompts.py
│   ├── tools/
│   │   ├── cardapio.py
│   │   ├── horarios.py
│   │   ├── reservas.py
│   │   ├── definitions.py
│   │   └── registry.py
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   └── __init__.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── restaurante.db
├── README.md
└── .venv/
```

## Como funciona

O fluxo básico é:

1. O usuário digita uma mensagem no terminal.
2. O arquivo `app/cli.py` inicia o agente.
3. O agente monta o contexto com:
   - instruções do sistema
   - histórico da conversa
   - mensagem atual
4. Esse texto é enviado para a Mistral.
5. A Mistral decide se:
   - responde diretamente, ou
   - chama uma tool
6. Se ela chamar uma tool, o código executa a ferramenta em Python.
7. O resultado volta para a Mistral.
8. A Mistral responde ao usuário com uma resposta final.

Em outras palavras, o modelo não “faz o trabalho” diretamente no banco. Ele decide qual ação precisa ser executada e o código Python executa essa ação de forma segura.

## Tools disponíveis

As ferramentas definidas no projeto são:

- `consultar_cardapio`
- `consultar_preco`
- `consultar_horario`
- `consultar_disponibilidade`
- `criar_reserva`
- `consultar_reserva`
- `cancelar_reserva`

Essas tools são descritas em `app/tools/definitions.py` e conectadas às funções reais em `app/tools/registry.py`.

## Banco de dados

O projeto usa SQLite. O arquivo do banco está em:

```text
restaurante.db
```

Os modelos principais são:

- `Cardapio`
- `Horario`
- `Mesa`
- `Reserva`

Esses modelos estão definidos em `app/models.py`.

## Pré-requisitos

Você precisa ter instalado:

- Python 3.10 ou superior
- pip
- acesso à API da Mistral com chave válida

## Configuração do ambiente

Crie um arquivo `.env` na raiz do projeto com esse formato:

```env
MISTRAL_API_KEY=sua_chave_real_aqui
MISTRAL_MODEL=mistral-small-latest
DURACAO_RESERVA_MINUTOS=90
```

Você pode usar o arquivo `.env.example` como base.

Observações:

- o arquivo `.env` deve ficar na raiz do projeto
- não use aspas na chave
- não deixe espaços antes/depois do `=`
- use um modelo que esteja disponível para sua conta

## Instalação

Abra o terminal na pasta do projeto e execute:

```powershell
cd "C:\Users\rodri\OneDrive\Documentos\projeto_Mistral"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Testando o projeto

### Rodar no terminal

```powershell
python -m app.cli
```

### Rodar em modo debug

O modo debug mostra as ferramentas que o modelo chama durante a conversa:

```powershell
python -m app.cli --debug
```

### Exemplos de conversa

Tente algo como:

- “Quanto custa o risotto?”
- “Me mostra o cardápio de entradas”
- “O restaurante está aberto hoje às 20h?”
- “Quero reservar para 4 pessoas na sexta às 20:00”
- “Há mesa disponível para amanhã às 19:30?”
- “Consulta a reserva do João”
- “Cancela a reserva 12”

## Como usar o debug

Quando você roda com `--debug`, o código mostra logs detalhados sobre:

- qual tool foi chamada
- quais argumentos foram enviados
- o resultado da tool
- o que a Mistral respondeu

Isso ajuda bastante a entender o funcionamento do agente.

## Troubleshooting

### 1. `ModuleNotFoundError: No module named 'dotenv'`

Isso significa que a dependência do Python não está instalada.

Execute:

```powershell
pip install -r requirements.txt
```

### 2. `MISTRAL_API_KEY não definida`

Verifique se o arquivo `.env` existe e se contém a variável correta.

### 3. Erro 403: `This model is not available in your subscription tier`

Isso indica que a chave funciona, mas o modelo escolhido não está disponível para o seu plano/conta da Mistral.

Tente usar um modelo mais simples, por exemplo:

```env
MISTRAL_MODEL=mistral-small-latest
```

### 4. Erro 429: `Rate limit exceeded`

Isso significa que a sua conta da Mistral está excedendo o limite de chamadas.

O que fazer:

- espere alguns minutos
- reduza o número de requisições
- não execute varias instâncias do projeto ao mesmo tempo

## Dicas importantes

- sempre rode apenas uma instância do CLI por vez
- verifique o `.env` antes de testar
- use `--debug` para acompanhar o comportamento do agente
- se a API estiver limitando, espere e tente novamente

## Resumo

Este projeto usa a Mistral como cérebro do agente e o Python como executor das regras do restaurante. O modelo decide o que fazer, e o código em Python valida e executa as ações no banco de dados, devolvendo o resultado para a conversa final.

A combinação de:

- Mistral
- tools em Python
- SQLite
- terminal interativo

permite criar um assistente prático para restaurante, com pouca lógica “hardcoded” no prompt e muita lógica real executada pelo código.

## Observação sobre acesso à API

A aplicação depende da API da Mistral e do seu plano/conta. Se a autenticação ou o modelo não estiverem disponíveis na sua conta, o agente não consegue responder corretamente mesmo que o código esteja funcionando.

Se o projeto for reproduzido em outra máquina, o passo mais importante é a configuração correta do arquivo `.env`.

---

Se quiser, também posso criar uma versão ainda mais curta desse README, em formato de apresentação, para mandar para amigos ou colocar no GitHub.
