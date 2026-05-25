# CHEVEL AI Architecture

CHEVEL AI is organized as a local cognitive runtime with three main responsibilities:

- understand user intent through chat, voice, and attachments;
- decide and route safe actions;
- expose a stable control contract for Dum-E/U / WIL-E robotics integration.

## Runtime Flow

```txt
User input
  -> Chat API / CLI
  -> Cognitive Core
  -> Memory + World Model + Risk Decision
  -> LLM response and optional action
  -> Controller layer
  -> Local OS, IoT stub, communication stub, or Dum-E/U bridge
```

## Python Domain

Python owns orchestration, persistence, APIs, and integration boundaries.

Key areas:

- `chevel_main.py` starts CLI or FastAPI chat mode.
- `interfaces/chat/server.py` exposes chat, cognitive, health, and Dum-E/U endpoints.
- `core/` contains LLM, memory, decision, reasoning, learning, and monitoring modules.
- `controllers/` contains safe action boundaries for OS, IoT, communication, robotics, and Dum-E/U.
- `utils/` contains configuration, logging, security, and native fallback bridges.

## Cognitive Core

The cognitive core coordinates the MVP modules around every message:

- Fast Thinking receives sensor/reflex data when available.
- World Model snapshots the known environment.
- Goal System can surface safe proactive suggestions.
- Task Reasoning decomposes complex goals.
- Intent Processor detects commands or delegates to the LLM.
- Decision Engine classifies action risk.
- Self Monitor evaluates response confidence.
- Learning System records action-result episodes.

The current implementation is intentionally conservative. It prepares and explains actions, but high-risk robotics commands require confirmation.

## Native C++ Domain

The C++ layer provides deterministic helpers for:

- intent detection;
- program allowlist validation;
- action risk classification;
- vector similarity;
- reflex rule evaluation.

The native service can be built as `native/bin/chevel_core.exe`. When it is not available, Python fallbacks keep the app usable and `/health` reports the native state.

## Dum-E/U Bridge

`controllers/dume_controller.py` defines the current robotics contract in simulation mode:

- arm joints;
- 6D pose;
- gripper state;
- mobile base state;
- battery and safety state;
- emergency stop;
- command gateway;
- telemetry frames.

This bridge is the correct place to connect future hardware adapters. Real hardware adapters should preserve the same safety policy: emergency stop is always allowed, read-only status is safe, and motion requires confirmation.

## Public Interfaces

```txt
GET  /health
POST /api/chat
GET  /api/cognitive/health
GET  /api/cognitive/state
GET  /api/dume/status
GET  /api/dume/capabilities
POST /api/dume/command
POST /api/dume/emergency-stop
WS   /ws/dume/telemetry
```

## Persistence

SQLite is used for local MVP persistence:

- conversations;
- knowledge;
- preferences;
- events;
- world snapshots;
- procedural memory;
- learning episodes;
- goals.

Local databases are ignored by Git.

## Safety Boundary

CHEVEL separates intelligence from physical execution. The LLM can propose actions, but execution goes through deterministic controllers and the decision engine. Robotics motion is treated as high risk by default.
