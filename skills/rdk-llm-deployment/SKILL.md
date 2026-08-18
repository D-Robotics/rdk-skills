---
name: rdk-llm-deployment
description: Run on-device LLM / VLM chat and the voice stack (ASR→LLM→TTS, plus the xiaozhi 小智 assistant) on D-Robotics RDK boards. Covers hobot_llamacpp GGUF LLM/VLM on X5/S100, the S600 oellm_runtime / D-Robotics_LLM_S600 SDK path, the legacy hobot_llm on X3, and sensevoice_ros2 + hobot_tts. Use whenever the user wants a chatbot / 看图问答 / 语音助手 on the board, asks which LLM/VLM a board can run, or hits a board↔stack mismatch (e.g. trying hobot_llamacpp on S600). 触发词:端侧大模型、在板上跑 LLM、llama.cpp BPU、GGUF、hobot_llamacpp、InternVL、SmolVLM、Qwen3、VLM 看图问答、语音助手、小智、xiaozhi、语音识别、ASR、sensevoice、语音合成、TTS、hobot_tts、hobot_llm、oellm、S600 跑大模型。Routing — robot ACTION policies (VLA / Pi0 / LeRobot) → rdk-embodied-lerobot; ready-made vision detection/classification/segmentation + CLIP perception models → rdk-model-zoo; "can THIS board even run an LLM" sizing/expectation only → rdk-ecosystem; ROS2 env setup → rdk-tros-setup.
version: 1.0.0
license: Apache-2.0
---

# RDK On-Device LLM / VLM / Voice Deployment

Get a chatbot, a vision-language model, or a full voice assistant running **on the board** (not in the cloud). The single most important fact: **the runtime stack is chosen by the board, and the two stacks do not overlap** — `hobot_llamacpp` is the X5/S100 path, and **S600 uses a completely different runtime (`oellm_runtime` from the D-Robotics_LLM_S600 SDK)**. Pick the stack from the board first; everything else follows.

> Sources: official D-Robotics repos [hobot_llamacpp](https://github.com/D-Robotics/hobot_llamacpp), [hobot_llm](https://github.com/D-Robotics/hobot_llm), [sensevoice_ros2](https://github.com/D-Robotics/sensevoice_ros2), [hobot_tts](https://github.com/D-Robotics/hobot_tts), [xiaozhi-in-rdk](https://github.com/D-Robotics/xiaozhi-in-rdk), [oellm_server](https://github.com/D-Robotics/oellm_server); plus rdk_s_doc `LLM_Toolchain` (S100/S600) and the rdk_doc `hobot_llm` (Bloom) page. Facts verified against these on 2026-06; model lists track the repos / HuggingFace at that time.

## Board → stack cheat-sheet (decide this first)

| Board | On-device LLM/VLM stack | Runtime | Artifact / model format | Notes |
|-------|------------------------|---------|-------------------------|-------|
| **RDK X5** | `hobot_llamacpp` | llama.cpp (tag `b4749`) + BPU | GGUF (`-GGUF-BPU`) + ViT encoder `.bin` | 1–2B VLM fluent; Ubuntu 22.04 + Humble |
| **RDK S100 / S100P** | `hobot_llamacpp` **or** `oellm_runtime` (D-Robotics_LLM_S100 SDK) | llama.cpp + BPU / `libxlm.so` | GGUF + ViT encoder `.hbm`, or `.hbm` (march `nash-e` S100 / `nash-m` S100P) | bigger RAM → up to InternVL3-8B; Ubuntu 22.04 + Humble |
| **RDK S600** | **`oellm_runtime` ONLY** (D-Robotics_LLM_S600 SDK) | `libxlm.so` (OE-LLM / LeapLLM) | `.hbm` (march `nash-p`) | **NOT hobot_llamacpp** — no S600 build flag; Ubuntu 24.04 + Jazzy |
| **RDK X3 (4GB)** | `hobot_llm` (legacy, apt) | hobot-dnn | Bloom 1.4B tar from `archive.d-robotics.cc` | 4GB RAM only; Ubuntu 20.04/22.04 |
| **RDK Ultra / X3 (2GB)** | — | — | — | No first-party on-device LLM path |

Voice stack (`sensevoice_ros2` ASR, `hobot_tts` TTS, `xiaozhi-in-rdk`) is board-agnostic apt/Python — see Workflow 4.

> **Verify the current board state** — run `bash scripts/llm_env_check.sh` for structured JSON (`board_id`, `mem_total`, `llm_packages`, `recommended_stack`). Confirm the board matches the expected stack before starting; catch mismatches (e.g. hobot_llamacpp on S600) early.

## The mismatch that wastes the most time

When a user says *"I'm trying to build hobot_llamacpp on my S600"* / *"-DPLATFORM_S600 fails"* / *"S600 上 colcon 编译 hobot_llamacpp 报错"* — **stop them immediately**. `hobot_llamacpp`'s only build flags are `-DPLATFORM_X5` and `-DPLATFORM_S100`; **there is no S600 path in this repo**. S600 on-device LLM/VLM runs on the **D-Robotics_LLM_S600 SDK** (`oellm_runtime`, `libxlm.so`, `.hbm` march `nash-p`). Redirect to Workflow 2, do not debug the build.

## Workflows

### Workflow 1 — hobot_llamacpp GGUF LLM/VLM (X5 / S100 / S100P)

**Use when:** chatbot / VLM 看图问答 on X5 or S100, "InternVL / SmolVLM on RDK", llama.cpp on BPU.

1. **Pick the model** by board (HuggingFace `D-Robotics`, `-GGUF-BPU` suffix; use the **full repo slug** — short names won't resolve):
   - **X5:** `InternVL2_5-1B`, `InternVL3-1B/2B-Instruct`, `SmolVLM2-256M/500M-Video-Instruct`.
   - **S100/S100P:** all of the above **+ `InternVL3-8B-Instruct`** (more RAM).
   - **Pure LLM (no vision):** any GGUF model from HuggingFace.
2. **Build (on-board or cross-compile)** — full build commands (llama.cpp b4749 + colcon with `-DPLATFORM_X5`/`-DPLATFORM_S100`) → [llm-build-commands.md](references/llm-build-commands.md) §1. ROS deps: `dnn_node`, `cv_bridge`, `sensor_msgs`, `hbm_img_msgs`, `ai_msgs`.
3. **Get the model files.** Each **VLM needs TWO files**: a vision/ViT encoder **+** the language GGUF. The encoder format is **board-specific**: X5 uses `.bin`, S100 uses `.hbm`.
4. **Run** — `feed_type` 0=local-image VLM / 1=subscribed-image VLM / 2=subscribed LLM; `model_type` 0=InternVL / 1=SmolVLM. Full run commands + node params → [llm-build-commands.md](references/llm-build-commands.md) §2. On **S100** add the `.hbm` encoder: `-p model_file_name:=vit_model_int16.hbm`.
5. **Verify** — text output on topic `/llama_cpp_node`; intermediate (TTS-feedable) text on `/tts_text`. Drive prompts live by publishing `std_msgs/String` to `/prompt_text`.

Full parameter matrix (InternVL / SmolVLM / pure-LLM, X5 vs S100, exec vs launch) → [llm-voice-stack.md](references/llm-voice-stack.md) §1.

**验证:** `ros2 topic echo /llama_cpp_node` returns text output; `bash scripts/llm_env_check.sh` confirms `recommended_stack` matches the board (X5/S100 → hobot_llamacpp); intermediate text on `/tts_text` is non-empty.

### Workflow 2 — S600 on-device LLM/VLM (oellm_runtime SDK)

**Use when:** any LLM/VLM/ASR on **S600**, or the user tried hobot_llamacpp on S600.

1. **Get the SDK + manual** (per-board run steps live in the manual, not on GitHub) — download URLs + `oellm_server` setup → [llm-build-commands.md](references/llm-build-commands.md) §3.
2. **Supported models (D-Robotics_LLM_S600 1.0.2):** LLM = DeepSeek-R1-Distill-Qwen-1.5B, Qwen3-0.6B/1.7B/4B/8B; VLM = Qwen2.5-VL-3B/7B-Instruct, Qwen3-VL-2B/4B/8B-Instruct, InternVL2-2B; VLA = Pi0; ASR = whisper-medium.
3. **Pre-compiled `.hbm` models** — links are inside the SDK at `oellm_runtime/model/resolve_model_nash-p.md` (`nash-p` = S600). Artifacts are `.hbm`, march **`nash-p`**.
4. **(Optional) OpenAI-compatible HTTP server** via [`oellm_server`](https://github.com/D-Robotics/oellm_server) — endpoints `/health`, `/v1/models`, `/v1/chat/completions` (SSE). `--model-type` 0=INTERNVL / 1/4/7=text. Full setup → [llm-build-commands.md](references/llm-build-commands.md) §3.

> The model_zoo / LLM_Toolchain S600 numbers (TTFT / TPS / memory) are **benchmarks, not a runtime** — actual deployment goes through this SDK. Benchmark table → [llm-voice-stack.md](references/llm-voice-stack.md) §6, or get structured JSON via `python3 scripts/llm_benchmark.py --board s600 --model <model>`.

**验证:** `curl http://localhost:8000/health` returns 200; `curl http://localhost:8000/v1/models` lists the loaded model; `bash scripts/llm_env_check.sh` confirms `board_id` is S600 and `recommended_stack` is `oellm_runtime`; `python3 scripts/llm_benchmark.py --board s600 --model <model>` returns expected TTFT/TPS/memory JSON.

### Workflow 3 — hobot_llm legacy LLM (X3 4GB only)

**Use when:** plain text chat on an X3, "apt LLM node", smallest footprint.

Full install + run commands → [llm-build-commands.md](references/llm-build-commands.md) §4. Key constraints:
- Model is **Bloom 1.4B**; **X3 4GB RAM only**, Ubuntu 20.04 (Foxy) / 22.04 (Humble).
- **Raise BPU reserved memory to 1.7GB** (`0x6a400000`; doc rounds to ~1.9GB) via `srpi-config` or model won't load.
- Prefer `hobot_llamacpp` for any X5/S100 new project.

**验证:** `ros2 run hobot_llm hobot_llm_chat` starts and returns text responses; `free -h` shows >1.7 GB BPU reserved memory (set via `srpi-config`); board is X3 4 GB.

### Workflow 4 — Voice assistant loop (ASR → LLM → TTS) and 小智

**Use when:** 语音助手, voice control, ASR/TTS, 小智 / xiaozhi.

Two ways to build it:

**A. Compose the ROS pipeline** (mic → ASR → LLM → speaker):
1. **ASR — `sensevoice_ros2`** (offline SenseVoice.cpp). Launch command + params → [llm-build-commands.md](references/llm-build-commands.md) §5. ASR result → `/asr_text` → feed into hobot_llamacpp's `/prompt_text`. Command words in `config/cmd_word.json` (shipped 5 words); wakeup is separate (`wakeup_name`, default `你好`, needs `push_wakeup:=1`). Runs on X3/X5/S100/S100P/S600.
2. **LLM** — feed `/asr_text` into hobot_llamacpp (`feed_type:=2`) / hobot_llm.
3. **TTS — `hobot_tts`**: subscribes `/tts_text` → PCM → ALSA playback. Setup + run → [llm-build-commands.md](references/llm-build-commands.md) §5. Default playback device `hw:0,1`.

**B. Turnkey — `xiaozhi-in-rdk` (小智 AI assistant)**, RDK X3 / X5 / S100, end-to-end real-time voice:
- 16/24 kHz, Opus codec, spacebar push-to-talk, USB/MIPI dual-camera switch.
- Transport: **MQTT control + UDP audio**, **AES-128-CTR** encryption.
- Integrated **YOLOv8** detection exposed to the AI via **MCP**.
- Requires: rdkos **3.0.0+**, Python **3.10+**, ALSA + PulseAudio; USB mic + USB speaker recommended (X5 on-board audio works with default-device config).

Voice details → [llm-voice-stack.md](references/llm-voice-stack.md) §3–5.

**验证:** ASR — `ros2 topic echo /asr_text` returns recognized text when speaking; LLM — `/llama_cpp_node` (or `/hobot_llm`) generates responses to `/prompt_text`; TTS — `ros2 topic echo /tts_text` receives text and speaker plays audio; for xiaozhi — spacebar push-to-talk produces a voice response.

## Worked examples

**Example 1 — "我想在 S600 上跑个端侧大模型对话,用 hobot_llamacpp 怎么编译?"**
Stop the build. *"hobot_llamacpp 没有 S600 路径——它的编译宏只有 `-DPLATFORM_X5` 和 `-DPLATFORM_S100`。S600 端侧 LLM/VLM 走另一条官方栈:**D-Robotics_LLM_S600 SDK 的 oellm_runtime**(`libxlm.so`,`.hbm` march `nash-p`)。下 `D-Robotics_LLM_S600_1.0.2_SDK.tar.gz` + 用户手册,已编译模型看 SDK 内 `oellm_runtime/model/resolve_model_nash-p.md`;要 HTTP 接口用 oellm_server。"* Route to Workflow 2.

**Example 2 — "RDK X5 上想跑个看图问答的多模态,选哪个模型怎么起?"**
*"X5 用 hobot_llamacpp + GGUF-BPU 模型,1–2B VLM 流畅。推荐 `InternVL3-2B-Instruct-GGUF-BPU` 或更小的 `SmolVLM2-500M`。要下两个文件:ViT 编码器(X5 是 `.bin`)+ 语言 GGUF。最小启动 `feed_type:=0`(本地图)`model_type:=0`(InternVL),输出看 `/llama_cpp_node` 话题。"* Route to Workflow 1.

**Example 3 — "想做个能听我说话、回答还能播出来的语音助手,板子是 X5"**
*"拼三段 ROS 管线:`sensevoice_ros2`(ASR,结果发 `/asr_text`)→ hobot_llamacpp(`feed_type:=2`,订阅 `/prompt_text`)→ `hobot_tts`(订阅 `/tts_text` 播 PCM)。把 ASR 的 `/asr_text` 接到 LLM 的 `/prompt_text`,LLM 中间结果发 `/tts_text` 给 TTS 即闭环。想要开箱即用就直接上 `xiaozhi-in-rdk`(小智),空格键对话,要 rdkos 3.0.0+ 和 USB 麦/音箱。"* Route to Workflow 4.

**Example 4 — "sensevoice 默认能识别'地平线你好'这个唤醒词吗?"**
*"不能直接当唤醒词用。实际随仓库发布的 `config/cmd_word.json`(在 `config/` 根目录)是 5 条**命令词**:向前走/向后退/向左转/向右转/停止运动,**不含「地平线你好」**。唤醒词是另一个概念,由 `wakeup_name` 参数配置,**默认是「你好」(不是「地平线你好」)**,且要 `push_wakeup:=1` 才会发布唤醒话题。「地平线你好」只出现在 README 旧的 `config/hrsc/` 命令词示例里,既不在实际发布的配置中,也不是唤醒词默认值。想用它就把它写进 `cmd_word.json` 或设成 `wakeup_name`。命令词可自定义,建议中文 3–5 字。"*

## Common pitfalls

| ❌ Don't | ✅ Do |
|---------|------|
| Build `hobot_llamacpp` for S600 | S600 → D-Robotics_LLM_S600 SDK `oellm_runtime` (`.hbm`, `nash-p`) |
| Download only the GGUF for a VLM | VLM needs **two** files: ViT encoder (X5 `.bin` / S100 `.hbm`) + language GGUF |
| Use a short HF model name (`InternVL3-2B`) | Use the full `-GGUF-BPU` repo slug under `huggingface.co/D-Robotics` |
| Tell user "地平线你好" is the default wakeup/command word | Shipped `config/cmd_word.json` has 5 command words; wakeup is a separate `wakeup_name` param (default **你好**). 地平线你好 lives only in the README's old `config/hrsc/` example |
| Default to `hobot_llm` on X5/S100 | `hobot_llm` is X3-4GB-only legacy (Bloom 1.4B); use `hobot_llamacpp` |
| Run hobot_llm on X3 without BPU-memory tuning | Raise BPU reserved memory to **1.7GB** (`0x6a400000`; doc rounds to ~1.9GB) or the model won't load |
| Treat S600 model_zoo benchmark as the runtime | Benchmarks are perf data; deploy via the S600 SDK |

## Anti-hallucination guardrails

When answering from this skill, follow these rules — never fabricate facts, commands, or file paths:

1. **Report only observed data.** Quote what scripts/commands actually return, not what you remember. If the probe says `board_id: X5`, answer for X5 — even if the user insists it's an S100.
2. **No fabrication when tools are missing.** If a script or reference doesn't exist, say "not found" — don't invent from memory. Route to the appropriate skill or doc instead.
3. **Preserve null/false/empty on failure.** If a probe returns `null` or `false`, report that — don't substitute a plausible value. Empty output is data, not an error to "fix".
4. **No substitution off-platform.** If `off_platform: true`, say "probe didn't run on an RDK board" — don't guess what it would have returned. Ask for on-board logs.
5. **No hand-editing JSON.** Scripts emit structured JSON; never hand-craft output. If the contract says `{ok,off_platform,reason,fields}`, that's what goes to the user.
6. **Acknowledge sandbox limits.** If you can't run a command, say so — don't pretend you did. Offer the command for the user to run.
7. **Read-only boundary.** Never modify the system — no `dd`, `mkfs`, `rm -rf`, `apt install`, `reboot`, or GPIO output without explicit user confirmation.

## Reference map

| Read this | When |
|-----------|------|
| [llm-build-commands.md](references/llm-build-commands.md) | Quick-reference build & run commands for all 4 workflows (hobot_llamacpp build/run, S600 SDK + oellm_server, hobot_llm, sensevoice/hobot_tts/xiaozhi) |
| [llm-voice-stack.md](references/llm-voice-stack.md) | Full per-board commands: hobot_llamacpp run matrix (InternVL/SmolVLM/pure-LLM × X5/S100), all node params/topics, sensevoice/hobot_tts/xiaozhi config, oellm_server flags, S100/S600 benchmarks, model-source table |
| `scripts/llm_env_check.sh` | Live LLM environment probe — reads board_id + memory + scans `/opt/tros/*/lib/` for installed LLM packages (hobot_llm/hobot_llamacpp/oellm) + recommends the matching stack per board (structured JSON `{ok,off_platform,reason,fields}`; non-board → `{"ok":false,"off_platform":true,"reason":"not_on_rdk_board","fields":null}`) |
| `scripts/llm_benchmark.py` | Structured JSON LLM benchmark lookup — board + model → TTFT_ms / TPS / memory_gb / qtype / max_context (S600/S100P/X3; anti-hallucination: cite exact perf numbers, don't parse Markdown) |
