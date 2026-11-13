---
name: project-initializer
description: 初始化或接入项目、登记需求并回写看板、查询进度、搁置或恢复任务，以及办理结项、迁移和重启。
---

# 项目初始化与任务跟踪

从项目入口和 `management/project.json` 确认项目。以下命令使用技能包的 `scripts/project_init.py`。查进度用 `status <项目目录>`，核对结构用 `inspect`，只查一个任务的状态用 `task <项目目录> <ID> --metadata-only`。执行任务时再读取该任务详情。

- **初始化或接入**。按[初始化流程](references/Project_Initialization.md#初始化或接入的操作步骤)使用计划样例。根据实际类型选读相关章节：[编程](references/Programming_Project_File_Management.md)、[写作](references/Writing_Project_File_Management.md)、[AI 视频](references/AI_Video_Project_File_Management_v2.md)。
- **登记、执行、搁置或恢复**。按[任务流程](references/Project_Dashboard_Interface.md#三agent-怎样执行并回写)先登记具体需求，再按授权执行。追加同一需求沿用任务 ID。状态和结果写回正式任务来源，并复读索引和详情。单纯状态查询沿用现有任务记录。
- **结项、迁移或重启**。按[结项约定](references/Project_Initialization.md#结项迁移与重启)保留原记录。归档位置由用户选择，已结项项目继续实质工作前先重启。

已接入任务服务或外部系统时通过正式来源写入。本地写入提示有待恢复记录时运行 `recover <项目目录>`。发现冲突时保留记录并核对两边的实际内容。
