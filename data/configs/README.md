# CHEVEL Runtime Configs

This folder documents the local configuration contract for CHEVEL AI.

The repository tracks only `*.example.json` files. Real local files should use
the `*.local.json` suffix and stay private:

```powershell
Copy-Item data/configs/chevel.example.json data/configs/chevel.local.json
Copy-Item data/configs/voice.example.json data/configs/voice.local.json
Copy-Item data/configs/dume.example.json data/configs/dume.local.json
Copy-Item data/configs/robot-arm.example.json data/configs/robot-arm.local.json
```

CHEVEL loads all `data/configs/*.local.json` files, then applies
`CHEVEL_CONFIG_PATH` if it is set, and finally lets environment variables win.

Tracked examples:

- `chevel.example.json`: model, memory paths, search roots, allowed programs.
- `voice.example.json`: browser/local voice defaults and wake phrase.
- `dume.example.json`: safe Dum-E/U bridge mode and telemetry contract.
- `robot-arm.example.json`: 5DOF Arduino/serial defaults.
- `integrations.example.json`: placeholders for future providers without keys.
- `safety.example.json`: conservative safety gates for physical actions.

Do not commit ports, API keys, tokens, real hardware addresses, logs, memory
databases, or private user data.
