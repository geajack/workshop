from time import time

class TimedInterval:

    def __init__(self, name=None):
        self.name = name
        self.duration = None
        self.start_time = None
        self.subintervals = []
        self.data = {}

    def subinterval(self, name=None):
        sub = TimedInterval(name)
        self.subintervals.append(sub)
        return sub

    def put(self, key, value):
        self.data[key] = value

    def start(self):
        self.start_time = time()

    def stop(self):
        if self.duration is not None:
            return

        for sub in self.subintervals:
            sub.stop()
        
        if self.start_time is not None:
            self.duration = time() - self.start_time

    def show(self, indent=0):
        name = self.name if self.name else "anonymous"

        if self.duration >= 1:
            duration = f"{self.duration:.3f}s"
        else:
            duration = f"{int(self.duration * 1000)}ms"

        print(" " * indent + f"{name} - {duration}")
        for sub in self.subintervals:
            sub.show(indent=indent + 2)

    def __enter__(self):
        self.start()

    def __exit__(self, *exc_info):
        self.stop()


class ProgressCounter:

    def __init__(self, n_items):
        self.n_items = n_items
        self.n_done = 0
        self.t0 = time()
        self.t = self.t0
        self.dt = None

    def step(self):
        self.n_done += 1
        t = time()
        self.dt = t - time()
        self.t = t

    @property
    def remaining(self):
        seconds_elapsed = self.t - self.t0
        seconds_remaining = (seconds_elapsed / self.n_done) * (self.n_items - self.n_done)
        return seconds_remaining
    
    def log(self):
        if self.n_done == 0:
            return f"[0/{self.n_items}]"

        seconds_elapsed = self.t - self.t0
        seconds_remaining = (seconds_elapsed / self.n_done) * (self.n_items - self.n_done)

        days_remaining = int(seconds_remaining / (24 * 3600))
        seconds_remaining -= days_remaining * (24 * 3600)
        hours_remaining = int(seconds_remaining / 3600)
        seconds_remaining -= hours_remaining * 3600
        minutes_remaining = int(seconds_remaining / 60)
        seconds_remaining = int(seconds_remaining - minutes_remaining)

        timestring = ""
        if days_remaining > 0:
            timestring += f"{days_remaining}d"
        if hours_remaining > 0:
            timestring += f"{hours_remaining}h"
        if minutes_remaining > 0:
            timestring += f"{minutes_remaining}m"
        if seconds_remaining > 0:
            timestring += f"{seconds_remaining}s"

        return f"[{self.n_done}/{self.n_items}] - eta {timestring}"