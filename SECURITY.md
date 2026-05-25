# Security Policy

CHEVEL AI is a local-first control system with robotics integration goals. Security reports should focus on issues that can affect local execution, unsafe command routing, data exposure, or future hardware control boundaries.

## Supported Versions

The `main` branch is the active development line.

## Reporting A Vulnerability

Do not open a public issue for sensitive security reports.

Send a private report through GitHub's security reporting flow when available, or contact the maintainer privately with:

- affected component;
- steps to reproduce;
- expected impact;
- logs or proof of concept without secrets;
- suggested mitigation if known.

## Safety-Sensitive Areas

Reports are especially important for:

- command execution bypasses;
- unsafe robotics command approval;
- emergency stop failures;
- arbitrary file access;
- secret leakage;
- unauthenticated network exposure;
- native C++ crashes with security impact.

## Operational Note

The Dum-E/U bridge currently runs in simulation mode. Future hardware adapters must preserve the existing safety gates and confirmation policy.
