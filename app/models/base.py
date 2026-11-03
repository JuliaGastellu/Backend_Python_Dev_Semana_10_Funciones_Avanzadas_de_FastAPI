from datetime import datetime

from sqlalchemy import BigInteger, MetaData, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {int: BigInteger(), datetime: TIMESTAMP(timezone=True)}

