"""
Claude Code Proxy - Entry Point

Minimal entry point that imports the app from the api module.
Run with: uv run uvicorn server-2:app --host 0.0.0.0 --port 8084 --timeout-graceful-shutdown 5
"""

import os

# Load .env-2 file for this server instance
os.environ["FCC_ENV_FILE"] = ".env-2"

# Import settings FIRST to configure log file before importing app
from config.settings import get_settings
from config.logging_config import configure_logging

settings = get_settings()
# Override log file to be separated by server name
settings.log_file = "server2.log"
# Reconfigure logging with the updated log file
configure_logging(settings.log_file, force=True)

from api.app import app, create_app

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    import uvicorn

    from cli.process_registry import kill_all_best_effort

    try:
        # timeout_graceful_shutdown ensures uvicorn doesn't hang on task cleanup.
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_level="debug",
            timeout_graceful_shutdown=5,
        )
    finally:
        # Safety net: cleanup subprocesses if lifespan shutdown doesn't fully run.
        kill_all_best_effort()
