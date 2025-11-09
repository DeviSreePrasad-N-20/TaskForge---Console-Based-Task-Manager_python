"""
TaskForge - Console-Based Task Manager
Single-file Python application

Features implemented:
- Task class with id, title, priority, due_date, status
- TaskManager class with add, view, update, mark_complete, delete, filter, save, load
- tasks.json persistence (loaded at start, saved on changes or exit)
- Input validation and error handling
- Due-date filtering: today, this week
- Pretty console table (no external libs)

Run: python taskforge.py
"""

import json
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional

DATA_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"  # ISO format: 2025-10-10


class Task:
    def __init__(self, title: str, priority: str, due_date: Optional[date], status: str = "Pending", id: Optional[str] = None):
        self.id = id or self._generate_id()
        self.title = title
        self.priority = priority
        self.due_date = due_date  # stored as date object or None
        self.status = status

    @staticmethod
    def _generate_id() -> str:
        # short unique id
        return uuid.uuid4().hex[:8]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date.strftime(DATE_FORMAT) if self.due_date else None,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict):
        due = None
        if d.get("due_date"):
            try:
                due = datetime.strptime(d["due_date"], DATE_FORMAT).date()
            except Exception:
                due = None
        return cls(
            title=d.get("title", ""),
            priority=d.get("priority", "Low"),
            due_date=due,
            status=d.get("status", "Pending"),
            id=d.get("id"),
        )


class TaskManager:
    VALID_PRIORITIES = ["Low", "Medium", "High"]
    VALID_STATUS = ["Pending", "Completed"]

    def __init__(self):
        self.task_list: List[Task] = []
        self.load_from_file()

    def add_task(self, title: str, priority: str, due_date_str: Optional[str]):
        priority = self._normalize_priority(priority)
        due_date = self._parse_date(due_date_str) if due_date_str else None
        task = Task(title=title, priority=priority, due_date=due_date)
        self.task_list.append(task)
        print(f"Task added (ID: {task.id})")
        self.save_to_file()

    def view_tasks(self, tasks: Optional[List[Task]] = None):
        tasks = tasks if tasks is not None else self.task_list
        if not tasks:
            print("No tasks to show.")
            return

        # Compute column widths
        id_w = 8
        title_w = max(20, max((len(t.title) for t in tasks), default=20))
        pr_w = 8
        due_w = 12
        st_w = 10

        header = f"{'ID':<{id_w}}  {'Title':<{title_w}}  {'Priority':<{pr_w}}  {'Due Date':<{due_w}}  {'Status':<{st_w}}"
        print(header)
        print("-" * len(header))
        for t in tasks:
            due_str = t.due_date.strftime(DATE_FORMAT) if t.due_date else "-"
            print(f"{t.id:<{id_w}}  {t.title:<{title_w}}  {t.priority:<{pr_w}}  {due_str:<{due_w}}  {t.status:<{st_w}}")

    def update_task(self, task_id: str, new_title: Optional[str] = None, new_priority: Optional[str] = None, new_due: Optional[str] = None):
        t = self._find_by_id(task_id)
        if not t:
            print("Task not found.")
            return
        if new_title:
            t.title = new_title
        if new_priority:
            t.priority = self._normalize_priority(new_priority)
        if new_due is not None:
            t.due_date = self._parse_date(new_due) if new_due else None
        print("Task updated.")
        self.save_to_file()

    def mark_complete(self, task_id: str):
        t = self._find_by_id(task_id)
        if not t:
            print("Task not found.")
            return
        t.status = "Completed"
        print("Task marked as completed.")
        self.save_to_file()

    def delete_task(self, task_id: str):
        t = self._find_by_id(task_id)
        if not t:
            print("Task not found.")
            return
        self.task_list.remove(t)
        print("Task deleted.")
        self.save_to_file()

    def filter_tasks(self, by: str = "status", value: Optional[str] = None) -> List[Task]:
        by = by.lower()
        if by == "status":
            val = (value or "Pending").capitalize()
            return [t for t in self.task_list if t.status == val]
        elif by == "due_date":
            # value can be: today, week
            k = (value or "today").lower()
            today = date.today()
            if k == "today":
                return [t for t in self.task_list if t.due_date == today]
            elif k == "week":
                end = today + timedelta(days=6)
                return [t for t in self.task_list if t.due_date and today <= t.due_date <= end]
            else:
                # try parse specific date
                d = self._parse_date(value)
                if d:
                    return [t for t in self.task_list if t.due_date == d]
                return []
        else:
            return []

    def save_to_file(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.task_list], f, indent=2)
        except Exception as e:
            print(f"Failed to save tasks: {e}")

    def load_from_file(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.task_list = [Task.from_dict(d) for d in data]
        except FileNotFoundError:
            self.task_list = []
        except Exception as e:
            print(f"Failed to load tasks: {e}")
            self.task_list = []

    def _find_by_id(self, task_id: str) -> Optional[Task]:
        for t in self.task_list:
            if t.id == task_id:
                return t
        return None

    def _normalize_priority(self, p: str) -> str:
        p = (p or "").strip().capitalize()
        if p not in self.VALID_PRIORITIES:
            print(f"Unknown priority '{p}', defaulting to 'Low'. Valid: {', '.join(self.VALID_PRIORITIES)}")
            return "Low"
        return p

    def _parse_date(self, s: Optional[str]) -> Optional[date]:
        if not s:
            return None
        try:
            return datetime.strptime(s.strip(), DATE_FORMAT).date()
        except ValueError:
            print(f"Invalid date format: {s}. Expected {DATE_FORMAT}.")
            return None


def input_nonempty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Input cannot be empty.")


def main_menu():
    tm = TaskManager()
    print("Welcome to TaskForge — Console Task Manager")

    def show_help():
        print("\nCommands:")
        print("  1 - Add task")
        print("  2 - View tasks")
        print("  3 - Update task")
        print("  4 - Mark task complete")
        print("  5 - Delete task")
        print("  6 - Filter tasks")
        print("  7 - Save now")
        print("  8 - Exit")

    while True:
        show_help()
        cmd = input("\nEnter command number: ").strip()
        if cmd == "1":
            title = input_nonempty("Title: ")
            priority = input("Priority (Low/Medium/High) [Low]: ") or "Low"
            due = input(f"Due date ({DATE_FORMAT}) [blank = none]: ") or None
            tm.add_task(title, priority, due)

        elif cmd == "2":
            print("\nView options: \n  a - All  \n  b - By status  \n  c - By due date")
            o = input("Choose: ").strip().lower()
            if o == "a":
                tm.view_tasks()
            elif o == "b":
                st = input("Status (Pending/Completed) [Pending]: ") or "Pending"
                filtered = tm.filter_tasks(by="status", value=st)
                tm.view_tasks(filtered)
            elif o == "c":
                print("Due options: today, week, or YYYY-MM-DD")
                dv = input("Which: ") or "today"
                filtered = tm.filter_tasks(by="due_date", value=dv)
                tm.view_tasks(filtered)
            else:
                print("Unknown option")

        elif cmd == "3":
            tid = input_nonempty("Task ID to update: ")
            t = tm._find_by_id(tid)
            if not t:
                print("Task not found.")
                continue
            print("Press enter to keep existing value.")
            new_title = input(f"Title [{t.title}]: ") or None
            new_pr = input(f"Priority ({'/'.join(TaskManager.VALID_PRIORITIES)}) [{t.priority}]: ") or None
            new_due = input(f"Due date ({DATE_FORMAT}) [{t.due_date.strftime(DATE_FORMAT) if t.due_date else 'none'}]: ")
            if new_due == "":
                # keep existing
                new_due = None
            tm.update_task(tid, new_title, new_pr, new_due)

        elif cmd == "4":
            tid = input_nonempty("Task ID to mark complete: ")
            tm.mark_complete(tid)

        elif cmd == "5":
            tid = input_nonempty("Task ID to delete: ")
            confirm = input(f"Are you sure you want to delete {tid}? (y/N): ").strip().lower()
            if confirm == "y":
                tm.delete_task(tid)
            else:
                print("Delete cancelled.")

        elif cmd == "6":
            print("Filter by: 1) Status  2) Due date")
            choice = input("Choose: ").strip()
            if choice == "1":
                st = input("Status (Pending/Completed): ") or "Pending"
                res = tm.filter_tasks(by="status", value=st)
                tm.view_tasks(res)
            elif choice == "2":
                print("Due options: today, week, or YYYY-MM-DD")
                dv = input("Which: ") or "today"
                res = tm.filter_tasks(by="due_date", value=dv)
                tm.view_tasks(res)
            else:
                print("Unknown choice")

        elif cmd == "7":
            tm.save_to_file()
            print("Saved.")

        elif cmd == "8":
            tm.save_to_file()
            print("Goodbye — tasks saved.")
            break

        else:
            print("Unknown command. Enter a number 1-8.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted — saving and exiting.")
        try:
            TaskManager().save_to_file()
        except Exception:
            pass
        print("Bye.")