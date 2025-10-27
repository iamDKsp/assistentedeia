# Assistente de WhatsApp Web

Este projeto fornece um robô em Python capaz de automatizar interações no WhatsApp Web:

- **Login automático** reutilizando sessões do navegador e salvando o QR code exibido pela interface.
- **Leitura de mensagens recebidas** em tempo real a partir de conversas com notificações não lidas.
- **Respostas automáticas personalizadas** com base em palavras-chave, comandos e mensagens genéricas configuráveis.
- **Atraso configurável** entre a detecção e o envio da resposta para simular interação humana.
- **Atendimento simultâneo** a múltiplos chats através do processamento em lote das conversas não lidas.
- **Registro das conversas** em um arquivo JSON line-by-line para auditoria posterior.

## Estrutura do projeto

```
whatsapp_bot/
├── bot.py             # Implementação principal do robô
├── browser.py         # Fabrica de WebDriver do Chrome
├── config.py          # Modelos e utilidades de configuração
├── logger.py          # Persistência de mensagens trocadas
└── responder.py       # Motor de respostas baseadas em palavras-chave
scripts/
└── run_bot.py         # Entrada de linha de comando
config.example.yaml    # Exemplo de configuração
requirements.txt       # Dependências do projeto
```

## Pré-requisitos

1. Python 3.10 ou superior.
2. Google Chrome instalado (necessário para o WebDriver).
3. Dependências Python instaladas:

```bash
pip install -r requirements.txt
```

> **Dica:** o projeto utiliza `webdriver-manager` para baixar o ChromeDriver compatível automaticamente.

## Configuração

Copie o arquivo de exemplo e ajuste às suas necessidades:

```bash
cp config.example.yaml config.yaml
```

### Opções principais (`config.yaml`)

- `session_dir`: diretório onde o perfil do Chrome será salvo. Mantê-lo permite login automático em execuções futuras.
- `qr_output`: caminho do arquivo onde o QR code exibido pelo WhatsApp Web será salvo. Ajuste para `null` para desabilitar.
- `conversation_log`: arquivo que receberá os registros das conversas.
- `implicit_wait`: espera implícita do Selenium em segundos.
- `headless`: define se o Chrome deve ser executado sem interface gráfica.
- `reply.default`: mensagem enviada quando nenhuma palavra-chave é encontrada.
- `reply.faq`: mapa de palavras-chave para respostas específicas.
- `reply.commands`: comandos (por exemplo `/ajuda`) e suas respostas.
- `reply.delay`: intervalo `[min, max]` em segundos para simular o tempo de digitação.

## Execução

```bash
python scripts/run_bot.py config.yaml --log-level INFO
```

Durante a primeira execução será necessário escanear o QR code salvo em `qr_code.png` (ou exibido no navegador). As sessões seguintes reutilizam o perfil armazenado em `session_dir`, evitando novo pareamento.

O robô permanece em loop verificando novas conversas com mensagens não lidas, enviando as respostas configuradas e registrando os diálogos.

## Registro das conversas

Cada interação é gravada em `logs/conversations.log` no formato JSON por linha:

```json
{"contact": "Cliente Exemplo", "message": "Olá!", "direction": "in", "timestamp": "2023-11-21T15:42:00"}
```

Esse arquivo pode ser importado em ferramentas de análise ou sistemas de auditoria.

## Extensibilidade

A arquitetura está preparada para crescimento futuro:

- O módulo `responder` pode ser expandido com novos motores de decisão (por exemplo, integração com IA ou bases de conhecimento).
- O `ConversationLogger` pode ser adaptado para bancos de dados ou serviços externos.
- O `WhatsAppBot` expõe métodos como `process_unread_chats` e `run`, facilitando integrações personalizadas.

## Aviso Legal

Automatizar interações no WhatsApp Web pode violar os termos de uso da plataforma. Utilize este código com responsabilidade e em ambientes controlados.

