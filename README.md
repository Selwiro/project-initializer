# project-initializer

面向 AI 编程助手的项目初始化与任务管理技能。它帮助新项目或已有项目建立入口和任务索引，跟踪需求、执行结果、搁置事项，以及结项和重启。

## 安装

将本仓库作为 `project-initializer` 文件夹放入支持 `SKILL.md` 的助手技能目录。按所用工具的约定选取技能目录，再让助手加载 [SKILL.md](SKILL.md)。

## 使用

- 初始化当前项目，沿用已有的 README、工程路径和任务记录。
- 把具体项目需求登记为任务，按验收条件验证并回写任务状态。
- 结项时选择原地归档、同级 `_Archive` 或自定义位置。

本地命令使用 Python 3.10 或更高版本和 Unix 文件锁。可在仓库根目录运行：

```sh
python3 scripts/project_init.py --help
python3 scripts/project_init.py inspect /path/to/project
```

项目任务索引保存在项目自己的 `management/project.json`，可供兼容的看板读取。字段和操作约定见[看板接口文档](references/Project_Dashboard_Interface.md)。

## 许可证

见 [LICENSE](LICENSE)。
