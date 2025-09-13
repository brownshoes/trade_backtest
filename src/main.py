import argparse
import json

from init.initalization import init, load_config, load_csv, init_test, init_test2

from configs.create_config import create_config_from_json

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


def main():
    parser = argparse.ArgumentParser(description="Run analysis with a specific config.")
    parser.add_argument(
        "--config", type=str, required=True,
        help="The module path of the config file (e.g., btc_config)"
    )

    args = parser.parse_args()
    config = init_test2(args.config)

    #config = init(args.config)

    #init_test('configs/config_test.json')
    #print(config)




    # # Setup logger and get instance
    # logger = setup_logger(args.config)

    # # Now logger is properly configured
    # config = load_config(args.config)
    # val = config.to_string()
    # logger.info(val)
    # #print(val)
    

    # if config.mode == "backtest":
    #     bufferd_start_time = get_buffered_start_time(config.start_time, config.time_series)
    #     logger.info(f"Buffered start time: {bufferd_start_time}")
    #     df, list_of_dict = intake_csv_data(config.csv_input_file, bufferd_start_time, config.end_time)



if __name__ == '__main__':
    main()