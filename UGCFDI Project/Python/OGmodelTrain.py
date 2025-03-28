"""
model_training.py

This script loads features.csv, encodes the movement labels,
trains a neural network classifier using TensorFlow/Keras, and saves the model.
outputs a classifier file
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

import tensorflow as tf
keras = tf.keras
# from tensorflow.keras import models, layers, utils

# Load features dataset
data = pd.read_csv("features.csv")
X = data[["mean", "std", "rms", "max", "min"]].values
labels = data["label"].values
print(labels)

# Encode string labels to integers
le = LabelEncoder()
y_encoded = le.fit_transform(labels)
num_classes = len(le.classes_)
y = keras.utils.to_categorical(y_encoded, num_classes)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define a simple neural network model
model = keras.models.Sequential([
    keras.layers.Dense(32, activation='relu', input_shape=(X_train.shape[1],)),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(num_classes, activation='softmax') #output layer softmax makes output btwn 0 to 1
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=50, batch_size=4, validation_data=(X_test, y_test))

# Save the trained model and label classes
model.save("emg_classifier.h5")
# Save label encoder classes for future reference (optional: here we print them)
print("Trained classes:", le.classes_)
print("Model saved as emg_classifier.h5")
