# CHEVEL AI

CHEVEL AI e uma inteligencia local para operar, conversar, lembrar contexto e atuar como camada de controle segura para o projeto Dum-E/U / WIL-E.

O objetivo principal e transformar comandos naturais em decisoes, planos e acoes verificaveis para um sistema robotico avancado: braco de 7 DOF, garra, base movel, sensores, telemetria e modulos futuros de visao, ROS 2 e controle fisico.

## Objetivo

CHEVEL nao e apenas um chat. Ele foi estruturado para ser o cerebro operacional do Dum-E/U:

- interpretar comandos por texto, voz e anexos;
- usar um modelo local apresentado como `HELI 1.5`;
- manter memoria e estado do ambiente;
- decidir acoes com regras de risco;
- bloquear comandos fisicos sem confirmacao humana;
- expor APIs para integracao com dashboards, ROS 2, Jetson, microcontroladores e servicos do robo.

## Estado atual

Esta versao roda localmente e entrega:

- chat web escuro e minimalista;
- entrada por texto, imagem, audio e arquivos de texto;
- voz no navegador com escuta e fala quando o browser permite Web Speech API;
- CLI local;
- memoria SQLite;
- motor Ollama local temporario;
- core cognitivo com decisao, mundo, metas, aprendizado, reflexos e monitoramento;
- nucleo C++ opcional para rotinas rapidas e fallback Python;
- ponte Dum-E/U em modo simulado seguro.

## Dum-E/U / WIL-E

A ponte Dum-E/U define o contrato que sera usado pelo hardware real:

- estado do braco, juntas, pose, garra, base, bateria e seguranca;
- parada de emergencia;
- comando home;
- abertura e fechamento de garra;
- movimento por juntas e pose;
- navegacao de base;
- telemetria via WebSocket.

Por seguranca, comandos de movimento ficam em modo simulado e pedem confirmacao antes de qualquer execucao fisica. Adaptadores reais para ROS 2, API embarcada, serial/Arduino, Jetson, visao 3D e controle de motores entram sobre esse contrato.

## Rodar localmente

```powershell
cd C:\END0-SYM\chevel\chevel-ai
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

CLI:

```powershell
.\.venv\Scripts\python.exe chevel_main.py --mode cli
```

Chat web:

```powershell
.\.venv\Scripts\python.exe chevel_main.py --mode chat
```

Acesse:

```text
http://localhost:8000
```

## Modelo local

A interface exibe `HELI 1.5`. Nesta fase, o motor local temporario usa Ollama por baixo.

```powershell
$env:CHEVEL_PUBLIC_MODEL="HELI 1.5"
$env:CHEVEL_MODEL="llama3.2:latest"
ollama serve
ollama pull llama3.2:latest
```

Se o Ollama estiver offline, o sistema continua online e responde com erro amigavel.

## API

Chat e saude:

- `GET /health`
- `POST /api/chat`
- `GET /api/cognitive/health`
- `GET /api/cognitive/state`

Dum-E/U:

- `GET /api/dume/status`
- `GET /api/dume/capabilities`
- `POST /api/dume/command`
- `POST /api/dume/emergency-stop`
- `WS /ws/dume/telemetry`

Exemplo de comando Dum-E/U:

```json
{
  "command": "home",
  "parameters": {},
  "confirm": false,
  "source": "api"
}
```

Sem confirmacao, comandos de movimento retornam `requires_confirmation`. A parada de emergencia e sempre permitida.

## C++ nativo

O nucleo C++ fica em `native` e pode acelerar rotinas deterministicas como intencao, seguranca, similaridade e reflexos. Quando nao estiver compilado, o Python usa fallback seguro.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_cpp_service.ps1
.\native\bin\chevel_core.exe version
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Direcao tecnica

A proxima etapa natural e conectar os adaptadores reais do Dum-E/U:

- ROS 2 topics para juntas, pose, camera, LIDAR, bateria e diagnostico;
- camada de visao com RGB-D, deteccao de objetos, pose 6D e SLAM;
- controle de movimento com trajetoria, torque, PID e colisao;
- ASR/TTS local para substituir dependencias do navegador;
- modelos proprios HELI para linguagem, visao e voz.
