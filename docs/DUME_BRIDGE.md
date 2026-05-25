# Dum-E/U Bridge

The Dum-E/U bridge is the control contract between CHEVEL AI and the future robotics platform.

The current implementation is safe simulation. It exists to stabilize APIs, state shape, telemetry, and safety behavior before real hardware adapters are connected.

## State Model

`GET /api/dume/status` returns:

- platform name;
- simulation or safe-stop mode;
- hardware connection flag;
- emergency stop state;
- 7 joint values;
- 6D end-effector pose;
- gripper state and force;
- mobile base pose;
- battery state;
- safety flags;
- last command.

## Capabilities

`GET /api/dume/capabilities` describes:

- supported commands;
- telemetry fields;
- future adapter targets;
- safety policy.

## Command Gateway

`POST /api/dume/command`

```json
{
  "command": "home",
  "parameters": {},
  "confirm": false,
  "source": "api"
}
```

Read-only commands are allowed. Motion commands return `requires_confirmation` unless `confirm` is true. This keeps the public contract useful while preventing accidental physical execution once real adapters exist.

## Emergency Stop

`POST /api/dume/emergency-stop`

Emergency stop is always allowed. It switches the simulated platform into `safe_stop`, clears motion, and marks `emergency_stop` as true.

## Telemetry

`WS /ws/dume/telemetry` emits periodic telemetry frames for dashboards and future monitoring tools.

## Hardware Adapter Direction

Future adapters should attach behind the bridge instead of changing the public API:

- ROS 2 topics;
- embedded REST service;
- serial or Arduino control;
- Jetson perception service;
- motor and gripper controller APIs.

Adapters must keep the same safety model: status is safe, emergency stop is always available, and motion requires confirmation.
