# CHEVEL Local Memory

This folder is for runtime memory only.

Tracked files in this folder are examples and documentation. Real conversation
history, SQLite databases, generated interaction JSON files, and private user
profile files stay local and are ignored by Git.

## Private User Profile

CHEVEL can load stable user context from:

```text
data/memory/profile.local.json
```

That file is optional and ignored by Git. It is useful for facts that should
shape the assistant across sessions, such as preferred name, language,
communication style, active projects, and safety preferences.

Use `profile.example.json` as a schema reference, then create your local file:

```powershell
Copy-Item data/memory/profile.example.json data/memory/profile.local.json
```

Do not put API keys, passwords, tokens, or private credentials in the profile.
