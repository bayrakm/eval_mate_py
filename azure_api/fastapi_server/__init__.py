import logging
import sys
from pathlib import Path

import azure.functions as func
from azure.functions import AsgiMiddleware

# Ensure the repository root (which contains the `app` package) is importable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.server import app  # noqa: E402

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Entry point for the Azure Function – forwards requests to FastAPI."""
    logger.info("Forwarding request to FastAPI backend via ASGI middleware")
    asgi = AsgiMiddleware(app)
    return asgi.handle(req, context)
