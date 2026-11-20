"""Declarative registry shared with the database migration owner."""

from sqlalchemy import BigInteger, Column, MetaData, Table
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Use the physical names and constraints defined in DOC 6.4-B."""


# Resolve external FKs for standalone repository tests without adding partial
# tables to the metadata DB will use for complete models and migrations.
_external_references = MetaData()
user_reference = Table("users", _external_references, Column("id", BigInteger, primary_key=True))
post_reference = Table("posts", _external_references, Column("id", BigInteger, primary_key=True))
dish_reference = Table("dishes", _external_references, Column("id", BigInteger, primary_key=True))
tag_reference = Table("tags", _external_references, Column("id", BigInteger, primary_key=True))
