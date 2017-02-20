from keras.models import load_model
import sys
import numpy as np

if __name__ == '__main__':
    window = np.array(eval(sys.argv[1])) # INSECURE!
    window_size = len(window[0])
    model = load_model(f'weights2_bitcoin_{window_size}_4.h5')
    prediction = model.predict(window)
    print(prediction[0][0])

