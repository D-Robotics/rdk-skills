---
name: rdk-skill-finder
description: Find the real D-Robotics RDK Skill or workspace pack for a task, board platform, or installation type, then return its deterministic install or handoff action. Use for requests such as "which skill handles X5 model quantization?", "find an RDK skill for diagnostics", "what RDK toolchain pack should I use?", or "帮我找 X5 模型量化/编译对应的 Skill". Do not use to install or modify anything directly; use rdk-pack-installer for confirmed workspace-pack installation.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics Skills Team
  tags:
    - rdk
    - discovery
    - catalog
    - routing
  data-classification: public
---

# RDK Skill Finder

## Purpose

Search the bundled, generated RDK catalog and return only registered Skills. It
provides a Hub install command for flat Skills and hands workspace-integrated
records to `rdk-pack-installer`.

## When to use

Use when the user needs to discover the right RDK Skill or workspace pack from
a task description, board/platform term, or exact name. This is especially
useful for X5 toolchain, model quantization, compilation, diagnostics, and
hardware workflow discovery.

Do not use it to install a result, edit a Skill, or answer a general RDK
question when the user has not asked for discovery.

## Instructions

1. Run the bundled search script before recommending any Skill or command:

   ```bash
   python scripts/search_catalog.py QUERY [--pack NAME] [--platform TOKEN] [--install-type flat|workspace] [--limit N]
   ```

2. Read the JSON result. Each match is already ranked deterministically and
   includes its canonical `name`, `description`, catalog location, score, and
   `action`. Use the first match unless the user provides a filter that asks
   for a different result.
3. For a flat result, present the returned `npx skills add` command unchanged.
   For a workspace result, hand off to `rdk-pack-installer`; that Skill owns
   project-root confirmation and all installation writes.
4. If `matches` is empty, say that no registered RDK Skill matched and use the
   `rdk-docs-reference` fallback. Do not invent a Skill, repository, command,
   or pack name.
5. If the script returns `error`, surface the index error and stop. Do not
   guess from stale catalog data.

## Safety

- The finder is read-only: it only reads `references/skill-index.json`.
- Never execute an `action` automatically. Installation requires the user's
  explicit request, and workspace installation must be handled by
  `rdk-pack-installer` with its confirmation gates.
- Treat an unreadable, malformed, or unsupported index as terminal; do not
  substitute manually remembered catalog records.
