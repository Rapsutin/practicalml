import requests
from huey.contrib.djhuey import crontab, periodic_task
from ml_frontend.models import Candlestick, Prediction
from keras.models import load_model
from django.db.models import Max
import logging
import numpy as np
logger = logging.getLogger(__name__)
from datetime import timedelta

@periodic_task(crontab(minute='*/10'))
def fetch_data():
    response = requests.get("https://api.bitfinex.com/v2/candles/trade:1m:tBTCUSD/hist")
    candlesticks = response.json()
    Candlestick.create_candlesticks_from_json(candlesticks)
    logging.info("Fetched candlesticks")
    predict()

def predict():
    unpredicted_start_times = list(Candlestick.without_predictions())
    for i in range(1, 6):
        model = load_model(f"weights2_bitcoin_{i}_4.h5")
        unpredicted_windows = Candlestick.all_unpredicted_windows(unpredicted_start_times, i)
        logger.error(str(i) + " " + str(len(unpredicted_windows)))
        for window_with_datetimes in unpredicted_windows:
            window = window_with_datetimes[:, 1:]
            normalized_window = window - window[0][0]
            network_input = np.array([normalized_window])

            logger.error(window_with_datetimes[-1][0])
            prediction = model.predict(network_input)[0][0] + float(window[0][0])
            prediction_time = window_with_datetimes[-1][0] + timedelta(minutes=4)
            Prediction(time=prediction_time, prediction_type=str(i), prediction=prediction).save()





