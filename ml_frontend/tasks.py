import requests
from huey.contrib.djhuey import crontab, periodic_task
from ml_frontend.models import Candlestick, Prediction
from django.db.models import Max
import logging
import numpy as np
import subprocess
logger = logging.getLogger(__name__)
from datetime import timedelta

@periodic_task(crontab(minute='*/15'))
def fetch_data():
    response = requests.get("https://api.bitfinex.com/v2/candles/trade:1m:tBTCUSD/hist")
    candlesticks = response.json()
    Candlestick.create_candlesticks_from_json(candlesticks)
    logging.info("Fetched candlesticks")
    predict()

def predict():
    unpredicted_start_times = list(Candlestick.without_predictions())
    for i in range(1, 6):
        unpredicted_windows = Candlestick.all_unpredicted_windows(unpredicted_start_times, i)
        logger.error(str(i) + " " + str(len(unpredicted_windows)))
        for window_with_datetimes in unpredicted_windows:
            window = window_with_datetimes[:, 1:]
            normalized_window = window - window[0][0]
            network_input = np.array([normalized_window]).astype(float).tolist()
            network_output = subprocess.run(["python", "neural_network.py", str(network_input)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            prediction = float(network_output.stdout.rstrip())
            prediction += float(window[0][0])
            logger.error(prediction)
            prediction_time = window_with_datetimes[-1][0] + timedelta(minutes=4)
            Prediction(time=prediction_time, prediction_type=str(i), prediction=prediction).save()

