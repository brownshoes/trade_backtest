import argparse

from factories.initalization import init, load_config, load_csv


# from input.csv_input import intake_csv_data, get_buffered_start_time

# from log.logger import setup_logger

# import logging

#logger = logging.getLogger(__name__)

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

    init(args.config)

    config = load_config(args.config)
    logger.info(config.to_string())

    df, list_of_dict = load_csv(config)



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