from __future__ import annotations

import os

from dagster import ConfigurableResource
from sqlalchemy.orm import Session, sessionmaker

from src.db.session import get_session_factory, init_db


class DatabaseResource(ConfigurableResource):
    database_url: str = ""

    def _url(self) -> str:
        return self.database_url or os.environ["DATABASE_URL"]

    def setup(self) -> None:
        init_db(self._url())

    def get_session(self) -> Session:
        factory: sessionmaker = get_session_factory(self._url())
        return factory()


class LitellmResource(ConfigurableResource):
    model: str = ""
    batch_size: int = 16

    def _model(self) -> str:
        return self.model or os.getenv("GEMINI_MODEL", "gemini/gemini-1.5-flash")

    def _batch_size(self) -> int:
        return self.batch_size or int(os.getenv("LLM_BATCH_SIZE", "16"))
