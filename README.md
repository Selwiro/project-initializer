# project-initializer

**用 Codex 初始化项目、记录任务，换个会话也能接着做。**

这是一个适用于编程、写作、AI 视频等项目的技能。新项目可以用它整理目标、文件位置和第一项任务。已有项目可以沿用原来的文件和任务记录，补齐缺少的说明。

## 用 Codex 开始

**1. 安装技能。** 在终端运行以下命令。需要 Git 和 Python 3.10 或更高版本。

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Selwiro/project-initializer.git ~/.agents/skills/project-initializer
```

**2. 在 Codex 里打开你的项目文件夹。** 新项目可以先建一个空文件夹。把下面这句话发给 Codex，把例子换成自己的目标。

> 用 `$project-initializer` 初始化当前项目。我想做一个记账应用，第一版能记录支出并查看每月合计。请帮我写清第一版的范围和完成条件，再登记第一项任务。

已有项目可以说「用 `$project-initializer` 接入当前项目，沿用现有文件和任务记录」。

**3. 继续做任务。** Codex 会建立或补齐项目说明和任务清单。在同一个项目里，可以用下面这些指令继续。

- 「执行 T001，完成后记录结果和验证方式。」
- 「现在做到哪了？下一步做什么？」
- 「把 T002 暂缓，等拿到素材后再继续。」

## 搭配 agent-kanban 使用

想在网页上查看多个项目的进度，可以搭配 [agent-kanban](https://github.com/Selwiro/agent-kanban)。技能负责在项目里建立和更新任务记录，看板读取同一份记录。

1. 用本技能初始化或接入项目后，在看板点「选择项目目录」，打开含有 `management/project.json` 的项目文件夹，勾选「选择当前目录」，再点「扫描并加入」。
2. 在看板查看进度或新建任务。拿到任务编号后，回到该项目的 Codex 会话，告诉它要执行哪一项。
3. Codex 写回执行结果后，在看板点「刷新数据」查看。

## 更新与终端试用

按上面的方式安装过，可以在终端更新。

```sh
git -C ~/.agents/skills/project-initializer pull --ff-only
```

其他支持 [SKILL.md](SKILL.md) 的 AI 助手，可把整个仓库放进各自的技能目录。

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
