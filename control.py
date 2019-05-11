from threading import Event, Timer

class Control(object):
    def __init__(self):
        self.execution_timer = None
        self.run_event = Event()
        self.exit_now = False
        self.timer_val = 0;
        self.sunrise = 0
        self.sunset = 0
        self.time = None
        self.simulate_run = False

    def schedule_logic_run(self):
        # Activate the event to let the desired
        # functionality run
        self.run_event.set()
        # Restart the timer to cause the next timer event
        # to allow the event to be set
        self.schedule_run(self.timer_val)

    def schedule_run(self, timer_val):
        self.timer_val = timer_val
        if self.execution_timer:
            self.execution_timer.cancel()
            self.execution_timer = None
        self.execution_timer = Timer(timer_val, self.schedule_logic_run)
        self.execution_timer.start()

