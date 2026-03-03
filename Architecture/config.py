class Config:
    #for the data coming in
    window_size = 200 #how many samppes per training window, 
    #increase means more context per window, like more values, capcapture gestures, slow interferece
    #decrease means less context, like less values coming in, might miss important gesture points
    overlap = 0.75

    ''' basically overlapp is for windowing the csv data, if the csv has 800 samples, window saize is 200, and overlapp is 0.75,
    then the stride for 'sectioning' of the slides would be (200*(1-0.75)) = 50, so window 1 would be samples 0 to 199, 
    window 2 would be 50 to 249, window 3 100 to 299 and so on, the overlap starts 50 samples later, and the window overlaps 75% with the previous one
    
    '''

    patch_size = 20
    '''how many samples per token, each sample woild be row in the excel csv'''
    train_split = 0.8
    ''' 80% of files go into training, so for ex, 80% of all the clench files go to training'''

    #for the model
    num_channels = 1
    ''' how many emg channels there are, we curretnyl have 1'''
    num_gestures = 3
    ''' how many gestures, right now the gestures are clench, rest, and wrist, but hopefully add more'''
    n_embed = 128
    ''' how many numbers represent each token, basically 128 dimensions of describing it, the more, more model capacity, better accuracy, more params, slow
            the less of this jus the opposite of if it was more
    '''
    n_head = 4

    ''' how many parallel attention heads, each learns different patterns about the data
        increasing means more diverse patterns more params, less means less diversity, might might patterns
        MUST DIVIDE EVENLY INTO n_embed, so in this case 128/4 is 32 per head, 32 numbers or dimensions
    '''
    n_layer = 4
    '''the depth of the model, how many transformers are stacked
        increasing means more processing epth, better at complex patterns, slower, might overfit
        decreasing is opposite of that
        3 to 4 layers should be fine    
    '''
    dropout = 0.2
    ''' dropout is just a technique DURING TRAINING it 'drops' neurons out, making them 0, so the model has to lear with less neurons
    
    '''

    #for da training
    batch_size = 16

    ''' how many parallel windows processing toegther, windows being the tokens'''
    learning_rate = 3e-4 #can also be #1e-4?
    ''' how big each wiehgt update step is, for the optimizer step, increasing it is faster training, overshoot optimal weights, unstable loss, decreasing means 
    slower training, more stable, smoother convergence,'''
    num_epochs = 50

    ''' number of tmimes to iterate thorugh the whole dataset, increasing means more training time, might ovefit if no ealry stopping, decreaseing it means less training time, might underfit'''
    patience = 10 # stop if val loss doesnt improve for 10 second epochs


    # ═══════════════════════════════════════════════════════════════════════
# RESEARCH PAPER REFERENCES
# ═══════════════════════════════════════════════════════════════════════

'''
SIGNAL PROCESSING & WINDOWING:
--------------------------------
window_size = 200ms:
  - "Myoelectric Control Using Transformers" (Sensor Review, 2025)
    Sweet spot: 100-250ms, 200ms captures full gesture dynamics

overlap = 0.75:
  - "Myoelectric Control Using Transformers" (Sensor Review, 2025)
    65-75% overlap improves accuracy by 3-5% for datasets <10K windows

patch_size = 20ms:
  - "xPatch: Dual-Stream Time Series Encoding" (2025)
    20ms patches optimal for 200ms windows, reduces self-attention cost


TRANSFORMER ARCHITECTURE:
--------------------------
n_embed = 128:
  - "xPatch: Dual-Stream Time Series Encoding" (2025)
    n_embed=128 recommended for edge deployment
  - "Lightweight Transformers for Real-Time EMG" (Sivakumar, 2025)
    Student models use n_embed=128 for ~300K parameter target

n_head = 4:
  - "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
    n_head=4 or 8 optimal, 4 provides multi-view temporal context without lag

n_layer = 3-4:
  - "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
    Most EMG models stay at 3-4 layers to keep <1M parameters for real-time use
  - "Lightweight Transformers for Real-Time EMG" (Sivakumar, 2025)
    Student: n_layer=4 (~300K params), Teacher: n_layer=12 (~15M params)

dropout = 0.1-0.2:
  - "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
    dropout=0.1-0.2 recommended for biosignal transformers


TRAINING HYPERPARAMETERS:
--------------------------
batch_size = 32-64:
  - "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
    batch_size=32-64 optimal, 32 better for smaller datasets (<10K samples)

learning_rate = 1e-4 to 3e-4:
  - "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
    learning_rate=1e-4 to 3e-4 for transformer training
  - "Lightweight Transformers for Real-Time EMG" (Sivakumar, 2025)
    Start with 1e-4 for initial training, drop to 1e-5 if loss oscillates


MULTI-CHANNEL EMG:
------------------
num_channels = 2-8:
  - "Deep Learning for sEMG-based Gesture Recognition" (MDPI, 2024)
    Multi-channel (2-8 sensors) improves accuracy 5-15% over single channel


SIGNAL PREPROCESSING (Not Yet Implemented):
--------------------------------------------
Bandpass Filter: 20-450 Hz (Butterworth order 4)
Notch Filter: 60 Hz (powerline noise removal), Q=30
Voltage Range: -5mV to +5mV
Artifact Rejection: ±6mV threshold
  - "Deep Learning for sEMG-based Gesture Recognition" (MDPI, 2024)
    Removes skin movement (low freq) and electronic hiss (high freq)


PERFORMANCE TARGETS:
--------------------
Accuracy: >95% on test set
Cross-user accuracy: >85% zero-shot on new users
Latency: <100ms total pipeline, <10ms inference only
Model size: <1M parameters (~300KB file) for edge deployment
  - Combined from: "Attention-Based Deep Learning for EMG" (SAI Computing, 2025)
                   "Lightweight Transformers for Real-Time EMG" (Sivakumar, 2025)


KNOWLEDGE DISTILLATION (Future Work):
--------------------------------------
Teacher: n_embed=512, n_layer=12 (~15M params)
Student: n_embed=128, n_layer=4 (~300K params)
Compression ratio: 50:1
Accuracy loss: <1.5%
Distillation temperature: 3.0
Alpha (balance): 0.7
  - "Lightweight Transformers for Real-Time EMG" (Sivakumar, 2025)


BIO-VAULT (Future Work):
-------------------------
SNR threshold: 15 dB minimum for vault storage
Similarity threshold: 95% cosine similarity for cache hit
Max signatures per user: 50
Embedding dimension: 128 (same as n_embed)
Cache hit rate target: 60-80%
Latency improvement: <1ms for cached predictions
  - "Bio-Vault: Zero-Shot Adaptation for Myoelectric Interfaces" 
    (Frontiers in Neurorobotics, 2025)
  - "Multi-User EMG Pattern Recognition" (Mobarak et al., 2025)
    SNR-based selection outperforms confidence by 5% accuracy
'''