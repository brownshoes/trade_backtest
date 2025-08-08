import time

class TimeIntervalEntry:
    def __init__(self, time_interval_sec=180):
        self.time_interval_sec = time_interval_sec
        self.last_time = int(time.time())

    def identify_entry(self):
        current_time = int(time.time())
        time_elapsed = current_time - self.last_time

        print(f"TimeInterval Entry: {current_time}  {self.last_time} {time_elapsed}", flush=True)

        if time_elapsed >= self.time_interval_sec:
            self.last_time = current_time
            return True
        return False
