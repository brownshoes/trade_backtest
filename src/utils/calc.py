def most_recent_complete_timestamp(timestamp, granularity):
    return timestamp - (timestamp % granularity)