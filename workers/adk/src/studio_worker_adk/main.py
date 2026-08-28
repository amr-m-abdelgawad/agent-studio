from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from studio_worker_adk.workflows.ping import PingWorkflow, ping_activity


async def main() -> None:
    host = os.environ.get("TEMPORAL_HOST", "temporal:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "studio-dev")
    task_queue = os.environ.get("TEMPORAL_TASK_QUEUE", "studio-default")

    client = await Client.connect(host, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[PingWorkflow],
        activities=[ping_activity],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
