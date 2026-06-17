class ExecutionPipeline:
    def __init__(
        self,
        middlewares,
        executor
    ):
        self.middlewares = middlewares
        self.executor = executor

    async def execute(
        self,
        context
    ):
        async def call_next(index):
            if index == len(self.middlewares):
                return await self.executor.execute(
                    context
                )

            middleware = self.middlewares[index]

            return await middleware.process(
                context,
                lambda ctx: call_next(index + 1)
            )

        return await call_next(0)