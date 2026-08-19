#!/usr/bin/env bash

set -euo pipefail

: "${LINARO_GCC_ROOT:?Set LINARO_GCC_ROOT to the Arm GNU Toolchain root}"
: "${X5_DNN_ROOT:?Set X5_DNN_ROOT to the X5 dnn SDK root}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${1:-$SCRIPT_DIR/build-arm}"

if [ -e "$BUILD_DIR" ]; then
  echo "ERROR: build directory already exists: $BUILD_DIR" >&2
  exit 2
fi

cmake -S "$SCRIPT_DIR" -B "$BUILD_DIR" \
  -DCMAKE_C_COMPILER="$LINARO_GCC_ROOT/bin/aarch64-none-linux-gnu-gcc" \
  -DCMAKE_CXX_COMPILER="$LINARO_GCC_ROOT/bin/aarch64-none-linux-gnu-g++" \
  -DX5_DNN_ROOT="$X5_DNN_ROOT"
cmake --build "$BUILD_DIR" --parallel
