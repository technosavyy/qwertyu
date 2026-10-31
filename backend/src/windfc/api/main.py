"""ASGI entry point: ``uvicorn windfc.api.main:app``."""

import logging

from windfc.api.app import create_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = create_app()
