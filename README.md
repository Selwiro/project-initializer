# project-initializer

面向 AI 编程助手的项目初始化与任务管理技能。它帮助新项目或已有项目建立入口和任务索引，跟踪需求、执行结果、搁置事项，以及结项和重启。

## 通用初始化与专项规定

项目初始化适用于各类新项目，也可用于接入已有项目。通用流程包括明确目标、范围与验收条件，建立或补齐项目入口和任务索引，并在下一步明确时登记首项任务。接入已有项目时沿用现有工程位置和任务记录。[通用项目初始化规范](references/Project_Initialization.md)

以下类型在通用流程上补充专项规定。其他类型可直接使用通用流程，混合项目可按各工作内容组合适用的规定。

- **编程项目**。新工程在 `work/` 下按平台或用途建立独立目录，并明确 Git 仓库位置和推送范围。[编程项目文件与 Git 管理](references/Programming_Project_File_Management.md)
- **写作项目（编剧、小说）**。单一写作项目可直接在 `work/` 维护主稿和大纲，按需以场次或章节组织稿件并记录审阅版本。[写作项目文件管理](references/Writing_Project_File_Management.md)
- **AI 视频项目**。按制作阶段组织策划、资产和镜头文件，并记录素材来源和版本。[AI 视频项目文件管理](references/AI_Video_Project_File_Management_v2.md)

## 安装

以 Codex 为例，从终端安装到个人技能目录。进入要管理的项目后，可在 Codex 中输入「用 $project-initializer 初始化当前项目」。

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Selwiro/project-initializer.git ~/.agents/skills/project-initializer
```

已经用上面的方法安装时，可用以下命令更新。

```sh
git -C ~/.agents/skills/project-initializer pull --ff-only
```

其他兼容 [SKILL.md](SKILL.md) 的助手可按各自的技能目录约定放置整个仓库。

## 使用

- 初始化当前项目，沿用已有的 README、工程路径和任务记录。
- 把具体项目需求登记为任务，按验收条件验证并回写任务状态。
- 结项时选择原地归档、同级 `_Archive` 或自定义位置。

本地命令需要 Python 3.10 或更高版本，使用 Python 标准库。请先用 `python3 --version` 检查版本。以下示例在技能仓库根目录运行，用随附的演示账本计划创建临时项目。

```sh
demo_dir=$(mktemp -d)
python3 scripts/project_init.py apply "$demo_dir" assets/init-plan.json --dry-run
python3 scripts/project_init.py apply "$demo_dir" assets/init-plan.json
python3 scripts/project_init.py status "$demo_dir"
python3 scripts/project_init.py task "$demo_dir" T001
```

管理真实项目时，先按[初始化流程](references/Project_Initialization.md#初始化或接入的操作步骤)准备项目自己的计划。

## 搭配 agent-kanban 使用

用本技能初始化或接入项目后，可以在 [agent-kanban](https://github.com/Selwiro/agent-kanban) 中导入包含 `management/project.json` 的项目目录，在网页上查看进度或新建任务。把任务编号交给对应项目的 AI 助手，待助手写回执行结果后，点击看板上的「刷新数据」查看。

字段和操作约定见[看板接口文档](references/Project_Dashboard_Interface.md)。

## 许可证

见 [LICENSE](LICENSE)。
