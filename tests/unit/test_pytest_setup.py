import asyncio


async def test_pytest_runs_async_tests_with_auto_mode():
    await asyncio.sleep(0)

    assert True
