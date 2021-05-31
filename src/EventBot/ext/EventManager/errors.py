class DateNotAvailable(BaseException):
    """
    Exception when a date is not available for scheduling
    """
    def __init__(self, date, event):
        self.date = date
        self.event = event
