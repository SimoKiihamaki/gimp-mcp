"""
Diffusion-based Style Transfer model.

This module provides a wrapper around diffusion models for high-quality
style transfer. It supports both text-guided style transfer and reference-based
style transfer using example images.

The implementation uses the SDEdit approach (Meng et al., 2021) which adds noise 
to the content image and then guides the denoising process with style information.
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
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionControlNetPipeline, ControlNetModel

logger = logging.getLogger(__name__)

# Define available diffusion models
DIFFUSION_MODELS = {
    "sd1.5": {
        "name": "Stable Diffusion 1.5",
        "model_id": "runwayml/stable-diffusion-v1-5",
        "description": "Balanced quality and speed",
        "strengths": ["Good general purpose model", "Faster than SD 2.1"]
    },
    "sd2.1": {
        "name": "Stable Diffusion 2.1",
        "model_id": "stabilityai/stable-diffusion-2-1",
        "description": "Higher quality, slower inference",
        "strengths": ["Higher quality", "Better text understanding"]
    },
    "sdxl": {
        "name": "Stable Diffusion XL",
        "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "description": "Highest quality, slower inference",
        "strengths": ["Highest quality", "Best composition", "Most realistic"]
    },
    "controlnet-canny": {
        "name": "ControlNet (Canny edges)",
        "model_id": "lllyasviel/sd-controlnet-canny",
        "base_model_id": "runwayml/stable-diffusion-v1-5",
        "description": "Best for preserving structure",
        "strengths": ["Preserves edges and structure", "Best for drawings and line art"]
    }
}

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diffusion_weights")

# Ensure model directory exists
os.makedirs(MODELS_DIR, exist_ok=True)
