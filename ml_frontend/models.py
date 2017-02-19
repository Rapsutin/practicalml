import logging
import numpy as np
logger = logging.getLogger(__name__)

from django.db import models
from django.utils import timezone
from datetime import datetime
from django.db.models import Max
from datetime import timedelta


class Candlestick(models.Model):
    time = models.DateTimeField(primary_key=True)
    open = models.DecimalField(max_digits=20, decimal_places=4)
    high = models.DecimalField(max_digits=20, decimal_places=4)
    low = models.DecimalField(max_digits=20, decimal_places=4)
    close = models.DecimalField(max_digits=20, decimal_places=4)

    @staticmethod
    def create_candlesticks_from_json(json):
        preprocessed_json = Candlestick._preprocess_json(json)
        for stick in preprocessed_json:
            timestamp = timezone.make_aware(
                datetime.fromtimestamp(stick[0] / 1000), timezone.utc)
            stick = Candlestick(
                timestamp,
                open=stick[1],
                close=stick[2],
                high=stick[3],
                low=stick[4])
            stick.save()

    @staticmethod
    def window(window_end_time, window_size_in_minutes):
        window = Candlestick.objects.filter(
            time__gt=window_end_time - timedelta(minutes=window_size_in_minutes),
            time__lte=window_end_time).order_by('time')
        logger.error(window)
        return np.array([candlestick.as_array() for candlestick in window])

    @staticmethod
    def without_predictions():
        unpredicted_window_start_times = Candlestick.objects.raw("""
            SELECT time
            FROM ml_frontend_candlestick
            WHERE time NOT IN
            (SELECT DISTINCT datetime(time, '-4 minutes')
            FROM ml_frontend_prediction)
            """)
        return unpredicted_window_start_times

    @staticmethod
    def all_unpredicted_windows(unpredicted_window_start_times, window_size_in_minutes):
        windows = np.array([
            Candlestick.window(start_time.time, window_size_in_minutes)
            for start_time in unpredicted_window_start_times
        ])
        windows_with_the_correct_length = [window for window in windows if len(window) == window_size_in_minutes]
        return np.array(windows_with_the_correct_length)

    @staticmethod
    def _preprocess_json(json):
        one_minute = 60000
        processed_sticks = []
        previous_stick = None
        json = sorted(json, reverse=True)
        for i in range(len(json)):
            stick = json[i]

            if previous_stick:
                time_difference = previous_stick[0] - stick[0]
                if time_difference != one_minute:
                    time_difference_in_minutes = int(time_difference /
                                                     one_minute)
                    for j in range(1, time_difference_in_minutes):
                        replacement = [
                            previous_stick[0] - j * one_minute,
                            previous_stick[4], previous_stick[4],
                            previous_stick[4], previous_stick[4]
                        ]
                        processed_sticks.append(replacement)

            previous_stick = stick
            processed_sticks.append(stick)
        return processed_sticks

    def as_array(self):
        return np.array(
            [self.time, self.open, self.high, self.low, self.close])


class Prediction(models.Model):
    time = models.DateTimeField()
    prediction = models.FloatField()
    prediction_type = models.CharField(max_length=100)

    class Meta:
        unique_together = (("time", "prediction_type"))
