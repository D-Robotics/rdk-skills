#!/usr/bin/env bash
#
# D Robotics Workspace 初始化脚本
#
# 用法: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>
#
# --update  升级模式：已安装且 VERSION 与源一致（未加 --force）时直接跳过；
#           版本不同则以重建方式升级（先删目标目录再铺设，不残留旧文件）。
# --force   配合 --update 忽略版本比较，强制重建。
# --ref     安装来源标签（如 v1.0.0），记录到 .drobotics-s/INSTALLED_REF；
#           省略时回退为资源 VERSION。installer 以它作升级比对锚点。
#
# 将资源铺设到 <project-root>/.drobotics-s/，并向 CLAUDE.md / AGENTS.md
# 注入路由规则。资源位置自适应两种布局：
#   - Pack 仓库根执行：资源在 ./drobotics-s/（本脚本同级子目录）
#   - Hub 镜像目录执行：资源与本脚本同层（rsync 平铺 + setup.sh 覆盖层）
#
set -euo pipefail

command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 1; }

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
        echo "ERROR: --ref 需要一个参数（如 v1.0.0）" >&2
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
if [ -d "$RESOURCE_DIR/drobotics-s" ]; then
  DROBOTICS_SRC="$RESOURCE_DIR/drobotics-s"
else
  DROBOTICS_SRC="$RESOURCE_DIR"
fi
DROBOTICS_DST="$PROJECT_ROOT/.drobotics-s"

if [ ! -d "$DROBOTICS_SRC" ]; then
  echo "ERROR: 找不到资源目录 $DROBOTICS_SRC" >&2
  exit 1
fi

echo "==> Resource:  $RESOURCE_DIR"
echo "==> Project:   $PROJECT_ROOT"
echo "==> Target:    $DROBOTICS_DST"

if [ -f "$DROBOTICS_SRC/VERSION" ]; then
  SRC_VERSION=$(tr -d '\r' < "$DROBOTICS_SRC/VERSION")
else
  SRC_VERSION=""
fi
if [ -f "$DROBOTICS_DST/VERSION" ]; then
  INSTALLED_VERSION=$(tr -d '\r' < "$DROBOTICS_DST/VERSION")
else
  INSTALLED_VERSION=""
fi

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

# ── 1. 铺设 .drobotics-s/ ──────────────────────────────────────────────
mkdir -p "$DROBOTICS_DST"

# docs
if [ -d "$DROBOTICS_SRC/docs" ]; then
  mkdir -p "$DROBOTICS_DST/docs"
  cp -r "$DROBOTICS_SRC/docs/"* "$DROBOTICS_DST/docs/"
  echo "  [ok] docs/    ($(ls "$DROBOTICS_DST/docs" | wc -l) files)"
else
  echo "  [WARN] docs/ 资源目录不存在，跳过" >&2
fi

# skills
if [ -d "$DROBOTICS_SRC/skills" ]; then
  mkdir -p "$DROBOTICS_DST/skills"
  cp -r "$DROBOTICS_SRC/skills/"* "$DROBOTICS_DST/skills/"
  # 跳过含 eval.json 的 test/ 目录（评测用例，不属于用户工作区）
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

# DROBOTICS-S.md
if [ -f "$DROBOTICS_SRC/DROBOTICS-S.md" ]; then
  cp "$DROBOTICS_SRC/DROBOTICS-S.md" "$DROBOTICS_DST/DROBOTICS-S.md"
  echo "  [ok] DROBOTICS-S.md"
else
  echo "  [WARN] DROBOTICS-S.md 不存在，跳过" >&2
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
MARKER='# D Robotics S Workspace Rules'

ROUTING_RULES="$MARKER

If the user request involves D Robotics S-series toolchain related topics
(quantization, compile, deploy, evaluation, training, CLI usage, version issues),
you MUST follow the project rules defined in .drobotics-s/DROBOTICS-S.md.

For D Robotics S-series toolchain related tasks:
- Do NOT guess toolchain APIs or CLI parameters based on general LLM knowledge.
- If uncertain, you MUST retrieve documentation before answering."

INJECTED=0
for file in CLAUDE.md AGENTS.md; do
  target="$PROJECT_ROOT/$file"
  if [ -f "$target" ]; then
    python3 - "$target" "$ROUTING_RULES" <<'PYROUTE'
from pathlib import Path
import re
import sys
path = Path(sys.argv[1])
rules = sys.argv[2]
text = path.read_text()
markers = ['Horizon Workspace Rules', 'D Robotics Workspace Rules', 'D Robotics S Workspace Rules']
# Installed blocks have exactly this bounded sentence structure.
pattern = r"(?m)^# (?:" + "|".join(re.escape(x) for x in markers) + r")\r?\n\r?\nIf the user request involves [^\n]+\n\(quantization, compile, deploy, evaluation, training, CLI usage, version issues\),\n[^\n]+\n\nFor [^\n]+\n- Do NOT guess toolchain APIs or CLI parameters based on general LLM knowledge\.\n- If uncertain, [^\n]+(?:\n|$)"
text = re.sub(pattern, "", text).lstrip("\n")
path.write_text(rules + "\n\n" + text)
PYROUTE
    echo "  [ok] $file (routing refreshed)"
  fi
done
if [ -d "$PROJECT_ROOT/.horizon" ]; then
  echo "  [note] Legacy .horizon/ retained. Review and migrate local board/environment configuration before use."
fi

ERRORS=0
for f in DROBOTICS-S.md skill-index.json VERSION; do
  if [ ! -f "$DROBOTICS_DST/$f" ]; then
    echo "  [FAIL] 缺少 $f" >&2
    ERRORS=$((ERRORS + 1))
  fi
done
if [ ! -d "$DROBOTICS_DST/skills" ] || [ "$(find "$DROBOTICS_DST/skills" -name 'SKILL.md' 2>/dev/null | wc -l)" -eq 0 ]; then
  echo "  [FAIL] skills/ 目录为空" >&2
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -gt 0 ]; then
  echo "==> 安装完成，但有 $ERRORS 个问题，请检查上方输出。" >&2
  exit 1
else
  echo "==> Done. .drobotics-s/ initialized at $DROBOTICS_DST"
fi
