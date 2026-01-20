import json
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.inspection import inspect

from database.db_setup import Base

CONFIG_RESULTS_TABLE_NAME = "config_results"


class ConfigResult(Base):
    __tablename__ = CONFIG_RESULTS_TABLE_NAME

    # Primary key
    json_file_name = Column(String, primary_key=True)

    # Time range
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    # Performance metrics
    total_pnl = Column(Float, nullable=False)
    total_pnl_percent = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    profit_factor = Column(Float, nullable=False)
    percent_profitable = Column(Float, nullable=False)

    def to_json(self):
        to_dict = {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
        return json.dumps(to_dict, indent=4)
