#arduino produes 1 sample every 1 ms
# the model requires 200 samples at once
#circular buffer, will always be 200 samples after the first time model gets 200 live samples
from collections import deque
import numpy as np

#why deque?, when a python list is full, you have to manually delete oldest, 
#deque, or deque(maxlen=200) deletes odlest when you add to buffer, so when maxlen exceeds 200
#good for rolling windows, which is what we need

class EMGBuffer:
    #circular buffer for continous emg data collection

    def __init__(self, buffer_size = 2000, window_size = 200):
        '''
        args:
        buffer size is total samples to keep in memeory, 2 seconds at 1000hz
        
            why is buffer size = 2000? breaking it down
            the sampling rate is 1000 samples/second
            2 seconds of data is 1000*2 = 2000

            why 2 seconds?
            window size is 200 ms(0.2 seconds)
            we need around 10x for safety
            not too much memory. 2000 numbers isnt alot apparently

            researchers say 200ms is optimal


        window_size = how many samples needed for prediction which is 200 ms

    '''

        self.buffer_size = buffer_size
        self.window_size = window_size
        self.buffer = deque(maxlen=buffer_size)
        #why this line above, you create a queue that stores 2000 items, automatically deletes oldest when you add 2001st item
        self.timestamps = deque(maxlen = buffer_size)

    
    def add_sample(self, value, timestamp = None):

        '''
        add one sample to buffer
        value is the raw adc value which would be 1023 
        '''

        import time

        self.buffer.append(value)
        self.timestamps.append(timestamp if timestamp is not None else time.time()) # ehhh


    def get_latest_window(self):
        
        if len(self.buffer) < self.window_size:
            return None
        
        #getting the last window size samples
        window = list(self.buffer)[-self.window_size:]
        return np.array(window)
    

        '''
                # Buffer has 2000 samples:
        self.buffer = deque([512, 515, 520, ..., 2000 samples total])
        self.window_size = 200

        # Check if ready:
        if len(self.buffer) < 200:  # 2000 < 200? No, we're ready!
            return None  # Skip this

        # Get last 200:
        window = list(self.buffer)[-200:], [-200:] means last 200 items
        # Converts deque to list, then slices last 200 items

        # Convert to numpy array:
        return np.array(window)  # Shape: (200,)
        '''
    def is_ready(self):
        return len(self.buffer) >= self.window_size
    
    def clear(self):
        ''' clear buffer'''
        self.buffer.clear()
        self.timestamps.clear()

    def get_fill_percentage(self):
        ''' see how full buffer is'''
        return (len(self.buffer) / self.buffer_size) * 100
    

buffer = EMGBuffer(window_size=200)

# After 50 samples:
buffer.is_ready()  # False (50 < 200)

# After 150 samples:
buffer.is_ready()  # False (150 < 200)

# After 200 samples:
buffer.is_ready()  # True! (200 >= 200)

# After 1000 samples:
buffer.is_ready()  # True! (1000 >= 200)