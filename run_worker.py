"""
OmniMind AI — Celery Worker Runner Entrypoint

Usage:
  python run_worker.py
"""
from omnimind.worker.celery_app import celery_app

if __name__ == "__main__":
    print("Starting OmniMind AI Celery worker pool...")
    celery_app.worker_main(["worker", "--loglevel=info", "--pool=solo"])
