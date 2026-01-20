from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.db_config_results_model import ConfigResult
from database.db_setup import engine

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

def create_entry(config_result):
    with Session(engine) as session:
        try:
            session.add(config_result)
            session.commit()
            logger.info("ConfigResult: %s added successfully.", config_result.json_file_name)
            return True, None
        except IntegrityError as e:
            session.rollback() # Rollback the transaction to clear the error state
            if "UNIQUE constraint failed" in str(e):
                msg = f"Result '{config_result.json_file_name}' already exists."
                logger.error(msg)
                return False, msg
            else:
                logger.error("An unexpected error occurred: %s", e)
                return False, "Database integrity error"

        except Exception as e:
            session.rollback()
            logger.error("An unexpected error occurred: %s", e)
            return False, "Unexpected database error"

        
def get_all_entries():
    with Session(engine) as session:
        try:
            return session.query(ConfigResult).all()
        except Exception as e:
            logger.error("Failed to fetch ConfigResult rows: %s", e)
            return []
