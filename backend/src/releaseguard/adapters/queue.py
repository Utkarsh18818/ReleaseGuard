"""RQ delivery metadata only; graph records remain canonical."""

from redis import Redis
from rq import Queue
from rq.exceptions import DuplicateJobError


def connection(settings):
    if not settings.queue_password:
        raise ValueError("Operational Redis password not configured")
    return Redis(
        host=settings.queue_host,
        port=settings.queue_port,
        password=settings.queue_password,
        socket_connect_timeout=2,
        socket_timeout=3,
    )


class DeliveryQueue:
    def __init__(self, settings):
        self.queue = Queue(
            settings.target + "_" + settings.graph + "_jobs",
            connection=connection(settings),
            serializer="json",
        )

    def status(self, id):
        job = self.queue.fetch_job(id)
        return str(job.get_status().value) if job else None

    def enqueue(self, id, delivery):
        try:
            self.queue.enqueue(
                "releaseguard.worker.perform",
                id,
                job_id=delivery,
                unique=True,
                job_timeout=180,
                result_ttl=86400,
                failure_ttl=86400,
                description="ReleaseGuard investigation",
            )
        except DuplicateJobError:
            pass
