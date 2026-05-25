# Model Registry

This folder is a registry boundary for model metadata, not a place to commit
large model weights.

CHEVEL currently uses Ollama locally through `CHEVEL_MODEL`, with `HELI 1.5`
as the public UI alias. Future HELI-specific language, voice, and multimodal
models should be documented here with small manifest files while the actual
weights remain outside Git.

Tracked files should stay lightweight:

- model manifests;
- adapter notes;
- checksum or source references when they are public.

Ignored files should include:

- downloaded model weights;
- private fine-tunes;
- generated datasets;
- exported binaries above normal repository size.
