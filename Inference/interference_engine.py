#old nn flow, when from arduino to buffer to extract features, then to the model and prediction
# we did the extracting features part manually, but transformer does it

#the new flow is arduno, buffer, raw window, model, prediction
# no feature extraction is necessary, transformer finds it for itself


#inference engine loads trained transformer and makes predictions on raw emg windows
#first train model and then run it live

# we need to load trained weights from the main

#the student transformer creates an empty model, the the 

#the goal is a class that takes raw emg window, and resturns the gesture, so iputs 200 adc values, and 
#Outputs gesture name and the confidene score

import torch
import numpy as np
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Architecture.student_transformer import StudentTransformer
from Architecture.config import Config

_INFERENCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GESTURE_MAP = {0: 'rest', 1: 'clench', 2: 'wrist'}


class InterferenceEngine:
    '''loads the traied model and makes predictions on raw emg windows'''

    def __init__(self, model_path = 'student_model_best.pth', device = 'cpu'): # later replace with gpu if available
        self.device = device

        self.gesture_map = GESTURE_MAP
        
        self.model = StudentTransformer(
            num_gestures = Config.num_gestures,
            n_embed = Config.n_embed,
            n_head = Config.n_head,
            n_layer= Config.n_layer,
            dropout = Config.dropout
        )
        #at this point we have loaded the model, but it has random weights

        resolved_path = os.path.join(_INFERENCE_DIR, model_path) if not os.path.isabs(model_path) else model_path
        self.model.load_state_dict(torch.load(resolved_path, map_location=device), strict=False)
        #actually getting the numbers for model to use
        self.model.to(device)
        self.model.eval()
        #changing it to evaluation model or prediciton mode
        print(f"the model is now loaded from {model_path}")

    def preprocess_window(self, window):
        # we need to normalize adc to model input format

        window = np.array(window, dtype  = np.float32) #might need to look into float32 later
        
        #takes input of python list from ardunio, the 200, converts it to numpy array with 32 bbit floats, because math operations are faster on numpy arrays
        #pytorch models uses 32 bit floats, not the 64 bit python default
        ''' input would be [23, 24, 25, 26, ...] and then after it would be array([23, 24, 25, 26, ...], dtype = float32)'''
        window= (window / 4095.0) * 3.3 # ESP32: 12-bit ADC (0-4095), 3.3V logic
        ''' converts arduino's raw adc reading to actual voltage
        
            arduio adc outputs 0-1023(10 bit resolution)
            myoware sensor outputs 0 to 5 volts

            myoware sensor outputs analog voltage, continous value between 0 to 5 volts
            computers can only store digital numbres, integers like o, 1, 2,3
            arduino needs to convert voltage to number


            arduino has 10 bit adc, dividies 0 to 5 v range into 1024 steps, (2^10 = 1024)

            basically from 0v to 5v, there are 1024 marks, each mark is a discrete value arduino can output

            how big is each step?
            the total range is 5v - 0v = 5v
            the number of steps is 1024, one step is 5v / 1024 = 0.00488 votlts or around 4.88 mV
            adc can distinguish voltages about 5 mV apart
            when you measure 2.5V exactly, you divide it to see how much from 0 to 1024 it is, then convert it to 0 to 5 v

            this line only works for 1 channel, if we have more, we have to normalize each separately

            if more then 1: 
                    for i in range(window.shape[0]):
                        window[i] = (window[i] / 1023.0) * 5.0
                        window[i] = (window[i] - np.mean(window[i])) * 1000


            window  = window.reshape(1, Config.num_channels, -1) not 1

            
        '''
        window = ( window - np.mean(window)) * 1000
        ''' window - np(mean(window)) is centering, removes baseline/dc offsert
            everyone's resting voltage is different, we want changes from baseline, not absolute voltage
            centering the model makes it work for different people

            # Before centering:window = [2.3, 2.4, 2.5, 2.3, 2.2]  # Baseline around 2.3V
                mean = 2.34

                # After centering:
                window = [-0.04, 0.06, 0.16, -0.04, -0.14]  # Now centered at 0

                *1000 converts the volts to millivolts, since the volts are tiny numbes, millivolts makes it easier to work with

        '''
        window = window.reshape(1,1,-1)
        ''' changes shape from 1d to 3d, the model expects input shape [batch size, num channels, window size]
        

            before it would just be (200,0) 200 example of input voltages
            after it woild be (1,1,200), where the batch size is 1 window, the num channels is 1 sensor, and window size is 200 samples

            -1 means calculate dimension automatically, we have 200 elements total, first dimension is 1, second is 1, 200 muste the third dimension
            
            i was then thinking, why not have Config.batch_size and Config.num_channels if its mentioned in the config file?
            batch_size is for training, not inference. we only want to process 1 window at a time, not however many we have, which would 

            the 1 is there because we want to only go through 1 window at a time in real time , not batches, 


            the second 1 should match config, it could use config, the input to preprocess window is already 1d array
        '''
        return torch.tensor(window, dtype = torch.float32).to(self.device)
    ''' this does two things, first converts numpy array to pytorch tensor,

        since model is pytorch, only understand pytorch sensor
        then to(self.device) noves tensor to cpu or gpu
    '''

    def predict(self, window, return_confidence = True):
        #predit gestures from 200 adc values

        window_tensor  = self.preprocess_window(window)

        ''' takes the input which is raw adc, a python list, and outputs a tensor, normalized
        '''
        with torch.no_grad():
             #we dont want pytorch to track gradient information, because during training, pytoch tracks every operation for backpropogation
            #we dont need gradients during prediction, skipping gradients is faster, less memory, we dont need to record everything unlike in training
            
            logits, _ = self.model(window_tensor, targets = None)
        ''' self.model calls StudentTransformer's forward() method, the window_tensor is preprocessed input

            targets = NONE, we are predicting, so no training, it returns two things, the logits which are the raw scores for each gesture
            and loss, but we don't need loss, so _. the logits are the raw unnormalized scores before softmaxn
        '''

        probabiliites = torch.softmax(logits, dim = -1)

        confidence, predicted_class = torch.max(probabiliites, dim =-1)
        '''
        torch.max returns two things, the max value, and where the max value was 
        '''


        #convert to python types

        gesture_id = predicted_class.item()
        confidence_score = confidence.item()
        gesture_name = self.gesture_map[gesture_id]


        if return_confidence:
            return gesture_name, confidence_score
        else:
            return gesture_name

