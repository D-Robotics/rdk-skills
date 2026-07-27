# D-Robotics Skills

> D-Robotics 面向 AI Agent 的能力包生态中央目录仓库。

## 这是什么

本仓库是 **D-Robotics Skills 的中央目录（catalog）**。各 Skill Pack 在独立仓库维护源头，本仓库做镜像同步、统一索引和路由入口。

用户只需跟本仓库打交道，一条命令即可浏览和安装全部 Skill。

## 快速开始

### Claude Code

```
/plugin marketplace add D-Robotics/skills
```

然后运行 `/plugin`，在 Discover 标签页浏览安装。

### 通用 skills CLI

```bash
npx skills add d-robotics/skills
```

## 已注册的 Skill Pack

| Pack | 仓库 | 范围 | Skill 数 |
|---|---|---|---|
| OE 工具链 | [D-Robotics/OE-Skills-D-Robotics](https://github.com/D-Robotics/OE-Skills-D-Robotics) | 量化、编译、推理、性能评测、诊断 | 60+ |
| BSP | _待建_ | 系统烧录、驱动配置、板端环境 | — |
| ISP Tuning | _待建_ | 图像质量调参、摄像头校准 | — |
| Model Zoo | _待建_ | 模型推理 demo、示例应用 | — |
| TROS | _待建_ | ROS 机器人算法包 | — |

注册表见 `components.d/`。新建 Pack 参见 [组织指南](../D-Robotics_Skills_组织指南.md)。

## 仓库结构

```
D-Robotics-skills/
├── README.md                        ← 本文件
├── skill-index.json                 ← 全量索引（同步流水线自动生成）
├── components.d/                     ← Pack 注册表（每个 Pack 一个 YAML）
│   └── oe-skills.yml
├── skills/                          ← 镜像目录（同步流水线写入，只读）
├── .claude-plugin/
│   └── marketplace.json             ← Claude Code marketplace
├── .agents/plugins/
│   └── marketplace.json             ← Codex / Cursor 等兼容
├── .github/scripts/                 ← 同步与校验脚本
│   ├── sync.py
│   └── validate.py
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

## 新建 Skill Pack

1. 在 `D-Robotics` 组织下创建仓库，命名 `<domain>-skills`
2. 在本仓库 `components.d/` 下添加一个 YAML 注册文件
3. 同步流水线会自动拉取并合并到中央索引

详见 [组织指南](../D-Robotics_Skills_组织指南.md)。

## 许可证

Apache-2.0
