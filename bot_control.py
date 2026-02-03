#!/usr/bin/env python3
"""Bot control script - manage bot lifecycle"""
import os
import sys
import signal
import subprocess
import time
from pathlib import Path


class BotControl:
    """Control bot lifecycle - start, stop, restart, status"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.pid_file = self.project_dir / "bot.pid"
        self.venv_python = self.project_dir / "venv" / "bin" / "python"
        self.log_dir = self.project_dir / "logs"
        self.stdout_log = self.log_dir / "bot_stdout.log"
        self.stderr_log = self.log_dir / "bot_stderr.log"

        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)

    def get_running_pids(self):
        """Get all running bot process PIDs"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )

            pids = []
            for line in result.stdout.split('\n'):
                # Case-insensitive search for python process running src.main
                line_lower = line.lower()
                if 'python' in line_lower and 'src.main' in line_lower and 'grep' not in line_lower:
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except ValueError:
                            continue

            return pids
        except Exception as e:
            print(f"Error getting running PIDs: {e}")
            return []

    def get_pid_from_file(self):
        """Get PID from PID file"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return None
        return None

    def save_pid(self, pid):
        """Save PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
        except IOError as e:
            print(f"Warning: Could not save PID file: {e}")

    def remove_pid_file(self):
        """Remove PID file"""
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except IOError:
                pass

    def is_process_running(self, pid):
        """Check if process is running"""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def stop_process(self, pid, force=False):
        """Stop a process by PID"""
        try:
            if force:
                os.kill(pid, signal.SIGKILL)
                print(f"  Force killed process {pid}")
            else:
                os.kill(pid, signal.SIGTERM)
                print(f"  Sent SIGTERM to process {pid}")

                # Wait for graceful shutdown
                for _ in range(10):
                    if not self.is_process_running(pid):
                        print(f"  Process {pid} stopped gracefully")
                        return True
                    time.sleep(0.5)

                # Force kill if still running
                print(f"  Process {pid} didn't stop gracefully, force killing...")
                os.kill(pid, signal.SIGKILL)

            return True
        except (OSError, ProcessLookupError):
            return False

    def stop(self):
        """Stop all bot processes"""
        print("🛑 Stopping bot...")

        # Get all running bot processes
        running_pids = self.get_running_pids()

        if not running_pids:
            print("✅ No bot processes running")
            self.remove_pid_file()
            return True

        print(f"Found {len(running_pids)} running process(es): {running_pids}")

        # Stop all processes
        for pid in running_pids:
            self.stop_process(pid)

        # Verify all stopped
        time.sleep(1)
        still_running = self.get_running_pids()

        if still_running:
            print(f"⚠️  Warning: {len(still_running)} process(es) still running: {still_running}")
            print("Force killing remaining processes...")
            for pid in still_running:
                self.stop_process(pid, force=True)

        self.remove_pid_file()
        print("✅ All bot processes stopped")
        return True

    def start(self):
        """Start bot"""
        print("🚀 Starting bot...")

        # Check if already running
        running_pids = self.get_running_pids()
        if running_pids:
            print(f"⚠️  Bot already running with PID(s): {running_pids}")
            print("Use 'restart' to restart or 'stop' to stop first")
            return False

        # Start bot process
        try:
            # Change to project directory
            os.chdir(self.project_dir)

            # Open log files
            stdout_file = open(self.stdout_log, 'a')
            stderr_file = open(self.stderr_log, 'a')

            # Write startup marker
            stdout_file.write(f"\n{'='*60}\n")
            stdout_file.write(f"Bot started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            stdout_file.write(f"{'='*60}\n")
            stdout_file.flush()

            # Start bot in background
            process = subprocess.Popen(
                [str(self.venv_python), "-m", "src.main"],
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
                cwd=str(self.project_dir)
            )

            # Save PID
            self.save_pid(process.pid)

            # Give it a moment to start
            print(f"Waiting for bot to initialize...")
            time.sleep(3)

            # Check if it's still running
            if self.is_process_running(process.pid):
                print(f"✅ Bot started successfully (PID: {process.pid})")
                print(f"📝 PID saved to {self.pid_file}")
                print(f"📋 Logs: {self.stdout_log}")
                print(f"📋 Errors: {self.stderr_log}")
                return True
            else:
                print("❌ Bot failed to start - checking error logs...")

                # Read last few lines of stderr
                try:
                    stderr_file.close()
                    with open(self.stderr_log, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print("\n🔴 Last error messages:")
                            print("".join(lines[-20:]))
                except Exception:
                    pass

                self.remove_pid_file()
                return False

        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            self.remove_pid_file()
            return False

    def restart(self):
        """Restart bot"""
        print("🔄 Restarting bot...")
        self.stop()
        time.sleep(2)
        return self.start()

    def status(self):
        """Show bot status"""
        print("📊 Bot Status:")
        print("=" * 60)

        running_pids = self.get_running_pids()
        saved_pid = self.get_pid_from_file()

        if not running_pids:
            print("Status: ❌ NOT RUNNING")
        else:
            print(f"Status: ✅ RUNNING")
            print(f"Active processes: {len(running_pids)}")
            print(f"PIDs: {running_pids}")

        if saved_pid:
            is_valid = saved_pid in running_pids
            status = "✅ Valid" if is_valid else "⚠️  Stale"
            print(f"\nPID file: {status}")
            print(f"Saved PID: {saved_pid}")
        else:
            print(f"\nPID file: Not found")

        print("=" * 60)
        return len(running_pids) > 0

    def logs(self, lines=50, show_errors=False):
        """Show recent logs"""
        log_file = self.stderr_log if show_errors else self.stdout_log

        if not log_file.exists():
            print(f"📝 No log file found at {log_file}")
            return

        log_type = "errors" if show_errors else "output"
        print(f"📝 Last {lines} lines from {log_type} log:")
        print("=" * 60)

        try:
            result = subprocess.run(
                ["tail", f"-{lines}", str(log_file)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except Exception as e:
            print(f"Error reading logs: {e}")

        print("=" * 60)
        if not show_errors:
            print("💡 Tip: Use 'python bot_control.py logs errors' to see error log")


def main():
    """Main entry point"""
    control = BotControl()

    if len(sys.argv) < 2:
        print("Bot Control Script")
        print("=" * 60)
        print("Usage: python bot_control.py <command> [options]")
        print("\nCommands:")
        print("  start            Start the bot")
        print("  stop             Stop the bot")
        print("  restart          Restart the bot")
        print("  status           Show bot status")
        print("  logs [N]         Show last N lines of output (default: 50)")
        print("  logs errors [N]  Show last N lines of error log")
        print("\nExamples:")
        print("  python bot_control.py start")
        print("  python bot_control.py logs 100")
        print("  python bot_control.py logs errors 50")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        success = control.start()
        sys.exit(0 if success else 1)

    elif command == "stop":
        success = control.stop()
        sys.exit(0 if success else 1)

    elif command == "restart":
        success = control.restart()
        sys.exit(0 if success else 1)

    elif command == "status":
        is_running = control.status()
        sys.exit(0 if is_running else 1)

    elif command == "logs":
        # Check if second argument is "errors" or a number
        show_errors = False
        lines = 50

        if len(sys.argv) > 2:
            if sys.argv[2].lower() == "errors":
                show_errors = True
                if len(sys.argv) > 3:
                    lines = int(sys.argv[3])
            else:
                lines = int(sys.argv[2])

        control.logs(lines, show_errors)
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, stop, restart, status, logs")
        sys.exit(1)


if __name__ == "__main__":
    main()
