#transformer_encoder.py
import torch
import torch.nn as nn
from torch.nn import functional as F

class Head(nn.Module): # one attention head, looks which tokens are more important, focused on a certain aspect of the data
 
    def __init__(self, n_embed, head_size, dropout):
        super().__init__()
        # n_embed = how many numbers each token has (128)
        # head_size = how many numbers this head works with (32)
        # dropout = randomly zero some neurons to prevent memorizing
        
        # Three parallel transformations of the input
        self.key = nn.Linear(n_embed, head_size, bias=False)    # "what do I contain?"
        self.query = nn.Linear(n_embed, head_size, bias=False)  # "what am I looking for?"
        self.value = nn.Linear(n_embed, head_size, bias=False)  # "what will I share?"
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        # x = [batch, num_tokens, n_embed] = [32, 10, 128]
        B, T, _ = x.shape  # B=batch, T=tokens
        
        # Generate Q, K, V for every token
        k = self.key(x)    # [B, T, head_size]
        q = self.query(x)  # [B, T, head_size]
        
        # Calculate attention scores: which tokens should talk to which
        # scale by sqrt(head_size), not sqrt(n_embed) — q and k are [B, T, head_size]
        wei = q @ k.transpose(-2, -1) * k.shape[-1]**-0.5  # [B, T, T]
        # wei[i][j] = how much token i cares about token j
        
        # Convert scores to probabilities (sum to 1)
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        
        # Use attention scores to mix the value vectors
        v = self.value(x)  # [B, T, head_size]
        out = wei @ v      # [B, T, head_size]
        # token i's output = weighted average of all tokens' values
        
        return out
    
class MultiHeadAttention(nn.Module): #multiiple heads work in parallel, dtermining which tokens are useful

    def __init__(self, n_embed, num_heads, head_size, dropout):
        super().__init__()
        # num_heads = how many heads to run (4)
        # each head gets head_size numbers (32)
        # 4 heads × 32 each = 128 total = n_embed
        
        # Create num_heads independent attention heads
        self.heads = nn.ModuleList([
            Head(n_embed, head_size, dropout) for _ in range(num_heads)
        ])
        
        # After concatenating all heads, mix them together
        self.proj = nn.Linear(n_embed, n_embed)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Run all heads independently on the same input
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        # concatenate: [B, T, 32] + [B, T, 32] + ... = [B, T, 128]
        
        # Mix all the heads together and apply dropout
        out = self.dropout(self.proj(out))
        return out

class FeedForward(nn.Module): # each token takes in info after attention, the code basically has the tokens summarizing the data that it learned
 
    def __init__(self, n_embed, dropout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embed, 4 * n_embed),  # expand: 128 → 512
            nn.ReLU(),                         # non-linearity: allows complex patterns
            nn.Linear(4 * n_embed, n_embed),  # compress: 512 → 128
            nn.Dropout(dropout),               # randomly zero 20% to prevent memorizing
        )

    def forward(self, x):
        # x goes through all layers in sequence
        return self.net(x)

class Block(nn.Module): # one block is communication(the attention part) where each token talks to each other, then the feeedforward part where each token thinks independently then computation. 4 are stacked to make a full transformer
  
    def __init__(self, n_embed, n_head, dropout):
        super().__init__()
        # n_embed = 128 numbers per token
        # n_head = 4 attention heads
        # dropout = regularization
        
        head_size = n_embed // n_head  # 128 // 4 = 32 per head
        
        # Communication: tokens exchange information
        self.sa = MultiHeadAttention(n_embed, n_head, head_size, dropout)
        
        # Computation: each token processes what it learned
        self.ffwd = FeedForward(n_embed, dropout)
        
        # Layer norms: keep numbers stable (prevent exploding/vanishing)
        self.ln1 = nn.LayerNorm(n_embed)
        self.ln2 = nn.LayerNorm(n_embed)

    def forward(self, x):
        # Attention with residual connection
        # x + ... means "add original signal back in"
        # prevents losing information through deep layers
        x = x + self.sa(self.ln1(x))    # normalize → attention → add back
        
        # Feedforward with residual connection
        x = x + self.ffwd(self.ln2(x))  # normalize → feedforward → add back
        
        return x
        # output has same shape as input: [B, T, n_embed]
        # but tokens now understand more context