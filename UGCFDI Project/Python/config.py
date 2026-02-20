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