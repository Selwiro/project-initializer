# project-initializer

**让 AI 助手帮你初始化项目、记录任务，换个会话也能接着做。**

这是一个适用于编程、写作、AI 视频等项目的技能。新项目可以用它整理目标、文件位置和第一项任务。已有项目可以沿用原来的文件和任务记录，补齐缺少的说明。

## 快速开始

**1. 获取技能。** 如果你的助手支持安装技能，把整个仓库放进它的技能目录。你也可以下载整个仓库，把 [SKILL.md](SKILL.md) 的本地路径发给助手，请它按文件里的步骤操作。两种方式都需要助手能读写项目文件并运行 Python 3.10 或更高版本。

例如，使用 Codex 时，可以用 Git 安装到个人技能目录。

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Selwiro/project-initializer.git ~/.agents/skills/project-initializer
```

**2. 告诉助手你想做什么。** 让助手打开你的项目文件夹。新项目可以先建一个空文件夹，再把下面的例子换成自己的目标。

> 用 project-initializer 初始化当前项目。我想做一个记账应用，第一版能记录支出并查看每月合计。请帮我写清第一版的范围和完成条件，再登记第一项任务。

已有项目可以说「用 project-initializer 接入当前项目，沿用现有文件和任务记录」。

**3. 继续做任务。** 助手会建立或补齐项目说明和任务清单。在同一个项目里，可以用下面这些指令继续。

- 「执行 T001，完成后记录结果和验证方式。」
- 「现在做到哪了？下一步做什么？」
- 「把 T002 暂缓，等拿到素材后再继续。」

## 搭配 agent-kanban 使用

想在网页上查看多个项目的进度，可以搭配 [agent-kanban](https://github.com/Selwiro/agent-kanban)。技能负责在项目里建立和更新任务记录，看板读取同一份记录。

1. 用本技能初始化或接入项目后，在看板点「选择项目目录」，打开含有 `management/project.json` 的项目文件夹，勾选「选择当前目录」，再点「扫描并加入」。
2. 在看板查看进度或新建任务。拿到任务编号后，回到该项目的 AI 助手会话，告诉它要执行哪一项。
3. 助手写回执行结果后，在看板点「刷新数据」查看。

## 更新与终端试用

如果用 Git 获取了技能，在技能仓库目录运行 `git pull --ff-only` 即可更新。

想先看看初始化会生成什么，可以在技能仓库根目录运行下面的示例。它会在临时目录建立一个演示账本，并显示项目进度和第一项任务。

```sh
demo_dir=$(mktemp -d)
python3 scripts/project_init.py apply "$demo_dir" assets/init-plan.json --dry-run
python3 scripts/project_init.py apply "$demo_dir" assets/init-plan.json
python3 scripts/project_init.py status "$demo_dir"
python3 scripts/project_init.py task "$demo_dir" T001
```

用终端初始化真实项目时，先为该项目准备计划文件。[初始化步骤](references/Project_Initialization.md#初始化或接入的操作步骤)

## 参考文档

- [项目初始化、接入、结项和重启](references/Project_Initialization.md)
- [编程项目的目录与 Git 管理](references/Programming_Project_File_Management.md)
- [剧本和小说的文件管理](references/Writing_Project_File_Management.md)
- [AI 视频的策划、素材与镜头管理](references/AI_Video_Project_File_Management_v2.md)
- [任务记录和看板接口](references/Project_Dashboard_Interface.md)

## 许可证

[MIT](LICENSE)
