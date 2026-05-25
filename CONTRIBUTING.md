# Contributing

CHEVEL AI is built as a local cognitive and robotics control layer. Contributions should preserve the safety boundary between intelligence, action planning, and physical execution.

## Development Flow

1. Create a branch from `main`.
2. Keep changes focused.
3. Add or update tests for behavior changes.
4. Run the validation suite.
5. Open a pull request with a clear summary.

## Local Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Optional native C++ build:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_cpp_service.ps1
```

## Safety Rules

- Do not bypass the decision engine for robotics actions.
- Do not make physical movement commands execute without confirmation.
- Keep emergency stop available.
- Keep local databases, logs, toolchains, and secrets out of Git.
- Do not hard-code private machine paths into public docs unless they are setup examples.

## Documentation

Public documentation should explain what the project does, what is implemented, and what is planned. Do not present future hardware adapters as already connected.
