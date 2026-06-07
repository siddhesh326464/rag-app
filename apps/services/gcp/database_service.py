import logfire
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from google.cloud.sql.connector import Connector, IPTypes
from apps.config import settings



Base = declarative_base()

class QueryLog(Base):
    __tablename__ = 'query_logs'

    id = Column(String, primary_key=True)
    query = Column(Text)
    response = Column(Text)
    letency = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


connector = Connector()

def get_connection():
    """
    get_connection establishes a secure connection to the Cloud SQL instance using the Cloud SQL Connector.
    """
    conn = connector.connect(
        settings.DB_CONNECTION_NAME,
        "pg8000",
        user = settings.DB_USER,
        password = settings.DB_PASSWORD,
        db = settings.DB_NAME,
        ip_type = IPTypes.PUBLIC
    )

    return conn


try:
    if settings.DB_CONNECTION_NAME:
        engine = create_engine('postgresql+pg8000://', creator=get_connection)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logfire.info("Database connection established successfully.")

    else:
        logfire.warning("Database connection name is not set. Database connection will not be established.")
        session = None
except Exception as e:
    logfire.error(f"Error establishing database connection: {e}")
    session = None


def log_query(id:str, query:str, response:str, letency:float, metadata:dict):
    """
    log_query logs the query and its response to the database.
    """
    if not SessionLocal:return
    try:
        db = SessionLocal()
        log_entry = QueryLog(
            id=id,
            query=query,
            response=response,
            letency=letency,
            metadata=metadata
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logfire.info(f"Query logged successfully with id: {log_entry}")
        db.close()
    except Exception as e:
        logfire.error(f"Error logging query: {e}")
        