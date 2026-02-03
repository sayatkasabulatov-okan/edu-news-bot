"""Test script for task monitoring and error recovery"""
import asyncio
from src.utils.task_monitor import task_monitor
import time


async def test_task_monitoring():
    """Test task monitoring functionality"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: Task Monitoring")
    print("="*60)

    # Register test tasks
    print("\n📋 Регистрирую тестовые задачи...")
    task_monitor.register_task("test_task_success")
    task_monitor.register_task("test_task_failure")

    # Simulate successful task runs
    print("\n✅ Симулирую успешные выполнения...")
    for i in range(3):
        task_monitor.record_run("test_task_success", success=True)
        await asyncio.sleep(0.1)

    # Simulate failed task runs
    print("\n❌ Симулирую ошибки...")
    task_monitor.record_run("test_task_failure", success=False, error="Connection timeout")
    await asyncio.sleep(0.1)
    task_monitor.record_run("test_task_failure", success=False, error="Database error")

    # Check task health
    print("\n📊 Проверяю статус задач:")
    print(f"  test_task_success is healthy: {task_monitor.is_task_healthy('test_task_success')}")
    print(f"  test_task_failure is healthy: {task_monitor.is_task_healthy('test_task_failure')}")

    # Get health report
    print("\n📄 Health Report:")
    print(task_monitor.get_health_report())

    print("✅ ТЕСТ ЗАВЕРШЕН\n")


async def test_retry_mechanism():
    """Test retry mechanism with decorator"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: Retry Mechanism")
    print("="*60)

    attempt_count = 0

    @task_monitor.monitor("test_retry_task")
    async def flaky_task():
        """Simulates a task that fails first 2 times, then succeeds"""
        nonlocal attempt_count
        attempt_count += 1
        print(f"\n  Попытка #{attempt_count}")

        if attempt_count < 3:
            raise Exception(f"Temporary error on attempt {attempt_count}")

        print("  ✅ Задача выполнена успешно!")
        return "Success"

    # Test with manual retry loop
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await flaky_task()
            print(f"\n✅ Результат: {result}")
            break
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            if attempt < max_retries - 1:
                print(f"  🔄 Повтор через 1 секунду...")
                await asyncio.sleep(1)
            else:
                print(f"  ❌ Все попытки исчерпаны")

    # Check final status
    print("\n📊 Финальный статус задачи:")
    status = task_monitor.get_task_status("test_retry_task")
    if status:
        print(f"  Total runs: {status.total_runs}")
        print(f"  Total errors: {status.total_errors}")
        print(f"  Is healthy: {status.is_healthy}")

    print("\n✅ ТЕСТ ЗАВЕРШЕН\n")


async def main():
    """Run all monitoring tests"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ТЕСТОВ МОНИТОРИНГА")
    print("="*60)

    try:
        await test_task_monitoring()
        await test_retry_mechanism()

        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ МОНИТОРИНГА ЗАВЕРШЕНЫ")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
