from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # NOTE: https://github.com/sqlalchemy/sqlalchemy/issues/9189 pylint 문제같음
    # pylint:disable= not-callable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # pylint:disable= not-callable
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
