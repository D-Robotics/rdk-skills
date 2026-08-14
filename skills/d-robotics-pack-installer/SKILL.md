---
name: d-robotics-pack-installer
description: Install a D-Robotics workspace-integrated Skill Pack (such as OE-Skills-X5 or OE-Skills-S) into a local development project — clone the pack repo, run its setup.sh with a confirmed project root, and verify the installed workspace (.drobotics/ or .horizon/). Use when the user asks to install, initialize, or set up a D-Robotics pack/toolchain for a project ("install D-Robotics OE-Skills-X5", "装一下 OE 工具链", "setup this repo for RDK X5 tool chain work"). 触发词:install OE-Skills、装 OE、setup X5 workspace、初始化 .drobotics、安装 D-Robotics pack、OE 工具链环境搭建. Do not use for installing a single flat skill (npx skills add / pack install.sh) or for editing skill content — those follow the flat-pack flow.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics Skills Team
  tags:
    - installer
    - workspace-pack
    - setup
    - oe
  data-classification: public
---

# D-Robotics Pack Installer

## Purpose

The Hub catalog hosts two kinds of packs. Flat packs (e.g. RDK Device Skills) install skill-by-skill via `npx skills add` or the pack's `install.sh`. Workspace-integrated packs (OE Tool Chain X5, OE Tool Chain S) cannot be installed that way — their skills depend on shared workspace resources (`docs/`, `platforms/`, `scripts/`, `skill-index.json`) laid down by the pack's `setup.sh`. This skill is the Hub's first-class installer for those workspace packs: it locates the pack registration, runs the documented install flow, and verifies the result.

## When to use

Use when the user asks to install / initialize / set up a workspace-integrated D-Robotics pack into a project:

- "Install D-Robotics OE-Skills-X5 into this project"
- "帮我把 OE 工具链装到这个项目"
- "Setup this repo for RDK X5 tool chain work"
- "装一下 OE-Skills-S（S 系列工具链）"

Do not use when:

- The request is a single flat skill install (`npx skills add d-robotics/rdk-skills --skill rdk-diagnostic`, pack `install.sh`) — hand off to the flat pack flow.
- The user only asks what a pack contains or how it works — read `components.d/*.yml` and answer without installing.
- The target pack has no `install_type: workspace` in its registration — then it is a flat pack.

## Instructions

1. **Locate the component.** Read every `components.d/*.yml` in the Hub repo. Match the user's intent against the component `name` and `description`. Confirm the matched component declares `install_type: workspace`; otherwise stop and explain it is a flat pack. Collect: `repo`, `install_script` (default `setup.sh`), and `install_instructions` if present.

2. **Confirm the project root.** Determine the candidate `PROJECT_ROOT`:
   - A directory containing `CLAUDE.md` or `AGENTS.md` in the user's current working tree, else
   - The user's current working directory.
   Always ask the user to confirm the exact `PROJECT_ROOT` before any write. Do not proceed unconfirmed.

3. **Clone the pack.** Shallow-clone to a disposable directory, never into the project:
   ```bash
   git clone --depth 1 https://github.com/<repo>.git <tmp>/<repo>
   ```
   If the clone fails (network/proxy/credentials), report the exact error and stop — do not fabricate results.

4. **Follow the pack's own setup instructions.** If the clone contains `agent-setup.md`, read and follow it. Otherwise run the declared install script:
   ```bash
   bash <tmp>/<repo>/<install_script> <PROJECT_ROOT>
   ```
   Before executing, tell the user what it will write (typically a `.drobotics/` or `.horizon/` workspace plus routing rules injected into `CLAUDE.md` / `AGENTS.md`) and get a final go-ahead.

5. **Verify the install.** Check the pack's declared artifacts exist, e.g. for OE-Skills-X5:
   ```bash
   test -f <PROJECT_ROOT>/.drobotics/X5.md
   test -f <PROJECT_ROOT>/.drobotics/VERSION
   test -f <PROJECT_ROOT>/.drobotics/skill-index.json
   test -f <PROJECT_ROOT>/.drobotics/skills/x5-router/SKILL.md
   ```
   Report which checks passed and failed. On failure, show the failing command and its output, retry at most once, then stop and report.

6. **Clean up.** Remove the temporary clone. Tell the user to **restart the agent session** so the newly installed skills load.

## Safety

- **Never run `setup.sh` (or any write) before the user confirms `PROJECT_ROOT`.** This is a hard gate.
- Show what will be modified (`.drobotics/` files, `CLAUDE.md`/`AGENTS.md` routing injection) and get a second confirmation before executing.
- The installer itself is read-only apart from the clone (temporary dir) and the pack's own install script. No `sudo`, no edits to files outside the confirmed project root.
- Repeated installs are expected to be safe (the packs' setup scripts are documented as idempotent for routing injection), but verify before re-running.
- Network failures are terminal for this flow: report and stop.
