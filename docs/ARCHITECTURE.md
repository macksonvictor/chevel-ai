# CHEVEL AI Architecture

CHEVEL is split into two equal domains.

## Python Domain

Python owns orchestration and I/O:

- FastAPI and WebSocket chat server.
- Browser UI assets.
- Ollama HTTP client and prompt context.
- SQLite memory persistence.
- Controller routing for OS, IoT, communication, and robot stubs.

## C++ Domain

C++ owns deterministic local core logic:

- Fast intent detection for local actions.
- Security validation for allowed programs.
- Vector math and similarity search primitives.
- Future hardware-facing control loops for robotics/IoT.

Python imports the C++ domain through `chevel_native` using `pybind11`. If the
native module is not compiled yet, the app remains usable through Python
fallbacks, but `/health` reports `native.available=false`.

## Build Requirement

On Windows, the C++ domain requires Visual Studio Build Tools with the C++ tools
or another compiler compatible with Python extension modules.
