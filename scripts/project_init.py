#!/usr/bin/env python3
"""Initialize projects, manage lifecycle status, and update local tasks."""

import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from uuid import uuid4

INDEX = "management/project.json"
TASK_STATES = {"todo", "in_progress", "blocked", "done", "cancelled"}
PROJECT_TYPES = {"programming", "writing", "ai_video", "other"}
PROJECT_STATES = {"planned", "active", "paused", "completed", "cancelled"}


def path_in(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("项目路径不能为空。")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"请使用项目内的相对路径：{value}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"路径越出项目目录：{value}")
    return path


def read_object(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"应为 JSON 对象：{path}")
    return data


def git_root(root):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return None
    return result.stdout.strip() or None


def inspect(root):
    index = path_in(root, INDEX)
    data = None
    issues = []
    if index.exists():
        try:
            data = read_object(index)
            validate_index(root, data)
            if not path_in(root, data["entry_path"]).is_file():
                issues.append(f"找不到项目入口：{data['entry_path']}")
            for task in data["tasks"]:
                for field in ("detail_path", "target_path"):
                    if field in task and not path_in(root, task[field]).exists():
                        issues.append(f"{task['id']} 找不到 {field}：{task[field]}")
        except (ValueError, OSError, KeyError, TypeError) as error:
            issues.append(str(error))
    else:
        issues.append(f"缺少看板索引：{INDEX}")
    return {
        "root": str(root),
        "git_root": git_root(root),
        "entries": sorted(p.name for p in root.iterdir() if p.name != ".DS_Store"),
        "index": data,
        "issues": issues,
    }


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def task_body(task_id, task, target):
    return (
        f"# {task_id} {task['title']}\n\n"
        f"## 工作范围\n\n{task['scope']}\n\n"
        f"工作位置：`{target}`\n\n"
        f"## 验收\n\n{task['acceptance']}\n\n"
        "## 执行记录\n"
    )


def overview_body(data, entry, scope, acceptance, target, plan):
    location = Path(entry).parent
    index_link = os.path.relpath(INDEX, location)
    target_link = os.path.relpath(target, location)
    first_task = next((task for task in data["tasks"] if task["id"] == data["next_task_id"]), None)
    next_link = ""
    if first_task and "detail_path" in first_task:
        detail = os.path.relpath(first_task["detail_path"], location)
        next_link = f"\n\n接入时登记的任务 [{first_task['id']}]({detail})"
    engineering = ""
    if data["type"] == "programming":
        mode = plan.get("push_mode", "待确认，按本地流程")
        run = plan.get("run_command", "待确认")
        verify = plan.get("verify_command", "待确认")
        engineering = f"\n- 推送模式 {mode}\n- 运行方式 {run}\n- 验证方式 {verify}\n"
    return (
        f"# {data['name']}\n\n"
        f"## 项目目标\n\n{data['summary']}\n\n"
        f"## 本阶段范围与验收\n\n{scope}\n\n{acceptance}\n\n"
        f"## 工作位置\n\n[`{target}`]({target_link})\n{engineering}\n"
        f"## 项目进度\n\n[项目概况与任务]({index_link}){next_link}\n"
    )


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False,
    ) as handle:
        temp = Path(handle.name)
        try:
            handle.write(content)
            handle.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def save_index(path, data):
    data["updated_at"] = now()
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def save_task_detail(index, data, detail, body, previous=None):
    atomic_write(detail, body)
    try:
        save_index(index, data)
    except OSError:
        if previous is None:
            detail.unlink()
        else:
            atomic_write(detail, previous)
        raise


def next_task_id(root, tasks):
    used = {task["id"] for task in tasks}
    number = 1
    while True:
        task_id = f"T{number:03}"
        detail = root / "management" / "tasks" / f"{task_id}.md"
        if task_id not in used and not os.path.lexists(detail):
            return task_id
        number += 1


@contextmanager
def write_lock(root):
    directory = path_in(root, "management")
    directory.mkdir(exist_ok=True)
    path = path_in(root, "management/.project-init.lock")
    with path.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def validate_index(root, data):
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("索引版本未知，请按看板接口核对。")
    for field in ("project_id", "name", "summary", "stage"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"缺少项目字段：{field}")
    if data.get("type") not in PROJECT_TYPES or data.get("status") not in PROJECT_STATES:
        raise ValueError("项目类型或状态不符合规范。")
    entries = data.get("tasks")
    if not isinstance(entries, list):
        raise ValueError("tasks 必须是数组。")
    task_ids = set()
    for task in entries:
        if not isinstance(task, dict):
            raise ValueError("每条任务必须是对象。")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip() or task_id in task_ids:
            raise ValueError("任务 ID 缺失或重复。")
        task_ids.add(task_id)
        if not task.get("title") or task.get("status") not in TASK_STATES:
            raise ValueError(f"任务标题或状态无效：{task_id}")
        for field in ("detail_path", "target_path"):
            if field in task:
                path_in(root, task[field])
    next_id = data.get("next_task_id")
    if next_id is not None and not any(
        task["id"] == next_id and task["status"] in {"todo", "in_progress"}
        for task in entries
    ):
        raise ValueError("next_task_id 应指向可推进的任务，或设为 null。")
    path_in(root, data["entry_path"])


def apply(root, plan, dry_run):
    if plan.get("task_source", "local") != "local":
        raise ValueError("请通过现有任务服务或外部任务系统维护索引。")
    if plan.get("public_repo") is True and git_root(root):
        raise ValueError("请在公开仓库外、且包含工程的项目管理根目录应用。")
    index = path_in(root, INDEX)
    original = read_object(index) if index.exists() else {}
    if original and "schema_version" in original and original["schema_version"] != 1:
        raise ValueError("索引版本未知，请先按看板接口核对。")
    data = dict(original)
    data.setdefault("schema_version", 1)
    if "project_id" not in data:
        data["project_id"] = plan.get("project_id") or f"project-{uuid4().hex[:12]}"
    for field in ("name", "type", "summary", "stage", "status"):
        if field in plan:
            data.setdefault(field, plan[field])
    data.setdefault("entry_path", plan.get("entry_path", "README.md"))
    data.setdefault("next_task_id", None)
    data.setdefault("tasks", [])
    entry = path_in(root, data["entry_path"])
    target = plan.get("target_path", "work/")
    target_dir = path_in(root, target)
    dirs = []
    if target_dir.exists() and not target_dir.is_dir():
        raise ValueError(f"工作位置必须为目录：{target}")
    if plan.get("create_target"):
        if not target_dir.is_relative_to(path_in(root, "work")):
            raise ValueError("新建工程应位于 work/。")
        if not target_dir.exists():
            dirs.append(target_dir)
    elif not target_dir.is_dir():
        raise ValueError(f"已有工作位置不存在：{target}")

    writes = {}
    first = plan.get("first_task")
    if first and data["tasks"] == []:
        if not isinstance(first, dict) or any(
            not isinstance(first.get(k), str) or not first[k].strip()
            for k in ("title", "scope", "acceptance")
        ):
            raise ValueError("首项任务需要标题、范围和验收条件。")
        task_id = next_task_id(root, data["tasks"])
        detail = f"management/tasks/{task_id}.md"
        data["tasks"] = [{
            "id": task_id, "title": first["title"], "status": "todo",
            "target_path": target, "detail_path": detail, "created_at": now(),
        }]
        data["next_task_id"] = task_id
        writes[path_in(root, detail)] = task_body(task_id, first, target)
    validate_index(root, data)
    if entry.exists() and not entry.is_file():
        raise ValueError("项目入口必须是文件。")
    if not entry.exists():
        if data["entry_path"] not in {"README.md", "management/overview.md"}:
            raise ValueError("已有自定义入口找不到，请先核对其位置。")
        scope, acceptance = plan.get("scope"), plan.get("acceptance")
        if not scope or not acceptance:
            raise ValueError("生成项目入口需要本阶段范围和验收条件。")
        writes[entry] = overview_body(data, data["entry_path"], scope, acceptance, target, plan)

    for task in data["tasks"]:
        if "detail_path" in task:
            detail = path_in(root, task["detail_path"])
            if detail not in writes and not detail.is_file():
                raise ValueError(f"找不到任务详情：{task['detail_path']}")
    if data != original or not data.get("updated_at"):
        if "revision" in original:
            raise ValueError("这个项目已有任务服务版本记录，请通过正式任务来源更新索引。")
        data["updated_at"] = now()
        writes[index] = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not dry_run:
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
        for path, content in writes.items():
            if path != index and path.exists():
                raise ValueError(f"文件已存在，请重新读取：{path.relative_to(root)}")
            atomic_write(path, content)
    return {
        "dry_run": dry_run,
        "directories": [p.relative_to(root).as_posix() for p in dirs],
        "files": [p.relative_to(root).as_posix() for p in writes],
        "new_runtime_files": (
            ["management/.project-init.lock"]
            if (dirs or writes) and not path_in(root, "management/.project-init.lock").exists()
            else []
        ),
        "entry_path": data["entry_path"],
        "next_task_id": data["next_task_id"],
    }


def read_task(root, task_id):
    data = read_object(path_in(root, INDEX))
    validate_index(root, data)
    for task in data["tasks"]:
        if task["id"] == task_id:
            result = {"project_id": data["project_id"], "entry_path": data["entry_path"], "task": task}
            if "detail_path" in task:
                result["detail"] = path_in(root, task["detail_path"]).read_text(encoding="utf-8")
            return result
    raise ValueError(f"项目中找不到任务：{task_id}")


def read_local_index(root):
    index = path_in(root, INDEX)
    data = read_object(index)
    validate_index(root, data)
    if "revision" in data:
        raise ValueError("这个项目已有任务服务版本记录，请通过正式任务来源更新。")
    return index, data


def add_task(root, title, scope, acceptance, target):
    title, scope, acceptance, target = (value.strip() for value in (title, scope, acceptance, target))
    if not all((title, scope, acceptance)):
        raise ValueError("请填写任务标题、范围和验收条件。")
    if not path_in(root, target).is_dir():
        raise ValueError(f"找不到任务工作目录：{target}")
    index, data = read_local_index(root)
    content = {"title": title, "scope": scope, "acceptance": acceptance}
    for existing in data["tasks"]:
        if existing["title"] != title:
            continue
        existing_detail = existing.get("detail_path")
        if existing_detail and existing.get("target_path") == target:
            detail = path_in(root, existing_detail)
            expected = task_body(existing["id"], content, target)
            if detail.is_file() and detail.read_text(encoding="utf-8").startswith(expected):
                return existing
        if existing["status"] in {"todo", "in_progress", "blocked"}:
            raise ValueError(f"已有同名未结任务 {existing['id']}，请核对后沿用原任务或使用不同标题。")

    task_id = next_task_id(root, data["tasks"])
    detail_path = f"management/tasks/{task_id}.md"
    task = {
        "id": task_id, "title": title, "status": "todo", "target_path": target,
        "detail_path": detail_path, "created_at": now(),
    }
    data["tasks"].append(task)
    validate_index(root, data)
    save_task_detail(index, data, path_in(root, detail_path), task_body(task_id, content, target))
    return task


def defer_task(root, task_id, title, reason, resume_when, record_path):
    reason, resume_when = reason.strip(), resume_when.strip()
    if not reason or not resume_when:
        raise ValueError("请填写搁置原因和恢复条件。")
    record = record_path.read_text(encoding="utf-8").strip() if record_path else ""
    index, data = read_local_index(root)

    if task_id is not None:
        matches = [task for task in data["tasks"] if task["id"] == task_id]
        if not matches:
            raise ValueError(f"项目中找不到任务：{task_id}")
    else:
        title = title.strip()
        if not title:
            raise ValueError("请填写事项标题。")
        matches = [task for task in data["tasks"] if task["title"] == title]
        if len(matches) > 1:
            raise ValueError("有多个同名任务，请指定任务 ID。")

    if matches:
        task = matches[0]
        if task.get("detail_url"):
            raise ValueError("请通过外部任务来源更新此任务。")
        if task["status"] in {"done", "cancelled"}:
            raise ValueError("已结束的任务保留原状态，请为后续事项使用新的标题。")
    else:
        new_id = next_task_id(root, data["tasks"])
        task = {"id": new_id, "title": title, "created_at": now()}
        data["tasks"].append(task)

    detail_path = task.get("detail_path")
    if detail_path is None:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", task["id"]):
            raise ValueError("请为此任务指定项目内的 detail_path。")
        detail_path = f"management/tasks/{task['id']}.md"
    detail = path_in(root, detail_path)
    if task.get("detail_path") and not detail.is_file():
        raise ValueError(f"找不到任务详情：{detail_path}")
    original = detail.read_bytes().decode("utf-8") if detail.exists() else None
    body = original if original is not None else (
        f"# {task['id']} {task['title']}\n\n## 执行记录\n"
    )
    summary = f"搁置原因：{reason}\n\n恢复条件：{resume_when}"
    if record:
        summary += f"\n\n{record}"
    if task.get("status") == "blocked" and task.get("blocked_reason") == reason and (
        body.rstrip().endswith(f"\n\n{summary}")
    ):
        return task

    task.update(status="blocked", detail_path=detail_path, blocked_reason=reason)
    task.pop("run_id", None)
    if data["next_task_id"] == task["id"]:
        data["next_task_id"] = None
    validate_index(root, data)
    save_task_detail(index, data, detail, f"{body.rstrip()}\n\n### {now()} · 搁置\n\n{summary}\n", original)
    return task


def update_lifecycle(root, action):
    result = inspect(root)
    if result["issues"]:
        raise ValueError("\n".join(result["issues"]))
    data = result["index"]
    if "revision" in data:
        raise ValueError("这个项目已有任务服务版本记录，请通过正式任务来源更新。")

    current = data["status"], data["stage"]
    if action == "closeout":
        if data["status"] == "cancelled":
            raise ValueError("已取消的项目应保留取消状态。")
        new = "completed", "结项与归档"
    else:
        new = "active", "项目重启"
        if data["status"] != "completed" and current != new:
            raise ValueError("只有已结项的项目适用重启。")

    if current != new or (action == "closeout" and data["next_task_id"] is not None):
        data["status"], data["stage"] = new
        if action == "closeout":
            data["next_task_id"] = None
        save_index(path_in(root, INDEX), data)
    return data


def update_task(root, task_id, action, run_id, record_path, reason):
    index, data = read_local_index(root)
    task = next((item for item in data["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise ValueError(f"项目中找不到任务：{task_id}")
    if "detail_url" in task:
        raise ValueError("请通过外部任务来源更新此任务。")
    if action == "start":
        if task["status"] != "todo":
            raise ValueError(f"只有待办任务可以开始，当前状态：{task['status']}")
        if "detail_path" not in task:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", task_id):
                raise ValueError("请为此任务指定项目内的 detail_path。")
            detail_path = f"management/tasks/{task_id}.md"
            detail = path_in(root, detail_path)
            if not detail.exists():
                atomic_write(detail, f"# {task_id} {task['title']}\n\n## 执行记录\n")
            task["detail_path"] = detail_path
        if not path_in(root, task["detail_path"]).is_file():
            raise ValueError(f"找不到任务详情：{task['detail_path']}")
        task.update(status="in_progress", run_id=uuid4().hex)
        save_index(index, data)
        return task

    status = "done" if action == "finish" else "blocked"
    if task.get("run_id") != run_id or not run_id:
        raise ValueError("执行编号不匹配，请重新读取当前任务。")
    if task["status"] == status:
        return task
    if task["status"] != "in_progress":
        raise ValueError(f"任务当前状态不允许回写：{task['status']}")
    if not task.get("detail_path"):
        raise ValueError("任务需要先补齐 detail_path，才能记录执行结果。")
    if not record_path:
        raise ValueError("请提供执行记录文件。")
    record = record_path.read_text(encoding="utf-8").strip()
    if not record or (status == "blocked" and not (reason or "").strip()):
        raise ValueError("执行记录和适用的阻塞原因不能为空。")
    detail = path_in(root, task["detail_path"])
    body = detail.read_text(encoding="utf-8")
    marker = f"<!-- task-run:{run_id}:{status} -->"
    timestamp = now()
    if marker not in body.splitlines():
        result = f"阻塞原因：{reason.strip()}\n\n" if status == "blocked" else ""
        atomic_write(detail, f"{body.rstrip()}\n\n### {timestamp}\n\n{marker}\n\n{result}{record}\n")
    task["status"] = status
    if status == "done":
        task["completed_at"] = timestamp
    else:
        task["blocked_reason"] = reason.strip()
    if data["next_task_id"] == task_id:
        data["next_task_id"] = None
    save_index(index, data)
    return task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect").add_argument("root", type=Path)
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("root", type=Path)
    apply_parser.add_argument("plan", type=Path)
    apply_parser.add_argument("--dry-run", action="store_true")
    task_parser = sub.add_parser("task")
    task_parser.add_argument("root", type=Path)
    task_parser.add_argument("task_id")
    add_parser = sub.add_parser("add-task", help="登记项目需求并生成待办")
    add_parser.add_argument("root", type=Path)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--scope", required=True)
    add_parser.add_argument("--acceptance", required=True)
    add_parser.add_argument("--target-path", default="work/")
    defer_parser = sub.add_parser("defer", help="记录搁置决定并更新看板索引")
    defer_parser.add_argument("root", type=Path)
    selector = defer_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--task-id")
    selector.add_argument("--title")
    defer_parser.add_argument("--reason", required=True)
    defer_parser.add_argument("--resume-when", required=True)
    defer_parser.add_argument("--record", type=Path)
    for action in ("closeout", "reopen"):
        sub.add_parser(action).add_argument("root", type=Path)
    for action in ("start", "finish", "block"):
        update = sub.add_parser(action)
        update.add_argument("root", type=Path)
        update.add_argument("task_id")
        if action != "start":
            update.add_argument("run_id")
            update.add_argument("--record", required=True, type=Path)
        if action == "block":
            update.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("项目根目录必须是目录。")
        if args.command == "inspect":
            result = inspect(root)
        elif args.command == "apply":
            plan = read_object(args.plan)
            preview = apply(root, plan, True)
            if args.dry_run or not (preview["directories"] or preview["files"]):
                result = preview
                result["dry_run"] = args.dry_run
            else:
                with write_lock(root):
                    result = apply(root, plan, False)
                result["new_runtime_files"] = preview["new_runtime_files"]
        elif args.command == "task":
            result = read_task(root, args.task_id)
        elif args.command == "add-task":
            with write_lock(root):
                result = add_task(root, args.title, args.scope, args.acceptance, args.target_path)
        elif args.command == "defer":
            with write_lock(root):
                result = defer_task(
                    root, args.task_id, args.title, args.reason, args.resume_when, args.record,
                )
        elif args.command in {"closeout", "reopen"}:
            with write_lock(root):
                result = update_lifecycle(root, args.command)
        else:
            with write_lock(root):
                result = update_task(
                    root, args.task_id, args.command, getattr(args, "run_id", None),
                    getattr(args, "record", None), getattr(args, "reason", None),
                )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
