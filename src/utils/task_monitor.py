"""Task monitoring and health check utilities"""
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import asyncio


@dataclass
class TaskStatus:
    """Status of a monitored task"""
    name: str
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    total_runs: int = 0
    total_errors: int = 0
    is_healthy: bool = True


class TaskMonitor:
    """Monitor background tasks and track their health"""

    def __init__(self):
        self._tasks: Dict[str, TaskStatus] = {}
        self._health_check_interval = 300  # 5 minutes
        self._max_time_since_success = timedelta(hours=25)  # Allow one missed daily run

    def register_task(self, task_name: str):
        """Register a new task for monitoring"""
        if task_name not in self._tasks:
            self._tasks[task_name] = TaskStatus(name=task_name)
            logger.info(f"Registered task for monitoring: {task_name}")

    def record_run(self, task_name: str, success: bool = True, error: Optional[str] = None):
        """Record task execution"""
        if task_name not in self._tasks:
            self.register_task(task_name)

        task = self._tasks[task_name]
        task.last_run = datetime.now()
        task.total_runs += 1

        if success:
            task.last_success = datetime.now()
            task.is_healthy = True
            logger.info(f"Task '{task_name}' completed successfully (total: {task.total_runs})")
        else:
            task.last_error = error or "Unknown error"
            task.total_errors += 1
            logger.error(f"Task '{task_name}' failed: {error} (errors: {task.total_errors}/{task.total_runs})")

            # Mark as unhealthy if too many errors
            if task.total_errors > 3 and task.total_errors / task.total_runs > 0.5:
                task.is_healthy = False
                logger.warning(f"Task '{task_name}' marked as unhealthy (error rate: {task.total_errors}/{task.total_runs})")

    def get_task_status(self, task_name: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        return self._tasks.get(task_name)

    def get_all_statuses(self) -> Dict[str, TaskStatus]:
        """Get statuses of all monitored tasks"""
        return self._tasks.copy()

    def is_task_healthy(self, task_name: str) -> bool:
        """Check if a task is healthy"""
        task = self._tasks.get(task_name)
        if not task:
            return True  # Unknown tasks are considered healthy

        # Check if task has run recently
        if task.last_success:
            time_since_success = datetime.now() - task.last_success
            if time_since_success > self._max_time_since_success:
                logger.warning(f"Task '{task_name}' hasn't succeeded in {time_since_success}")
                return False

        return task.is_healthy

    def get_health_report(self) -> str:
        """Get a formatted health report for all tasks"""
        if not self._tasks:
            return "📊 No tasks are being monitored"

        report = "📊 <b>Task Health Report</b>\n\n"

        for task_name, task in self._tasks.items():
            status_emoji = "✅" if task.is_healthy else "❌"
            report += f"{status_emoji} <b>{task_name}</b>\n"

            if task.last_run:
                time_ago = datetime.now() - task.last_run
                report += f"  • Last run: {self._format_timedelta(time_ago)} ago\n"
            else:
                report += f"  • Last run: Never\n"

            if task.last_success:
                time_ago = datetime.now() - task.last_success
                report += f"  • Last success: {self._format_timedelta(time_ago)} ago\n"

            if task.total_runs > 0:
                success_rate = ((task.total_runs - task.total_errors) / task.total_runs) * 100
                report += f"  • Success rate: {success_rate:.1f}% ({task.total_runs} runs)\n"

            if task.last_error:
                report += f"  • Last error: {task.last_error[:50]}...\n"

            report += "\n"

        return report

    @staticmethod
    def _format_timedelta(td: timedelta) -> str:
        """Format timedelta as human-readable string"""
        total_seconds = int(td.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            return f"{total_seconds // 60}m"
        elif total_seconds < 86400:
            return f"{total_seconds // 3600}h"
        else:
            return f"{total_seconds // 86400}d"

    def monitor(self, task_name: str):
        """Decorator to monitor async task execution"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                self.register_task(task_name)

                try:
                    result = await func(*args, **kwargs)
                    self.record_run(task_name, success=True)
                    return result
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    self.record_run(task_name, success=False, error=error_msg)
                    raise

            return wrapper
        return decorator


# Global task monitor instance
task_monitor = TaskMonitor()
