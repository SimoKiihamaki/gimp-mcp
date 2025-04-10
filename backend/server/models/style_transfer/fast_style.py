"""
Fast Neural Style Transfer model.

This module provides a wrapper around fast neural style transfer models
for applying artistic styles to images. It includes several pre-trained
style models (e.g., Van Gogh's Starry Night, Picasso, Ukiyo-e, etc.).

The models will be downloaded on first use if they don't exist locally.
"""
import os
import logging
import numpy as np
from io import BytesIO
from typing import Union, Tuple, Dict, Any, List, Optional
import base64

from PIL import Image
import requests
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms

logger = logging.getLogger(__name__)

# Define available styles with their model URLs and names
STYLE_MODELS = {
    "starry_night": {
        "name": "Starry Night (Van Gogh)",
        "url": "https://github.com/pytorch/examples/raw/main/fast_neural_style/saved_models/starry_night.pth"
    },
    "mosaic": {
        "name": "Mosaic",
        "url": "https://github.com/pytorch/examples/raw/main/fast_neural_style/saved_models/mosaic.pth"
    },
    "candy": {
        "name": "Candy",
        "url": "https://github.com/pytorch/examples/raw/main/fast_neural_style/saved_models/candy.pth"
    },
    "udnie": {
        "name": "Udnie",
        "url": "https://github.com/pytorch/examples/raw/main/fast_neural_style/saved_models/udnie.pth"
    }
}

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")

# Ensure model directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Define the transformer network for style transfer
class TransformerNetwork(nn.Module):
    """Transformer Network for Fast Neural Style Transfer."""
    def __init__(self):
        super(TransformerNetwork, self).__init__()
        
        # Initial convolution layers
        self.conv1 = nn.Conv2d(3, 32, kernel_size=9, stride=1, padding=4)
        self.in1 = nn.InstanceNorm2d(32, affine=True)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.in2 = nn.InstanceNorm2d(64, affine=True)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.in3 = nn.InstanceNorm2d(128, affine=True)
        
        # Residual layers
        self.res1 = ResidualBlock(128)
        self.res2 = ResidualBlock(128)
        self.res3 = ResidualBlock(128)
        self.res4 = ResidualBlock(128)
        self.res5 = ResidualBlock(128)
        
        # Upsampling layers
        self.deconv1 = nn.ConvTranspose2d(128, 64, kernel_size=3, stride=2, padding=1, output_padding=1)
        self.in4 = nn.InstanceNorm2d(64, affine=True)
        self.deconv2 = nn.ConvTranspose2d(64, 32, kernel_size=3, stride=2, padding=1, output_padding=1)
        self.in5 = nn.InstanceNorm2d(32, affine=True)
        self.deconv3 = nn.Conv2d(32, 3, kernel_size=9, stride=1, padding=4)
        
        # Non-linearities
        self.relu = nn.ReLU()
    
    def forward(self, x):
        y = self.relu(self.in1(self.conv1(x)))
        y = self.relu(self.in2(self.conv2(y)))
        y = self.relu(self.in3(self.conv3(y)))
        y = self.res1(y)
        y = self.res2(y)
        y = self.res3(y)
        y = self.res4(y)
        y = self.res5(y)
        y = self.relu(self.in4(self.deconv1(y)))
        y = self.relu(self.in5(self.deconv2(y)))
        y = self.deconv3(y)
        return y

class ResidualBlock(nn.Module):
    """Residual Block for the transformer network."""
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1)
        self.in1 = nn.InstanceNorm2d(channels, affine=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1)
        self.in2 = nn.InstanceNorm2d(channels, affine=True)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        residual = x
        out = self.relu(self.in1(self.conv1(x)))
        out = self.in2(self.conv2(out))
        out = out + residual
        return out
