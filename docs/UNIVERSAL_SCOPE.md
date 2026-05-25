# CHEVEL Universal Scope

CHEVEL AI is being shaped as the high-level intelligence and safety layer for
Dum-E/U and WIL-E. The long-term goal is not just a chat assistant. The goal is
a local cognitive system that can understand objectives, reason about the world,
plan safe actions, remember what happened, and control robotics adapters through
clear boundaries.

## Current Foundation

Implemented in this release:

- local chat and API runtime;
- Ollama-backed LLM engine with history;
- SQLite and JSON memory;
- cognitive modules for decision, world state, task reasoning, learning, fast
  reflexes, self monitoring, and goals;
- optional native C++ helper core with Python fallback;
- simulated Dum-E/U bridge with emergency stop and telemetry;
- 5DOF Arduino arm firmware and safe Python controller;
- browser voice controls plus Python voice foundations;
- configuration examples that make local setup explicit without leaking secrets.

## Dum-E/U Direction

Dum-E/U is the advanced robotics target. CHEVEL should own the high-level
control plane:

- parse natural commands;
- decompose complex objectives into subtasks;
- classify risk before action;
- update the world model from sensors;
- keep memory of tasks, failures, and procedures;
- expose APIs for dashboards and adapters;
- require human confirmation for physical actions that can hurt people, damage
  hardware, or alter the environment.

The current Dum-E/U bridge is simulation-only. It is a contract for future real
hardware adapters, not a claim that the full robot is connected today.

## WIL-E Direction

WIL-E is the companion platform direction for navigation, observation,
telemetry, and future mobile behavior. CHEVEL should treat WIL-E as another
adapter behind the same safety and cognitive contracts:

- status and telemetry first;
- emergency stop always available;
- read-only operations allowed;
- movement and manipulation gated by confirmation.

## Capability Boundaries

Implemented means code exists and tests cover the contract.

Hardware-ready means the code path is prepared for local hardware but defaults
to simulation or disabled mode.

Simulated means the public API and safety behavior exist, but no physical
adapter is active.

Planned means the concept belongs to the architecture but should not be marketed
as working runtime.

## Not Active Yet

These remain future adapters until implemented and tested:

- ROS 2 topics for real robot state;
- RGB-D cameras, YOLO, SAM, SLAM, and 6D pose estimation;
- MoveIt motion planning;
- Jetson services;
- real 7DOF industrial arm control;
- real gripper force feedback;
- physical mobile base control.

## Public README Rule

The public README should be ambitious about the direction and precise about the
state. It can say CHEVEL is built to control Dum-E/U/WIL-E safely. It should not
say real motors, perception stacks, or ROS 2 are already connected until those
adapters exist and pass tests.
