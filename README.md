<p align="center">
  <img src="./docs/assets/chevel-logo.png" alt="CHEVEL AI" width="180" />
</p>

<h1 align="center">CHEVEL AI</h1>

<p align="center">
  <strong>Local cognitive control layer for Dum-E/U, WIL-E, robotics workflows, and safe autonomous operation.</strong>
</p>

<p align="center">
  <a href="https://github.com/macksonvictor/chevel-ai/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/macksonvictor/chevel-ai/actions/workflows/ci.yml/badge.svg" />
  </a>
  <img alt="Version" src="https://img.shields.io/badge/version-v0.2.0-111111" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-111111?logo=python" />
  <img alt="C++" src="https://img.shields.io/badge/C++-Native_Core-111111?logo=cplusplus" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Chat_API-111111?logo=fastapi" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-111111" />
</p>

<p align="center">
  <a href="#overview">Overview</a> |
  <a href="#dumeu--wil-e">Dum-E/U</a> |
  <a href="#product-gallery">Gallery</a> |
  <a href="#capability-matrix">Matrix</a> |
  <a href="#features">Features</a> |
  <a href="#cognitive-core">Cognitive Core</a> |
  <a href="#native-c-core">Native C++</a> |
  <a href="#api">API</a> |
  <a href="#architecture">Architecture</a> |
  <a href="#configuration">Configuration</a> |
  <a href="#local-setup">Local setup</a> |
  <a href="#quality">Quality</a> |
  <a href="#roadmap">Roadmap</a>
</p>

---

## Overview

CHEVEL AI is a local assistant and robotics control brain built around Python orchestration, a deterministic C++ helper core, SQLite/JSON memory, a FastAPI chat interface, voice foundations, Arduino-ready robot control, and a safe Dum-E/U bridge.

The project is designed to turn natural language, voice, and file context into structured decisions, plans, and safe actions for a future physical robotics platform. The current release is a local cognitive robotics foundation: it can chat, remember, inspect cognitive state, classify risk, expose robotics control contracts, simulate Dum-E/U commands, drive a 5DOF Arduino arm controller in safe simulation by default, and block dangerous physical commands until human confirmation is available.

---

## Dum-E/U / WIL-E

The main product direction is integration with **Dum-E/U / WIL-E**: an advanced robotic system with a 7 DOF arm, gripper, mobile base, sensors, telemetry, and future vision/control stacks.

CHEVEL owns the high-level intelligence layer:

- interpret natural commands;
- decompose goals into safe steps;
- track world state and task memory;
- classify risk before actions;
- expose robotics APIs for dashboards and hardware adapters;
- keep emergency stop paths available and conservative.

The current Dum-E/U bridge runs in **safe simulation mode**. It defines the public control contract without claiming that real motors, ROS 2, cameras, SLAM, MoveIt, or Jetson adapters are already connected.

CHEVEL also includes a smaller 5DOF Arduino Mega arm bridge for local robotics experiments. That controller is hardware-ready through serial, but stays simulated unless a local port is explicitly configured.

---

## Product Gallery

### Chat Interface

A minimal dark interface for local chat, file input, voice controls, web mode, and the public `HELI 1.5` model alias.

<p align="center">
  <img src="./docs/assets/screenshots/chat.png" alt="CHEVEL AI chat interface" width="820" />
</p>

---

## Capability Matrix

| Area | Status | What exists now |
| --- | --- | --- |
| Chat and API | Implemented | FastAPI app, WebSocket chat, `/api/chat`, attachments, web mode, `HELI 1.5` public model alias |
| Local LLM | Implemented | Ollama-backed engine with history and offline-safe behavior |
| Memory | Implemented | SQLite memory plus JSON interaction files under `data/memory` |
| Cognitive Core | Implemented | decision, world model, task reasoning, learning, fast thinking, self monitoring, goals |
| Native C++ | Implemented with fallback | Optional helper service for deterministic intent, risk, similarity, and reflex checks |
| Voice | Hardware-ready foundation | Browser voice in the UI plus Python listener/wake-word modules for local setups |
| 5DOF arm | Hardware-ready foundation | Arduino Mega firmware, serial protocol, IK boundary, servo safety limits, simulation default |
| Dum-E/U bridge | Simulated contract | Status, capabilities, command gate, emergency stop, telemetry WebSocket |
| Dum-E/U real hardware | Planned adapter | ROS 2, sensors, MoveIt, RGB-D perception, Jetson and motor controllers are not connected in this release |
| Perception stack | Planned adapter | YOLO/SAM/SLAM/pose estimation are documented direction, not active runtime claims |

---

## Features

### Local Chat

- FastAPI web app with HTTP and WebSocket support.
- Minimal dark interface inspired by modern AI chat tools.
- Text input, image/audio/text attachments, web search toggle, and voice controls.
- Public model display as `HELI 1.5`.

### Memory

- SQLite conversation memory.
- Knowledge, preferences, and event storage.
- Advanced procedural memory for task steps and learned routines.

### Safe Actions

- OS action routing for allowed local tasks.
- IoT, communication, and robotics controller boundaries.
- Risk classification before action execution.
- Human confirmation requirement for high-risk robotics commands.

### Dum-E/U Bridge

- Simulated robotics state for arm, joints, pose, gripper, base, battery, and safety.
- Emergency stop endpoint.
- Command endpoint with confirmation gate.
- Telemetry WebSocket for dashboards and future robot monitoring.

### Voice and 5DOF Arm

- Browser voice controls in the chat UI.
- Python voice modules for SpeechRecognition and Porcupine-style wake word flows.
- Arduino Mega 2560 firmware for 5 servo channels.
- Safe 5DOF controller with cartesian target conversion and servo limit validation.
- Hardware remains opt-in through local config and serial port selection.

---

## Cognitive Core

CHEVEL includes a cognitive pipeline that coordinates the MVP modules around the existing LLM and controller layer:

- Decision Engine for risk-aware action selection.
- World Model for internal environment state.
- Advanced Memory for procedural task knowledge.
- Learning System for action-result episodes.
- Task Reasoning for decomposing complex commands.
- Fast Thinking for reflex-style safety rules.
- Self Monitoring for confidence and failure awareness.
- Goal System for persistent operational priorities.

The cognitive core is intentionally conservative. It can suggest and prepare robotics actions, but high-risk movement remains blocked until explicit confirmation is introduced.

---

## Native C++ Core

The native C++ layer is used for deterministic and fast local routines:

- intent detection;
- allowlisted program validation;
- action risk assessment;
- cosine similarity primitives;
- reflex evaluation for critical sensor states.

If the C++ executable or Python extension is unavailable, CHEVEL keeps running through Python fallbacks and reports native availability through `/health`.

---

## API

Core endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Runtime health, Ollama state, native core, cognitive state, Dum-E/U summary |
| `POST` | `/api/chat` | Main chat route with model, web mode, and attachments |
| `GET` | `/api/cognitive/health` | Cognitive health summary |
| `GET` | `/api/cognitive/state` | World model, goals, fast thinking, and learning state |

Dum-E/U endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dume/status` | Current simulated robotics state |
| `GET` | `/api/dume/capabilities` | Supported command and telemetry contract |
| `POST` | `/api/dume/command` | Safe robotics command gateway |
| `POST` | `/api/dume/emergency-stop` | Emergency stop path |
| `WS` | `/ws/dume/telemetry` | Real-time telemetry stream |

Example Dum-E/U command:

```json
{
  "command": "home",
  "parameters": {},
  "confirm": false,
  "source": "api"
}
```

Without confirmation, motion commands return `requires_confirmation`. Emergency stop remains available.

---

## Architecture

```txt
chevel-ai/
|-- core/
|   |-- cognitive_core.py
|   |-- decision_engine.py
|   |-- fast_thinking.py
|   |-- goal_system.py
|   |-- intent_processor.py
|   |-- learning_system.py
|   |-- llm_engine.py
|   |-- memory_advanced.py
|   |-- memory_system.py
|   |-- self_monitor.py
|   |-- task_reasoning.py
|   `-- world_model.py
|-- controllers/
|   |-- dume_controller.py
|   |-- os_controller.py
|   |-- iot_controller.py
|   |-- comm_controller.py
|   `-- robot_controller.py
|-- interfaces/
|   |-- chat/
|   |   |-- server.py
|   |   `-- web/
|   `-- voice/
|       |-- listener.py
|       `-- wake_word.py
|-- firmware/
|   `-- arduino_mega_5dof/
|-- native/
|   |-- chevel_core.cpp
|   |-- chevel_native.cpp
|   `-- CMakeLists.txt
|-- data/
|   |-- configs/
|   |-- memory/
|   |-- models/
|   `-- workflows/
|-- scripts/
|-- docs/
|-- tests/
|-- utils/
`-- chevel_main.py
```

More detail:

- [Architecture](./docs/ARCHITECTURE.md)
- [Dum-E/U Bridge](./docs/DUME_BRIDGE.md)
- [Safety Model](./docs/SAFETY_MODEL.md)
- [5DOF Robot Arm](./docs/ROBOT_ARM.md)
- [Configuration](./docs/CONFIGURATION.md)
- [Universal Scope](./docs/UNIVERSAL_SCOPE.md)

---

## Configuration

CHEVEL runs without private config files, but the public examples now make the runtime shape explicit.

The repository includes `.env.example` and the local `.env` is ignored. Safe local defaults cover `CHEVEL_PUBLIC_MODEL`, `CHEVEL_MODEL`, `CHEVEL_MAX_HISTORY`, and `OLLAMA_HOST`; secrets such as Porcupine keys should stay only in local env.

Tracked examples live in `data/configs`:

- `chevel.example.json` for model, memory paths, search roots, and allowed programs;
- `voice.example.json` for wake phrase, speech recognition, and TTS defaults;
- `dume.example.json` for the simulated Dum-E/U bridge contract;
- `robot-arm.example.json` for Arduino Mega 5DOF serial defaults;
- `integrations.example.json` for future providers without secrets;
- `safety.example.json` for conservative robotics gates.

Create local private files with the `.local.json` suffix:

```powershell
Copy-Item data/configs/chevel.example.json data/configs/chevel.local.json
```

CHEVEL loads `data/configs/*.local.json`, then `CHEVEL_CONFIG_PATH` when set, then environment variables.

More detail: [Configuration](./docs/CONFIGURATION.md).

---

## Local Setup

### Requirements

- Python 3.11 or newer.
- Ollama installed for local model execution.
- Optional C++ toolchain for the native helper core.

### 1. Enter the project

```powershell
cd C:\END0-SYM\chevel\chevel-ai
```

### 2. Install dependencies

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

### 3. Optional local config

```powershell
Copy-Item .env.example .env
Copy-Item data/configs/chevel.example.json data/configs/chevel.local.json
```

Edit only local files for machine-specific values such as ports, paths, and private integration settings.

### 4. Configure the model

```powershell
$env:CHEVEL_PUBLIC_MODEL="HELI 1.5"
$env:CHEVEL_MODEL="llama3.1:8b"
ollama serve
ollama pull llama3.1:8b
```

### 5. Start CLI

```powershell
.\.venv\Scripts\python.exe chevel_main.py --mode cli
```

### 6. Start chat

```powershell
.\.venv\Scripts\python.exe chevel_main.py --mode chat --host 127.0.0.1 --port 8000
```

Open:

```txt
http://127.0.0.1:8000
```

---

## Quality

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Build the optional C++ service:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_cpp_service.ps1
.\native\bin\chevel_core.exe version
```

CI validates Python tests and required repository governance files.

---

## Roadmap

### Robotics Integration

- Connect ROS 2 topics for joints, pose, camera, LIDAR, battery, and diagnostics.
- Add adapters for embedded hardware APIs, serial controllers, and Jetson services.
- Add hardware confirmation flows for motion commands.

### Perception

- Add RGB-D object detection and pose estimation adapters.
- Prepare world-model updates from real sensor data.
- Add camera and mapping contracts without bypassing safety.

### Voice and Models

- Replace browser speech dependencies with a local ASR/TTS pipeline.
- Introduce dedicated HELI models for language, voice, and multimodal analysis.
- Keep the `HELI 1.5` public model alias stable while backend providers evolve.

### Product

- Improve the robotics dashboard.
- Add telemetry visualization.
- Add confirmation UX for high-risk actions.
- Prepare release documentation for hardware integration phases.

---

## Release Line

`v0.2.0` is the cognitive robotics foundation release: public scope, meaningful configuration examples, voice and 5DOF arm foundations, safe Dum-E/U contracts, and documentation that separates implemented runtime from future hardware adapters.

---

## Support

Use GitHub Issues for public bugs and feature requests that do not include private data or hardware secrets.

For vulnerability reports, read [SECURITY.md](./SECURITY.md).

---

## License

This repository is licensed under the [MIT License](./LICENSE).
