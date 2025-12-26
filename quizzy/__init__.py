from __future__ import annotations

import os

from flask import Flask

from .config import Config
from .routes import bp


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_object(Config())
    app.register_blueprint(bp)
    return app
