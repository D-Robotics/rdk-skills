# D-Robotics Repo Family Map

> Sources: live `gh api orgs/D-Robotics/repos` metadata (name / description / language / fork / archived), verified 2026-07 at **350 public repos** (~440 total incl. private). 7 forks (lerobot, openpi, rosbag2, Alicia-D-SDK, rviz_2d_overlay_plugins, tros_nav_docking, agentic-auto-tester), 1 archived (DStereo_X5). Per-family counts below are approximate groupings — re-run `gh api` to confirm. The org evolves; treat the live org page as the source of truth.
>
> **Coverage note:** ~296 repos are explicitly listed below across 12 families. The remaining ~54 are forks, archived, or pure code libraries with no user-facing documentation — they are noted in their parent family or skipped. Re-run `gh api orgs/D-Robotics/repos --paginate --jq '.[].name'` for the exhaustive list.

## Naming-convention cheat table (pattern → meaning)

| Name pattern | Meaning | Layer |
| --- | --- | --- |
| `hobot-xxx` (hyphen) | BSP / system source component | System / BSP |
| `hobot_xxx` (underscore) | TROS / ROS2 application package | Application |
| *(no prefix:* `hobot-*` / `rdk-gen` / `manifest`) | **RDK X3** board | — |
| `x5-` prefix | RDK X5 board (public) | — |
| `s100-` prefix | RDK S100 / S100P board (**private** repos) | — |
| `j5-` prefix | Journey 5 (征程5, automotive SoC) board (**private** repos) | — |
| `tros_xxx` | TROS tooling / orchestration / release | Middleware |
| `nodehub_xxx` / `nodedhub_xxx` | NodeHub app packaging (deb for app center) | App distribution |
| `magicbox_xxx` | MagicBox hardware-product companion package | Product |
| `xxx_doc` / `xxx-doc` / `xxx_doc_center` | Documentation source | Docs |
| `speech_agent_*` | Speech Agent SDK (ASR/TTS/audio/bootstrap) | Application (LLM/speech) |
| `FAST-Calib*` / `fast-calib2*` | Calibration tooling | Application (perception) |
| `rdk_accessories_*_doc` | Accessories documentation (IMU/camera) | Docs |
| `sysroot_docker*` / `cross_compile` / `ros2_crosscompile*` / `tros_arm_build` | Cross-compilation toolchain | Toolchain |
| `rcl` / `rclcpp` / `rmw_*` / `rosbag2` / `vision_opencv` / `isaac_*` / `Livox-SDK2` | Upstream ROS2 port (NOT RDK-original) | Middleware |
| `mono*` / `stereo*` / `face_*` / `hand_*` / `*_cam` | Vision / perception application | Application |
| `pointcloud_*` / `*_pointcloud_*` | Pointcloud processing | Application |
| `rtabmap*` / `orb_slam*` / `*vins*` / `*_vio` | SLAM / VIO | Application |

## The 12 families

### 1. System / BSP (~40 public repos)
Kernel and board-support packages, assembled into the OS image via `repo` + `manifest` + `*-rdk-gen`.
- **Build entry**: `rdk-gen` (X3, public) / `x5-rdk-gen` (public, 61★) / `s100-rdk-gen` (private) / `j5-rdk-gen` (private). Manifests: `manifest` / `x5-manifest` (public); `j5-manifest` (private). Packages: `j5-packages`.
- **Low-level (public)**: `kernel` (3★) / `x5-kernel` (13★) / `x5-kernel-rt` / `uboot` / `x5-uboot` / `bootloader` (1★) / `x5-bootloader` (1★). (`s100-bootloader`, `j5-uboot`, `j5-kernel-5.10`, `j5-bootloader` are private.)
- **BSP components, one set per board**: `hobot-boot` / `-camera` / `-multimedia` / `-multimedia-dev` / `-multimedia-samples` / `-dnn` / `-bpu-drivers` / `-dtb` / `-wifi` / `-io` / `-io-samples` / `-utils` / `-display` / `-spdev` / `-sp-samples` / `-miniboot` / `-kernel-headers` / `-configs` / `-audio-config` / `-wm8960`, plus the `x5-hobot-*` public set and the `s100-hobot-*` **private** set.
- **Camera low-level (X5, public)**: `x5-libcam-sensor` / `x5-libcam-inc` / `x5-drv-camsys`.
- **Factory/tuning (X5)**: `x5-factorytest` (private) / `x5-tuning-json` / `x5-miniboot` / `x5-platform_samples` / `x5-multimedia-samples`.
- **RDK S600 note**: no `s600-` prefixed BSP/build repos exist (public or private). S600 support appears only in application-layer repos. See SKILL.md board-prefix table.
- Detailed build flow: [os-image-build.md](os-image-build.md).

### 2. TROS / ROS2 core ports (~15 repos)
RDK ports/mirrors of upstream ROS2 repos — **not RDK-original algorithms**: `rcl` / `rclcpp` (2★) / `rcl_interfaces` / `rmw_cyclonedds` / `ament_package` / `tinyxml_vendor` / `vision_opencv` / `rosbag2` (fork) / `rosbag2-foxy` / `livox_ros_driver2` / `Livox-SDK2` / `isaac_ros_nav_demo` / `isaac_rs_stereo_plugins_pkg` / `isaac_rs_stereo_component`. When one breaks, check upstream ROS2 first.

### 3. TROS tooling / orchestration (~19 repos)
`tros_*` and the build entry: `robot_dev_config` (7★, TROS compile entry) / `trosdep` / `tros_release` (private) / `tros_bridge_grpc` / `tros_perception_fusion` / `tros_perception_common` / `tros_runtime_stats` / `tros_websocket_interaction` (1★) / `tros_nav_docking` (fork) / `tros_gnss` / `tros_apriltag_det` (1★) / `tros_lowpass_filter` / `tros_bev` / `tros_ai_wrapper` / `tros_nav_workflow` / `tros_test` / `tros_mot` (1★) / `tros_application_model_zoo` / `tros_demos` (private).

### 4. Perception / vision application packages (~80 repos, largest family)
`hobot_*` underscore + algorithm-named repos. Organized by sub-task:
- **Detection / segmentation**: `hobot_yolo_world` (6★) / `hobot_dosod` (2★) / `hobot_bev` (8★) / `hobot_centerpoint` (5★) / `mono2d_body_detection` (5★) / `mono2d_trash_detection` (5★) / `mono3d_indoor_detection` (3★) / `mono2d_yolo_pose` / `mono_pwcnet` / `mono_edgesam` (1★) / `mono_edgetam` (1★) / `mono_mobilesam` (5★) / `mono_dosod26` / `object_detect` / `Grounded-Segment-Anything` / `deeplabv3p_hobot_dnn` / `hobot_falldown_detection` / `hobot_environmental_understanding` / `hobot_awareness` / `clip_image_feature_extraction`.
- **Tracking / MOT**: `body_tracking` (10★) / `mot` (1★) / `tros_mot` (1★) / `tbd_mot_train` / `gesture_control` / `audio_control` / `audio_tracking` / `reid` (1★) / `insightface_runtime` (1★).
- **Face / hand**: `face_age_detection` / `face_landmarks_detection` / `faceid` / `face_depth` / `palm_detection_mediapipe` / `hand_landmarks_mediapipe` / `hand_lmk_detection` / `hand_gesture_detection`.
- **Stereo depth**: `hobot_stereonet` (60★) / `hobot_stereonet_utils` / `DStereo` (1★) / `DStereo_X5` (archived) / `DStereo_evaluation` / `DStereoV2` / `StereoGDC` / `dstereo_occnet` (19★) / `domni_occnet` / `dfiseye_omni_occnet` (1★) / `elevation_net` / `stereo_error_dataset` / `binocular_depth_estimation_performance_test` / `camera_depth_estimation_performance_evaluation` / `depth_disp_render` / `multi_pipe_stereo_infer`.
- **SLAM / VIO**: `orb_slam3` / `rtabmap` / `rtabmap_ros` / `rtabmap_eval` / `dopenvins` / `drobotics_vio` / `semantic_map`.
- **Calibration** (9 repos): `FAST-Calib2` / `fast-calib2-python` (1★) / `stereo_calib` (5★) / `stereo_self_calib` / `stereo_calib_sensitivity_analysis` / `Lidar_Camera_Calib` / `camera_to_base_footprint_extrinsics_calibration` / `camera_to_base_footprint_extrinsics_calibration_use_odom` / `perception_calibrate` / `colmap-groundtruth-generation`.
- **Cameras**: `hobot_usb_cam` (3★) / `hobot_mipi_cam` (17★) / `hobot_rgbd_cam` / `hobot_zed_cam` (6★) / `hobot_stereo_mipi_cam` / `hobot_stereo_usb_cam` / `hobot_network_cam` / `hobot_rtsp_client` (1★) / `hobot_s316_cam` / `husq_stereo_cam` / `senyun_stereo_cam` / `sc202cs_mipi_cam` / `occ_s396_cam`.
- **Sensors / odometry**: `hobot_imu_sensor` (2★) / `hobot_sensors` / `wheel_odometry` / `sensor_paramter_manager` / `hobot_rtk`.
- **Pointcloud**: `pointcloud_voxel_convert` / `pointcloud_transform` / `pointcloud_web_viewer` / `ai_seg_mask_pointcloud_roi_extractor` (1★) / `mask_pc_roi_extractor`.
- **Fusion packages**: `hobot_obstacle_depth_fusion_pkg` / `hobot_segment_depth_fusion_pkg` / `hobot_water_stain_det_fusion_pkg`.
- **Feature matching**: `dfeature` / `glue-factory`.
- **Base / utilities**: `hobot_dnn` (29★, dnn_node) / `hobot_cv` (5★) / `hobot_msgs` / `hobot_shm` (1★) / `hobot_codec` (2★) / `hobot_hdmi` (2★) / `hobot_websocket` (3★) / `hobot_visualization` / `hobot_image_publisher` / `hobot_image_subscribe_example` / `hobot_trigger` / `hobot_agent` / `hobot_joy_develop` / `hobot_model` / `hobot_arm` / `hobot_autonomous_moving_grabbing` / `common_logger` / `drobotics_tools` / `feedback_example` / `rviz_2d_overlay_plugins` (fork) / `hobot_clip` (2★).
- **Application robots**: `xr_robot` / `line_follower` (8★) / `parking_search` / `parking_perception` / `feishu_robot` / `companion_agent` (1★).

### 5. Model Zoo (~6 repos)
`rdk_model_zoo` (353★, X3/X5, branches `rdk_x3` / `rdk_x5` / `rdk_s` / S600 feature branches) / `rdk_model_zoo_s` (59★, S-series, default branch `s100`) / `model_zoo` (1★) / `tros_application_model_zoo` / `ai_toolchain_models` / `easy_BPU_convert` / `RDK_Video_Solutions` (3★). → skill `rdk-model-zoo`.

### 6. NodeHub packaging (~10 repos)
`nodehub_config` / `nodehub_yolov8_object_detection` / `nodehub_yolov10_object_detection` / `nodehub_yolov8_instance_segmentation` / `nodehub_yolo11_object_detection` / `nodehub_hobot_clip` / `nodehub_hobot_yolo_world` / `nodehub_mono_mobilesam` / `nodedhub_hobot_stereonet` (1★, typo variant) / `nodehub-x5-rdkmodelzoo-samples` (2★).

### 7. Embodied AI (~10 repos)
`rdk_LeRobot_tools` (35★) / `RDK_LeRobot_Tools_4_THU_Discover_AirBotPlay` (2★) / `lerobot` (fork, 3★) / `openpi` (fork) / `openpi_runtime` (9★) / `RoboTwin` (4★) / `embodied_ai_robots` (1★) / `Alicia-D-SDK` (fork) / `object_graspnet` (2★) / `xr_robot`. → skill `rdk-embodied-lerobot`.

### 8. On-device LLM / Speech (~20 repos, split into two sub-families)

#### 8a. On-device LLM / VLM
`hobot_llamacpp` (14★) / `hobot_llm` (4★) / `hobot_xlm` (2★, LeapLLM) / `hobot_chatbot` / `hobot_gpt` / `chat_robot` / `llama.cpp` (fork, BPU model) / `PTQ_InternVL2` / `PTQ_MiniCPM` / `oellm_server` (1★) / `rdk_ai_gateway_ros` (4★). → skill `rdk-llm-deployment`.

#### 8b. Speech Agent SDK
`speech_agent_bootstrap` (C, SDK init for VTN/VAD/ASR/TTS) / `speech_agent_asr` (C++) / `speech_agent_tts` (C++) / `speech_agent_audio` (C, noise reduction + wake-up + VAD) / `speech_agent_test` (Python, integration test) / `sensevoice_ros2` (5★) / `hobot_tts` (2★) / `hobot_audio` (5★) / `xiaozhi-in-rdk` (7★). → skill `rdk-llm-deployment` (补 references).

### 9. MagicBox product (~7 repos)
`magicbox_lighting_control` (1★) / `magicbox_audio_io` / `magicbox_gesture_interaction` / `magicbox_qwen_llm` / `magicbox_servo_control` / `magicbox_mipi_cam` / `magicbox_doc`. → skill `rdk-ecosystem`.

### 10. Documentation (~17 repos)
`rdk_doc` (17★, main doc source, JavaScript/docs framework) / `rdk_s_doc` (1★) / `rdk_x_doc` / `rdk_oe_s_doc` (MDX, S-series OpenExplorer) / `tros_doc` / `tros_vims_doc` / `model_zoo_doc` / `rdk_studio_doc` / `rdk_doc_center` / `case_doc` / `accessories_doc` / `magicbox_doc` / `DRobotics_SoC_Technology` (1★) / `xburn_doc` (1★, xburn flashing) / `rdk_accessories_bmi088_doc` / `rdk_accessories_gs130wi_doc` / `rdk_accessories_gs130w_doc`. → skills `rdk-doc-finder` / `rdk-accessories` / `rdk-board-knowledge`.

### 11. Image / toolchain helpers (~9 repos)
`system_download` (image download manifest) / `sysroot_docker` / `sysroot_docker_noble` / `cross_compile` / `ros2_crosscompile_w_sdk` (1★) / `tros_arm_build` (1★, Dockerfile) / `bloom` / `evb_ros_depend` / `x5-tuning-json`. (`ai_toolchain_models`, `x5-factorytest` are private.) → skill `rdk-device` / 新建 `rdk-cross-compilation` (Layer 5).

### 12. Other / courses / internal (~30 repos)
`device-knowledge` (2★, this repo) / `moss` (109★, agent architecture) / `moss-ci` / `agentic-auto-tester` (fork) / `benchmark` / `d-robotics-recruit` / `rdk-course-demos` (RDK 课程示例) / `coding-skills` (1★) / `rdk_support` / `rdk_studio_examples` / `rdk_studio_private-ci` / `rdk-imu-module-sdk` (C/Python/ROS2 IMU SDK) / `rdk_imu` (6★) / `xwarehouse` / `trial_guard` / `htol_tool` / `factorytest_tool` / `tc_x5rdk_runner` / `breakpad` / `aes-dev` / `sqlite` / `Vims_dev_env` / `node-red-rdk-nodes` (3★) / `TEST_for_pull` / `Robotics-Dream-Keeper-Challenge` (22★). → skill `rdk-ecosystem`.

## Cross-platform / standalone repo reminders

- `lerobot` / `openpi` are D-Robotics **forks of upstream projects** (READMEs note BPU adaptation), not from-scratch originals. Same for `llama.cpp`, `rosbag2`, `Alicia-D-SDK`, `rviz_2d_overlay_plugins`, `tros_nav_docking`, `agentic-auto-tester`.
- `DStereo_X5` is **archived** — use `DStereo` or `dstereo_occnet` instead.
- Family-2 ROS2 core ports: when one breaks, verify upstream ROS2 behavior before assuming an RDK-introduced change.
- A single capability may exist as **both** a BSP library (hyphen) and a ROS package (underscore). Decide whether you want the low-level library or the ROS node **before** picking a repo.
- **Public vs private**: many `s100-*` / `j5-*` BSP/build repos and some `tros_*` repos are private. The prefix → board mapping is still valid for *classifying* a name you encounter, but you cannot clone a private one anonymously.

## Journey 5 (征程5)

`j5-` = Journey 5 (征程 Journey 5), Horizon's automotive/autonomous-driving SoC. The prefix → board mapping holds, but the `j5-rdk-gen` / `j5-manifest` / `j5-kernel-5.10` repos are private; product attribution is documented on the official developer site (Journey 5 OpenExplorer docs at developer.d-robotics.cc).
