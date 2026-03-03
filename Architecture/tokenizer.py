#tokenizer.py

import torch
import torch.nn as nn
from Architecture.config import Config

class EMGTokenizer(nn.Module):
    def __init__(self, 
                 num_channels=Config.num_channels,
                 window_size=Config.window_size,
                 patch_size=Config.patch_size,
                 n_embed=Config.n_embed):
        super().__init__()
        
        # Conv1D: splits signal into patches and embeds them
        self.conv = nn.Conv1d(
            in_channels=num_channels,   # number of EMG sensors
            out_channels=n_embed,       # embedding dimension
            kernel_size=patch_size,     # samples per token
            stride=patch_size           # no overlap between patches
        )
        
        # Positional encoding
        num_patches = window_size // patch_size
        self.position_embedding = nn.Embedding(num_patches, n_embed)
        self.num_patches = num_patches
    
    def forward(self, x):
        # x: [batch, num_channels, window_size]
        tokens = self.conv(x)           # [batch, n_embed, num_patches]
        tokens = tokens.transpose(1, 2) # [batch, num_patches, n_embed]
        
        positions = torch.arange(self.num_patches, device=x.device)
        pos_emb = self.position_embedding(positions)
        
        tokens = tokens + pos_emb
        return tokens