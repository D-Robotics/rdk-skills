# Skill Card: rdk-skill-finder

| Field | Value |
|---|---|
| name | rdk-skill-finder |
| owner | D-Robotics Skills Team |
| license | Apache-2.0 |
| kind | read-only catalog discovery |
| riskLevel | low — returns reviewed registry data and does not install or modify files |
| provenance | Hub-native infrastructure Skill; its bundled index is generated from reviewed `components.d` registrations and documented exceptions |

## Use case

Developers who need a real RDK Skill or workspace pack for an RDK task, rather
than a guessed skill name or installation command.

## Known risks

- A stale, missing, or malformed index could produce unsafe routing. Mitigation:
  the script validates schema version and record fields, then fails closed.
- A discovery result could be mistaken for permission to install. Mitigation:
  the Skill is read-only and workspace actions hand off to the confirmation-gated
  `rdk-pack-installer`.

## References

- Bundled generated index: `references/skill-index.json`
- Search implementation: `scripts/search_catalog.py`
- Evals: `evals/tasks.yaml`
