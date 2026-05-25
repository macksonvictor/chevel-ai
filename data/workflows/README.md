# Workflow Registry

This folder documents repeatable CHEVEL routines without storing private user
automation data.

The current release includes a task-reasoning engine with templates such as
pick object, deliver, navigate, inspect, and organize. Public workflow manifests
can describe those routines at a high level. Real learned user workflows should
remain local and private.

Good public workflow files:

- small examples;
- template names and required parameters;
- safety requirements;
- expected controller targets.

Do not commit:

- private schedules;
- personal file paths;
- access tokens;
- logs from real robot runs;
- home, workplace, or camera-derived coordinates.
