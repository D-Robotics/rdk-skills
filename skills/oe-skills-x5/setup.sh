#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
#
# X5 Workspace 初始化脚本
#
# 用法: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>
#
# --update  升级模式：已安装且 VERSION 与源一致（未加 --force）时直接跳过；
#           版本不同则以重建方式升级（先删目标目录再铺设，不残留旧文件）。
# --force   配合 --update 忽略版本比较，强制重建。
# --ref     安装来源标签（如 v2.1.0），记录到 .drobotics/INSTALLED_REF；
#           省略时回退为资源 VERSION。installer 以它作升级比对锚点。
#
# 将资源铺设到 <project-root>/.drobotics/，并向 CLAUDE.md / AGENTS.md
# 注入路由规则。资源位置自适应两种布局：
#   - Pack 仓库根执行：资源在 ./x5/（本脚本同级子目录）
#   - Hub 镜像目录执行：资源与本脚本同层（rsync 平铺 + setup.sh 覆盖层）
#
set -euo pipefail

RESOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

UPDATE=0
FORCE=0
PROVIDED_REF=""
while [ "$#" -gt 1 ]; do
  case "$1" in
    --update) UPDATE=1; shift ;;
    --force)  FORCE=1; shift ;;
    --ref)
      if [ -z "${2:-}" ]; then
        echo "ERROR: --ref 需要一个参数（如 v2.1.0）" >&2
        exit 2
      fi
      PROVIDED_REF="$2"; shift 2 ;;
    *)
      echo "ERROR: 未知参数: $1" >&2
      echo "用法: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>" >&2
      exit 2 ;;
  esac
done

if [ -z "${1:-}" ] || [ "${1:-}" = "--update" ] || [ "${1:-}" = "--force" ] || [ "${1:-}" = "--ref" ]; then
  echo "ERROR: 缺少参数" >&2
  echo "用法: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>" >&2
  exit 1
fi

if ! PROJECT_ROOT="$(cd "$1" 2>/dev/null && pwd)"; then
  echo "ERROR: 项目目录不存在或无法访问: $1" >&2
  exit 1
fi
if [ -d "$RESOURCE_DIR/x5" ]; then
  DROBOTICS_SRC="$RESOURCE_DIR/x5"
else
  DROBOTICS_SRC="$RESOURCE_DIR"
fi
DROBOTICS_DST="$PROJECT_ROOT/.drobotics"

if [ ! -d "$DROBOTICS_SRC" ]; then
  echo "ERROR: 找不到资源目录 $DROBOTICS_SRC" >&2
  exit 1
fi

echo "==> Resource:  $RESOURCE_DIR"
echo "==> Project:   $PROJECT_ROOT"
echo "==> Target:    $DROBOTICS_DST"

SRC_VERSION=$(cat "$DROBOTICS_SRC/VERSION" 2>/dev/null || true)
INSTALLED_VERSION=$(cat "$DROBOTICS_DST/VERSION" 2>/dev/null || true)

# ── 0. 升级判定（--update）────────────────────────────────────────
if [ "$UPDATE" -eq 1 ]; then
  if [ -n "$INSTALLED_VERSION" ] && [ "$INSTALLED_VERSION" = "$SRC_VERSION" ] && [ "$FORCE" -eq 0 ]; then
    echo "==> Already up to date ($INSTALLED_VERSION). Use --force to rebuild."
    exit 0
  fi
  if [ -n "$INSTALLED_VERSION" ]; then
    echo "==> Upgrade: $INSTALLED_VERSION -> $SRC_VERSION (rebuild, no stale files)"
  elif [ -e "$DROBOTICS_DST" ]; then
    echo "==> Existing workspace without VERSION record; --update rebuilds it"
  else
    echo "==> Fresh install (--update behaves like a normal install)"
  fi
  rm -rf "$DROBOTICS_DST"
fi

# ── 1. 铺设 .drobotics/ ───────────────────────────────────────────────────
mkdir -p "$DROBOTICS_DST"

# docs
if [ -d "$DROBOTICS_SRC/docs" ]; then
  mkdir -p "$DROBOTICS_DST/docs"
  cp -r "$DROBOTICS_SRC/docs/"* "$DROBOTICS_DST/docs/"
  echo "  [ok] docs/    ($(ls "$DROBOTICS_DST/docs" | wc -l) files)"
else
  echo "  [WARN] docs/ 资源目录不存在，跳过" >&2
fi

# platforms
if [ -d "$DROBOTICS_SRC/platforms" ]; then
  mkdir -p "$DROBOTICS_DST/platforms"
  cp -r "$DROBOTICS_SRC/platforms/"* "$DROBOTICS_DST/platforms/"
  echo "  [ok] platforms/"
else
  echo "  [WARN] platforms/ 资源目录不存在，跳过" >&2
fi

# scripts
if [ -d "$DROBOTICS_SRC/scripts" ]; then
  mkdir -p "$DROBOTICS_DST/scripts"
  cp -r "$DROBOTICS_SRC/scripts/"* "$DROBOTICS_DST/scripts/"
  echo "  [ok] scripts/"
else
  echo "  [WARN] scripts/ 资源目录不存在，跳过" >&2
fi

# skills
if [ -d "$DROBOTICS_SRC/skills" ]; then
  mkdir -p "$DROBOTICS_DST/skills"
  cp -r "$DROBOTICS_SRC/skills/"* "$DROBOTICS_DST/skills/"
  # 跳过含 eval.json 的 test/ 目录
  TEST_REMOVED=0
  while IFS= read -r eval_file; do
    rm -rf "$(dirname "$eval_file")"
    TEST_REMOVED=$((TEST_REMOVED + 1))
  done < <(find "$DROBOTICS_DST/skills" -path "*/test/eval.json" 2>/dev/null)
  SKILL_COUNT=$(find "$DROBOTICS_DST/skills" -name "SKILL.md" | wc -l)
  echo "  [ok] skills/  ($SKILL_COUNT skills, $TEST_REMOVED test dirs skipped)"
else
  echo "  [WARN] skills/ 资源目录不存在，跳过" >&2
fi

# X5.md
if [ -f "$DROBOTICS_SRC/X5.md" ]; then
  cp "$DROBOTICS_SRC/X5.md" "$DROBOTICS_DST/X5.md"
  echo "  [ok] X5.md"
else
  echo "  [WARN] X5.md 不存在，跳过" >&2
fi

# skill-index.json
if [ -f "$DROBOTICS_SRC/skill-index.json" ]; then
  cp "$DROBOTICS_SRC/skill-index.json" "$DROBOTICS_DST/skill-index.json"
  echo "  [ok] skill-index.json"
else
  echo "  [WARN] skill-index.json 不存在，跳过" >&2
fi

# VERSION
if [ -f "$DROBOTICS_SRC/VERSION" ]; then
  cp "$DROBOTICS_SRC/VERSION" "$DROBOTICS_DST/VERSION"
  VERSION=$(cat "$DROBOTICS_SRC/VERSION")
  echo "  [ok] VERSION ($VERSION)"
else
  echo "  [WARN] VERSION 不存在，跳过" >&2
fi

# INSTALLED_REF — 安装来源锚点（installer 升级比对用；--ref 缺失时回退 VERSION）
RESOLVED_REF="${PROVIDED_REF:-${SRC_VERSION:-unknown}}"
printf '%s\n' "$RESOLVED_REF" > "$DROBOTICS_DST/INSTALLED_REF"
echo "  [ok] INSTALLED_REF ($RESOLVED_REF)"

# ── 2. 注入路由规则到 CLAUDE.md / AGENTS.md ────────────────────────
MARKER='# X5 Workspace Rules'

ROUTING_RULES="$MARKER

If the user request involves X5 OpenExplorer related topics
(quantization, compile, deploy, evaluation, training, CLI usage, version issues),
you MUST follow the project rules defined in .drobotics/X5.md.

For X5 OpenExplorer related tasks:
- Do NOT guess toolchain APIs or CLI parameters based on general LLM knowledge.
- If uncertain, use .drobotics/scripts/search_local_docs.py to retrieve local documentation before answering."

INJECTED=0
for f in CLAUDE.md AGENTS.md; do
  target="$PROJECT_ROOT/$f"
  if [ -f "$target" ]; then
    if grep -q "$MARKER" "$target"; then
      echo "  [skip] $f (already injected)"
    else
      printf '%s\n\n%s\n' "$ROUTING_RULES" "$(cat "$target")" > "$target"
      echo "  [ok] $f (injected)"
    fi
    INJECTED=$((INJECTED + 1))
  fi
done
if [ "$INJECTED" -eq 0 ]; then
  echo "  [WARN] CLAUDE.md 和 AGENTS.md 都不存在，路由规则未注入" >&2
  echo "         请先创建对应文件后重新执行 setup.sh" >&2
fi

# ── 3. 最终检查 ────────────────────────────────────────────────────
ERRORS=0
for f in X5.md skill-index.json VERSION \
  docs/offline-artifact-delivery.md \
  scripts/search_local_docs.py \
  scripts/validate_x5_skills.py \
  scripts/check_bpu_python_api_version.py \
  scripts/validate_bpu_python_api_skills.py \
  scripts/release_artifacts.py \
  scripts/validate_release_artifacts.py; do
  if [ ! -f "$DROBOTICS_DST/$f" ]; then
    echo "  [FAIL] 缺少 $f" >&2
    ERRORS=$((ERRORS + 1))
  fi
done
if [ ! -d "$DROBOTICS_DST/platforms" ]; then
  echo "  [FAIL] platforms/ 目录缺失" >&2
  ERRORS=$((ERRORS + 1))
fi
if [ ! -d "$DROBOTICS_DST/skills" ] || [ "$(find "$DROBOTICS_DST/skills" -name 'SKILL.md' 2>/dev/null | wc -l)" -eq 0 ]; then
  echo "  [FAIL] skills/ 目录为空" >&2
  ERRORS=$((ERRORS + 1))
fi
for f in \
  platforms/x5/PACK.md \
  platforms/x5/skill-index.json \
  platforms/x5/evals/cases.yaml \
  platforms/x5/schemas/route.schema.json \
  platforms/x5/schemas/plan.schema.json \
  platforms/x5/schemas/artifacts.schema.json \
  platforms/x5/schemas/verification.schema.json \
  platforms/x5/scripts/run_contract.py \
  platforms/x5/scripts/run_ptq.py \
  platforms/x5/assets/runtime-cpp/main.cc \
  skills/x5-router/SKILL.md \
  skills/x5-bpu-python-api/SKILL.md \
  skills/x5-bpu-python-api/references/x5_bpu_pyapi.md; do
  if [ ! -f "$DROBOTICS_DST/$f" ]; then
    echo "  [FAIL] 缺少 $f" >&2
    ERRORS=$((ERRORS + 1))
  fi
done
DROBOTICS_SKILL_COUNT="$(find "$DROBOTICS_DST/skills" -name 'SKILL.md' -type f 2>/dev/null | wc -l | tr -d ' ')"
if [ "$DROBOTICS_SKILL_COUNT" -ne 22 ]; then
  echo "  [FAIL] X5 应安装 22 个 Skill，实际为 $DROBOTICS_SKILL_COUNT" >&2
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "==> 安装完成，但有 $ERRORS 个问题，请检查上方输出。" >&2
  exit 1
else
  echo "==> Done. .drobotics/ initialized at $DROBOTICS_DST"
fi
