import logging
import asyncio
from functools import wraps

def task(can_cancel):
    def decorator(func):
        @wraps(func)
        def func_wrapper(self, *args, **kwargs):
            return self.new_task(func(self, *args, **kwargs), can_cancel=can_cancel)
        return func_wrapper
    return decorator

class Service:
    def __init__(self, runner, name, config):
        self.log = logging.getLogger(name)
        # pylint: disable=E1128
        deps = self.do_init(runner, name, config)
        self.deps = set(deps) if deps is not None else set()
        self.rdeps = set()
        for dep in self.deps:
            dep.rdeps.add(self)
        self.running = False
        self.running_tasks = {}

    def do_init(self, runner, name, config):
        return None
        
    async def do_start(self):
        pass

    async def do_stop(self):
        pass

    async def start(self, loop):
        if self.running:
            return
        self.running = True
        self.loop = loop

        for dep in self.deps:
            await dep.start(loop)
        self.log.info("Starting service")
        await self.do_start()
        self.log.info("Service started")

    async def stop(self):
        if not self.running:
            return
        self.running = False
        for dep in self.rdeps:
            await dep.stop()
        self.log.info("Stopping service")
        await self.do_stop()
        await self.join_tasks()
        self.log.info("Service stopped")
        for dep in self.deps:
            await dep.stop()

    def new_task(self, coro, can_cancel):
        task = asyncio.ensure_future(coro)
        self.register_task(task, can_cancel)
        return task

    def register_task(self, task, can_cancel):
        self.running_tasks[task] = can_cancel
        def task_done(task):
            del self.running_tasks[task]
        task.add_done_callback(task_done)

    async def join_tasks(self):
        for task, can_cancel in list(self.running_tasks.items()):
            if can_cancel:
                task.cancel()

        pending = list(self.running_tasks)
        cancel_attempt = 1
        while pending:
            self.log.info("Waiting for tasks to finish")
            done, pending = await asyncio.wait(pending, timeout=5.0)

            for task in done:
                try:
                    task.result()
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    self.log.warn("Task returned exception: %s", ex)

            if pending:
                self.log.warn("Task(s) took too long to finish. Cancel attempt %s", cancel_attempt)
                cancel_attempt += 1
            for task in pending:
                task.cancel()

class PollingService(Service):
    default_interval=1.0

    def __init__(self, runner, name, config):
        self.poll_interval = config.getfloat('poll_interval', fallback=self.default_interval)
        super().__init__(runner, name, config)

    async def do_start(self):
        self.poll_loop()

    @task(can_cancel=True)
    async def poll_loop(self):
        while self.running:
            try:
                _ = await asyncio.shield(self.do_poll())
                await asyncio.sleep(self.poll_interval, loop=self.loop)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.log.error(e)
                try:
                    await asyncio.sleep(self.poll_interval, loop=self.loop)
                except asyncio.CancelledError:
                    raise

    @task(can_cancel=False)
    async def do_poll(self):
        pass