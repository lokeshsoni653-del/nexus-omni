"""
OmniMind AI — Celery Application Factory

When Redis is unavailable (dev/test mode), CELERY_TASK_ALWAYS_EAGER=True
causes all tasks to run synchronously in the calling thread — no broker needed.
"""
import logging
from celery import Celery

logger = logging.getLogger("omnimind.worker.celery_app")

_celery_app: Celery = None


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    global _celery_app
    if _celery_app is not None:
        return _celery_app

    from config import settings

    app = Celery(
        "omnimind",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["omnimind.worker.tasks"],
    )

    app.conf.update(
        # Serialization
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # Timezone
        timezone="UTC",
        enable_utc=True,
        # Dev mode: run tasks eagerly (synchronously) without a broker
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_eager_propagates=True,
        # Worker concurrency
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        # Result expiry (1 day)
        result_expires=86400,
        # Retry policy
        task_max_retries=3,
        task_default_retry_delay=5,
    )

    logger.info(
        f"Celery app created — broker: {settings.CELERY_BROKER_URL}, "
        f"always_eager={settings.CELERY_TASK_ALWAYS_EAGER}"
    )
    _celery_app = app
    return app


# Module-level singleton (imported by tasks.py and the FastAPI app)
celery_app = create_celery_app()
