# CHEVEL Configuration

CHEVEL works with safe defaults and does not require private config files. Local
configuration becomes useful when a machine needs custom model names, ports,
paths, voice settings, or future hardware adapter values.

## Loading Order

Runtime config is loaded in this order:

1. code defaults from `utils/config_manager.py`;
2. every `data/configs/*.local.json` file, sorted by filename;
3. the explicit file pointed to by `CHEVEL_CONFIG_PATH`, when set;
4. local `.env` values;
5. exported environment variables such as `CHEVEL_MODEL` and `CHEVEL_PUBLIC_MODEL`.

`.env` values override JSON config files. Exported OS environment variables
override both.

## Environment File

The repository tracks `.env.example` and ignores `.env`.

Safe local defaults:

```env
CHEVEL_PUBLIC_MODEL=HELI 1.5
CHEVEL_MODEL=llama3.1:8b
CHEVEL_MAX_HISTORY=20
OLLAMA_HOST=http://127.0.0.1:11434
```

Optional values such as `PORCUPINE_ACCESS_KEY` and `CHEVEL_WAKE_WORD_PATH`
should be added only to the local `.env` or to your OS environment.

## Public Examples

The repository tracks only examples:

- `data/configs/chevel.example.json`
- `data/configs/voice.example.json`
- `data/configs/dume.example.json`
- `data/configs/robot-arm.example.json`
- `data/configs/integrations.example.json`
- `data/configs/safety.example.json`

Create local files with the `.local.json` suffix:

```powershell
Copy-Item data/configs/chevel.example.json data/configs/chevel.local.json
Copy-Item data/configs/voice.example.json data/configs/voice.local.json
Copy-Item data/configs/dume.example.json data/configs/dume.local.json
Copy-Item data/configs/robot-arm.example.json data/configs/robot-arm.local.json
```

Local files are ignored by Git.

## Core Model

`chevel.local.json` can set the local runtime model while keeping the public UI
name stable:

```json
{
  "core": {
    "public_model_name": "HELI 1.5",
    "ollama_model": "llama3.1:8b",
    "ollama_host": "http://127.0.0.1:11434",
    "max_history": 20
  }
}
```

Equivalent environment override:

```powershell
$env:CHEVEL_PUBLIC_MODEL="HELI 1.5"
$env:CHEVEL_MODEL="llama3.1:8b"
```

## Voice

Voice config describes local intent without claiming that a complete local
ASR/TTS pipeline is active:

```json
{
  "voice": {
    "enabled": false,
    "backend": "browser",
    "language": "pt-BR",
    "wake_phrase": "ola chevel"
  }
}
```

The browser UI can use Web Speech when supported. Python voice modules are
available for local experiments with SpeechRecognition and Porcupine-style wake
word flows.

## Dum-E/U

Dum-E/U config is simulation-first:

```json
{
  "dume": {
    "mode": "simulation",
    "hardware_connected": false,
    "require_confirmation": true,
    "telemetry_interval_sec": 0.25
  }
}
```

Real ROS 2, camera, MoveIt, Jetson, motor, or gripper adapters should connect
behind the existing bridge without weakening the safety policy.

## Robot Arm

The 5DOF arm controller is safe by default:

```json
{
  "robot_arm": {
    "simulate": true,
    "port": "",
    "baudrate": 115200
  }
}
```

Set a serial port only after the Arduino firmware and physical power wiring
have been checked.

## Do Not Commit

Do not commit:

- `*.local.json` files;
- API keys and tokens;
- real hardware IPs or serial ports tied to a private setup;
- logs, memory databases, user conversations, or generated datasets;
- downloaded model weights.
