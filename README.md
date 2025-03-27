# Universal-Game-Controller-for-Disabled-Individuals

File pathway

EMG_AI_Project/
├── Arduino/
│   └── emg_sensor.ino  :contains code to run the arduino
├── Python/
│   ├── data_collection.py  : collect data and store it in csv files 
│   ├── data_preprocessing.py   : uses Data and the csv files in it
│   ├── model_training.py       : main NN, 
│   └── real_time_classification.py : testing realtime 
├── Data/
│   ├── index_finger_up.csv
│   ├── wrist_flexing.csv
└── README.md

## AI model

For prototyping purposes we decided to use a simple classification neural network with 2 hidden layers. 


## Data Flow Summary

Collect raw EMG data → CSV files via data_collection.py

Preprocess → single features.csv via data_preprocessing.py

Train → saved Keras model via model_training.py

Deploy → live predictions via real_time_classification.py