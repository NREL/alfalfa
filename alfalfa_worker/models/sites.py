from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Define variables DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
SQLALCHEMY_DATABASE_URI = 'postgresql://alfalfa_user:password@localhost:5432/alfalfa'

# ----- connect to the PostgreSQL database -----
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()
# ---- end connections


class Site(Base):
    __tablename__ = "site"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    name = Column(String)
    haystack = Column(JSON)

    def __repr__(self):
        return f"Site(id={self.id!r}, name={self.name!r})"


class Model(Base):
    """The file representing the model to be simulated. Each site can have only one model but can be used in multiple runs."""

    __tablename__ = "model"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    file = Column(String)
    site_id = Column(Integer, ForeignKey('site.id'))

    def __repr__(self) -> str:
        return f"Run(id={self.id!r}, site_id={self.site_id!r})"


class Run(Base):
    __tablename__ = "run"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    site_id = Column(Integer, ForeignKey("site.id"))
    # The model_id can be grabbed through the site, so check if we need this.
    model_id = Column(Integer, ForeignKey("model.id"))
    run_dir = Column(String)
    sim_type = Column(String)

    def __repr__(self):
        return f"Run(id={self.id!r}, site_id={self.site_id!r})"


class Point(Base):
    __tablename__ = "point"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    key = Column(String)
    name = Column(String)
    run_id = Column(Integer, ForeignKey("run.id"))
    # hmm, datatype of the value?
    value = Column(String)
