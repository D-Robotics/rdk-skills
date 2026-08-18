# Skill Card: rdk-pack-installer

| Field | Value |
|---|---|
| name | rdk-pack-installer |
| owner | D-Robotics Skills Team (Hub maintainers) |
| license | Apache-2.0 |
| kind | workflow (installer) |
| riskLevel | medium — clones a repo and runs the pack's setup.sh, which writes `.drobotics/`/`.horizon/` and injects routing rules into `CLAUDE.md`/`AGENTS.md` |
| provenance | Hub-native infrastructure skill, maintained via direct PR in `D-Robotics/rdk-skills`; its bundled registry is generated from reviewed workspace-pack registrations |

## Use case

Users who want a workspace-integrated D-Robotics pack (OE-Skills-X5, OE-Skills-S) installed into their development project. The Hub discovery plugin ships this skill so that after a single plugin install, an agent can install a whole pack from one sentence.

## Known risks

- The pack's `setup.sh` modifies `CLAUDE.md` / `AGENTS.md` (routing injection). Mitigation: hard confirmation gates before any write.
- Proxy/credential issues can break the clone step. Mitigation: shallow clone to a temp dir, fail loudly with the exact error.
- If a pack's setup script is not idempotent, re-install could duplicate content. Mitigation: packs document idempotent injection; verify before re-running.
- This skill trusts the pack repo it clones. Mitigation: it only installs repos declared in its bundled registry, which Hub maintainers generate from reviewed workspace-pack registrations.

## References

- Bundled registry: `references/pack-registry.json`
- Pack install contract: each workspace pack's `agent-setup.md` (e.g. `oe-skills-x5/agent-setup.md`)
- Evals: `evals/tasks.yaml`
