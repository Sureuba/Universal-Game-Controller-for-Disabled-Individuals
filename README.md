# Universal-Game-Controller-for-Disabled-Individuals

File pathway
```
EMG_AI_Project/
├── Arduino/
│   └── emg_sensor.ino  :contains code to run the arduino
├── Python/
│   ├── data_collection.py  : collect data and store it in csv files 
│   ├── data_preprocessing.py   : uses Data and the csv files in it
│   ├── model_training.py       : simple NN, trains the AI model
│   └── real_time_classification.py : testing realtime 
├── Data/
│   ├── index_finger_up.csv
│   ├── wrist_flexing.csv
└── README.md
```

## How to Run

### Training the AI model

1. Run data_preprocessing.py
2. Run data_preprocessing.py
3. Run model training.py

Now the model is fully trained with the datasets saved in the data file

### Running the game

We want the game and AI to run at the same time as well as the muscle sensor to be sensing data and inputing it into the arduino. 

1. Plug in the EMG sensor to the arduino, plug in the arduino to the computer port
2. If the arduino code is not on the sensor we want to run the arduino code called emg_sensor.ino on the arduino environment which downloads the code to turns on the sensor and constantly inputs voltage data
3. Run the real_time_classification.py file which is exactly what it says, a real-time classifier using the neural network AI we trained
4. Run the Game file: dino_game.py connected to the AI on a separate terminal

Now the AI and gamee should work together with your muscles :) 

## AI model

For prototyping purposes we decided to use a simple classification neural network with 2 hidden layers. 


## Data Flow Summary

Collect raw EMG data → CSV files via data_collection.py

Preprocess → single features.csv via data_preprocessing.py

Train → saved Keras model via model_training.py


Deploy → live predictions via real_time_classification.py

