# Safety Model

CHEVEL AI is designed as a local control brain with a conservative execution boundary.

## Principles

- Natural language is never treated as direct hardware permission.
- LLM output can suggest actions, but controllers decide what can run.
- Read-only actions are preferred when uncertainty is high.
- Emergency stop must remain available.
- Physical motion requires confirmation.

## Risk Levels

| Risk | Behavior |
| --- | --- |
| `seguro` | Can run automatically when it is read-only or protective |
| `baixo` | Can run when scoped and allowlisted |
| `medio` | May require confirmation depending on command |
| `alto` | Requires human confirmation |
| `critico` | Always blocked until explicit human handling |

## Robotics Policy

Dum-E/U motion commands are high risk by default. The MVP runs them in simulation mode and returns `requires_confirmation` for physical movement commands.

Allowed without confirmation:

- status;
- capabilities;
- diagnostics;
- emergency stop.

Requires confirmation:

- home;
- joint movement;
- pose movement;
- gripper movement;
- navigation;
- pick, place, and deliver commands.

## Native Core And Fallback

The optional C++ core can classify intent, validate allowed programs, assess risk, and evaluate reflexes. If it is unavailable, Python fallback logic keeps the app operational and conservative.

## Future Hardware Rule

Any real adapter for ROS 2, serial, Jetson, or motor control must preserve this policy and must not bypass `DecisionEngine` or the Dum-E/U bridge.
