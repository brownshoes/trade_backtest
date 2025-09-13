from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

DB_NAME = 'database\db_configurations'

engine = create_engine(f"sqlite:///{DB_NAME}.db")
Base = declarative_base()

def init_db():
    # Import all models here
    # import database.models.json_record
    # import database.models.data_provenance_rec
    Base.metadata.create_all(bind=engine)