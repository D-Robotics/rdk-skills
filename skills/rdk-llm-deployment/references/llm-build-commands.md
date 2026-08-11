# LLM / VLM Build & Run Commands — Quick Reference

> Extracted from the SKILL.md workflows so the SKILL.md stays an entry point. For full node parameters, topic names, model lists, and benchmarks, see [llm-voice-stack.md](llm-voice-stack.md).

---

## 1. hobot_llamacpp — Build (X5 / S100 / S100P)

```bash
# 1. Pull llama.cpp at the pinned tag and build it
git clone https://github.com/ggml-org/llama.cpp -b b4749
cmake -B build && cmake --build build --config Release
# 2. Symlink it into the package
cd hobot_llamacpp && ln -s ../llama.cpp llama.cpp
# 3. colcon build with the board's platform flag
colcon build --merge-install --cmake-args -DPLATFORM_X5=ON  --packages-select hobot_llamacpp   # X5
colcon build --merge-install --cmake-args -DPLATFORM_S100=ON --packages-select hobot_llamacpp   # S100/S100P
```

- Environment: C/C++, Ubuntu 22.04, GCC 11.4.0, OpenCV 3.4.5.
- ROS deps: `dnn_node`, `cv_bridge`, `sensor_msgs`, `hbm_img_msgs`, `ai_msgs`. `hbm_img_msgs` (in `hobot_msgs`) is only needed for the shared-mem image path (`SHARED_MEM=ON`, default).
- **No `-DPLATFORM_S600` flag exists** — S600 uses the D-Robotics_LLM_S600 SDK (§3 below).

## 2. hobot_llamacpp — Run (VLM / LLM)

```bash
source ./install/setup.bash
cp -r install/lib/hobot_llamacpp/config/ .
ros2 run hobot_llamacpp hobot_llamacpp --ros-args \
  -p feed_type:=0 -p image:=config/image2.jpg -p image_type:=0 \
  -p user_prompt:="描述一下这张图片."
```

- `feed_type`: 0=local-image VLM / 1=subscribed-image VLM / 2=subscribed LLM.
- `model_type`: 0=InternVL / 1=SmolVLM.
- On **S100** add the `.hbm` encoder: `-p model_file_name:=vit_model_int16.hbm`.
- Text output → topic `/llama_cpp_node`; TTS-feedable intermediate text → `/tts_text`.
- Drive prompts live by publishing `std_msgs/String` to `/prompt_text`.
- Full parameter matrix (InternVL / SmolVLM / pure-LLM × X5 / S100 × exec / launch) → [llm-voice-stack.md](llm-voice-stack.md) §1.

## 3. S600 SDK — Download & oellm_server

```bash
# Download the SDK + manual (per-board run steps are in the manual, not on GitHub)
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/D-Robotics_LLM_S600_1.0.2_SDK.tar.gz
wget https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/llm_s600/1.0.2/D-Robotics_LLM_S600_1.0.2_Doc.zip
```

OpenAI-compatible HTTP server via `oellm_server` on top of `oellm_runtime`:

```bash
export LD_LIBRARY_PATH=<...>/oellm_runtime/lib:$LD_LIBRARY_PATH
python3 openai_server.py --model-type 7 --hbm-path <model.hbm> \
  --tokenizer-dir <dir> --template-path <chat_template> --host 0.0.0.0 --port 8000
```

- `--model-type`: 0=INTERNVL (then `--config-path` required), 1/4/7 = text models (then `--hbm-path` + `--tokenizer-dir` required).
- Endpoints: `/health`, `/v1/models`, `/v1/chat/completions` (SSE streaming).
- Run `sh set_performance_mode.sh` first for full speed.
- README examples ship for S100 SDK; S600 uses the same interface — defer to the S600 manual for final wiring.

## 4. hobot_llm — X3 4GB Legacy (Bloom 1.4B)

```bash
pip3 install transformers
sudo apt update && sudo apt install -y hobot-dnn          # update on-board dnn
sudo apt install -y tros-humble-hobot-llm                 # or tros-hobot-llm (foxy)
wget http://archive.d-robotics.cc/llm-model/llm_model.tar.gz
sudo tar -xf llm_model.tar.gz -C /opt/tros/${TROS_DISTRO}/lib/hobot_llm/
ros2 run hobot_llm hobot_llm_chat                          # terminal chat; or `hobot_llm` for topic I/O
```

- Model: **Bloom 1.4B**; X3 4GB RAM only, Ubuntu 20.04 (Foxy) / 22.04 (Humble).
- **Raise BPU reserved memory to 1.7GB** (`0x6a400000`; doc rounds to ~1.9GB) via `srpi-config`, or the model fails to load.
- Best perf: CPU `performance` governor + boost.
- Prefer `hobot_llamacpp` for any X5/S100 new project.

## 5. Voice Pipeline — ASR / TTS / 小智

### sensevoice_ros2 (ASR)

```bash
sudo apt install -y tros-humble-sensevoice-ros2
source /opt/tros/humble/setup.bash
ros2 launch sensevoice_ros2 sensevoice_ros2.launch.py \
  audio_asr_model:="sense-voice-small-fp16.gguf" language:="zh" micphone_name:="plughw:0,0"
```

- ASR result → `/asr_text` (`std_msgs/String`) → feed into hobot_llamacpp's `/prompt_text`.
- Command-word / wakeup events → `/audio_smart` (`audio_msg/msg/SmartAudioData`).
- Command words in `config/cmd_word.json` (shipped 5 words). Wakeup is separate (`wakeup_name`, default `你好`, needs `push_wakeup:=1`).
- Runs on X3/X5/S100/S100P/S600.

### hobot_tts (TTS)

```bash
wget http://archive.d-robotics.cc/tts-model/tts_model.tar.gz
sudo tar -xf tts_model.tar.gz -C /opt/tros/${TROS_DISTRO}/lib/hobot_tts/
source /opt/tros/setup.bash && export GLOG_minloglevel=1
ros2 run hobot_tts hobot_tts
```

- Subscribes `/tts_text` → PCM → ALSA playback.
- Default playback device `hw:0,1` (`playback_device` param). Check `ls /dev/snd/` for `pcmC0D1p`.

### xiaozhi-in-rdk (turnkey 小智)

- X3 / X5 / S100; rdkos 3.0.0+, Python 3.10+, ALSA + PulseAudio.
- 16/24 kHz, Opus codec, spacebar push-to-talk, USB/MIPI dual-camera.
- MQTT control + UDP audio, AES-128-CTR encryption. Integrated YOLOv8 via MCP.
- USB mic + USB speaker recommended (X5 on-board audio works with default-device config).
