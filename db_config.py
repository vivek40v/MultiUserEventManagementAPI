import sqlalchemy as sql
from sqlalchemy import MetaData, Table, Column, Integer, VARCHAR, UniqueConstraint, \
    func, BOOLEAN, create_engine, Date, Float, text, BigInteger, Index
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from settings import settings
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

use_sqlite = False  # Used in Table DDL as well
rdbms_type = 'postgres'

engine_str = f"postgresql+psycopg2://{settings.SOURCE_PG_USER}:{settings.SOURCE_PG_PASSWORD}@{settings.SOURCE_PG_HOST}:{settings.SOURCE_PG_PORT}/{settings.SOURCE_PG_DBNAME}"
temp_engine_str = f"postgresql+psycopg2://{settings.SOURCE_PG_USER}:{settings.SOURCE_PG_PASSWORD}@{settings.SOURCE_PG_HOST}:{settings.SOURCE_PG_PORT}"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_str)
Base = declarative_base()

# Create an engine and connect to the database
with create_engine(temp_engine_str, isolation_level='AUTOCOMMIT').connect() as conn:
    # Correctly use SQLAlchemy text function to create a SQL expression object
    res = conn.execute(text(f"SELECT * FROM pg_database WHERE datname = :db_name"), {'db_name': settings.SOURCE_PG_DBNAME})
    rows = res.rowcount > 0
    if not rows:
        # Create the database if it does not exist
        res_db = conn.execute(text(f"CREATE DATABASE {settings.SOURCE_PG_DBNAME};"))
        print(f"DB created {settings.SOURCE_PG_DBNAME}. Response: {res_db.rowcount}")


# Association Table (Many-to-Many)
user_events = Table(
    "user_events", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("event_id", Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    contact_number = Column(String(15))
    dob = Column(Date)
    role = Column(String(20), default="attendee")
    created_at = Column(TIMESTAMP, server_default=func.now())
    events = relationship("Event", secondary=user_events, back_populates="attendees")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))
    event_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    attendees = relationship("User", secondary=user_events, back_populates="events")


# Create an engine and connect to the database
with create_engine(engine_str, isolation_level='AUTOCOMMIT').connect() as conn:
    # Create Tables
    Base.metadata.create_all(bind=conn)