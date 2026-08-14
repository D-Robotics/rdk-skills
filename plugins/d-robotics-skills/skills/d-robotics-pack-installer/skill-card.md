# Skill Card: d-robotics-pack-installer

| Field | Value |
|---|---|
| name | d-robotics-pack-installer |
| owner | D-Robotics Skills Team (Hub maintainers) |
| license | Apache-2.0 |
| kind | workflow (installer) |
| riskLevel | medium — clones a repo and runs the pack's setup.sh, which writes `.drobotics/`/`.horizon/` and injects routing rules into `CLAUDE.md`/`AGENTS.md` |
| provenance | Hub-native infrastructure skill, maintained via direct PR in `D-Robotics/rdk-skills` (no components.d upstream) — same pattern as NVIDIA's `nvidia-skill-finder` |

## Use case

Users who want a workspace-integrated D-Robotics pack (OE-Skills-X5, OE-Skills-S) installed into their development project. The Hub discovery plugin ships this skill so that after a single plugin install, an agent can install a whole pack from one sentence.

## Known risks

- The pack's `setup.sh` modifies `CLAUDE.md` / `AGENTS.md` (routing injection). Mitigation: hard confirmation gates before any write.
- Proxy/credential issues can break the clone step. Mitigation: shallow clone to a temp dir, fail loudly with the exact error.
- If a pack's setup script is not idempotent, re-install could duplicate content. Mitigation: packs document idempotent injection; verify before re-running.
- This skill trusts the pack repo it clones. Mitigation: it only installs repos declared in `components.d/*.yml`, which Hub maintainers review.

## References

- Registration schema: `components.d/README.md` in this repo
- Pack install contract: each workspace pack's `agent-setup.md` (e.g. `oe-skills-x5/agent-setup.md`)
- Evals: `evals/tasks.yaml`
