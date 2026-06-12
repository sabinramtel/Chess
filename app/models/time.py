from datetime import datetime

class Timer:
    """Game timer with increment support."""
    
    def __init__(self, initial_seconds, increment_seconds=0):
        self.initial_seconds = initial_seconds
        self.increment_seconds = increment_seconds
        self.time_remaining = initial_seconds
        self.last_update = None
        self.is_running = False
    
    def start(self):
        self.is_running = True
        self.last_update = datetime.now()
    
    def pause(self):
        if self.is_running:
            self.time_remaining = self.get_remaining()
            self.is_running = False
    
    def add_increment(self):
        if self.is_running:
            self.time_remaining = self.get_remaining() + self.increment_seconds
            self.last_update = datetime.now()
    
    def get_remaining(self):
        if not self.is_running:
            return max(0, self.time_remaining)
        
        elapsed = (datetime.now() - self.last_update).total_seconds()
        remaining = self.time_remaining - elapsed
        return max(0, remaining)
    
    def is_expired(self):
        return self.get_remaining() <= 0
    
    def format_time(self):
        remaining = int(self.get_remaining())
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes}:{seconds:02d}"
    
    def to_dict(self):
        return {
            'time_remaining': self.get_remaining(),
            'increment_seconds': self.increment_seconds,
            'is_running': self.is_running,
            'formatted': self.format_time()
        }