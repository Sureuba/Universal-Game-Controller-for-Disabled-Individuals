#student_transformer.py
import torch.nn as nn
from torch.nn import functional as F 
from tokenizer import EMGTokenizer
from transformer_encoder import *
from config import Config
#input raw emg signals, voltage readings
#output, which gesture, rest, fist , flex, extend wave

class StudentTransformer(nn.Module):
    def __init__(self, num_gestures = Config.num_gestures, n_embed = Config.n_embed, n_head = Config.n_head, n_layer = Config.n_layer, dropout = Config.dropout):
        #num_gestures = how many gestures to recognize 
        #n_embed = 128, how many numbers per token, basically describing it
        #n_head = 4, how many attention heads, eah head learns to pay attenton to different patterns in the signal, they all get combined
        super().__init__()


        #tokenizer, sort of same as kaparthy, basically it takes raw signals, converts to tokens

        self.tokenizer = EMGTokenizer(
            num_channels= Config.num_channels,
            window_size= Config.window_size,
            patch_size= Config.patch_size,
            n_embed=Config.n_embed

        )
        #trasofmer blocks, same as kaparthy, takes 4 transformer blocks, and stacks them, each block is for attention and feedforward
        self.blocks = nn.Sequential(
            *[Block(n_embed, n_head, dropout) for _ in range(n_layer)]

        )

        #final layer norm
        self.ln_f = nn.LayerNorm(n_embed)

        #classifaction head
        self.classifier = nn.Linear(n_embed, num_gestures)
        #takes the 128 numbers, output 5 scores, one per gesture, instead of vocab size, same as num getures = 5

    def forward(self, x, targets = None):
        #x is the raw emg windows, with the shape B,
        tokens = self.tokenizer(x) #turning raw voltage into tokens

        tokens = self.blocks(tokens) # run tokens through transformer blocks, context is added from the blocks

        #normalize, 
        tokens = self.ln_f(tokens) 
        #avergae all 10 tokens into one summary
        pooled = tokens.mean(dim = 1)
        # went from 10 tokens to 1 summary of whole window

        #classify which gestures
        logits  = self.classifier(pooled)
        #the highest score is prediction


        #IF TRAINING, WE WANT THE LOSS
        if targets is None:
            loss = None # no targets, just predicting, not training
        else:
            loss = F.cross_entropy(logits, targets)

        return logits, loss
        #logits are the 5 scores, loss is how wrong we are

