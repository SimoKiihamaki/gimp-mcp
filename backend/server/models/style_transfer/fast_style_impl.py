"""
Implementation for Fast Neural Style Transfer model.

This file contains the implementation of the StyleTransferModel class and helper functions.
"""
import os
import logging
import numpy as np
from io import BytesIO
from typing import List, Dict, Any
import base64

from PIL import Image
import requests
import torch
from torchvision import transforms

from .fast_style import TransformerNetwork, STYLE_MODELS, MODELS_DIR

logger = logging.getLogger(__name__)

class StyleTransferModel:
    def __init__(self, style_name: str = "mosaic", use_gpu: bool = True):
        """
        Initialize the Style Transfer model.
        
        Args:
            style_name (str): Name of the style to use (must be in STYLE_MODELS)
            use_gpu (bool): Whether to use GPU for inference if available
        """
        if style_name not in STYLE_MODELS:
            raise ValueError(f"Unknown style '{style_name}'. Available styles: {', '.join(STYLE_MODELS.keys())}")
        
        self.style_name = style_name
        self.style_info = STYLE_MODELS[style_name]
        self.model_path = os.path.join(MODELS_DIR, f"{style_name}.pth")
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        self.model = None
        
        # Transform for input images
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                std=[0.229, 0.224, 0.225])
        ])
        
        logger.info(f"Initializing Style Transfer model for style: {self.style_info['name']} on device: {self.device}")
    
    def load_model(self):
        """
        Load the style transfer model.
        
        Downloads the model if it doesn't exist locally.
        """
        if self.model is not None:
            return
        
        # Check if model exists, if not download it
        if not os.path.exists(self.model_path):
            self._download_model()
        
        try:
            # Create and load the model
            self.model = TransformerNetwork()
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Style Transfer model for {self.style_info['name']} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Style Transfer model: {e}")
            raise RuntimeError(f"Failed to load Style Transfer model: {e}")
    
    def _download_model(self):
        """
        Download the style transfer model weights.
        """
        logger.info(f"Downloading style model weights for {self.style_info['name']}...")
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            response = requests.get(self.style_info['url'], stream=True)
            response.raise_for_status()
            
            with open(self.model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Model weights downloaded to {self.model_path}")
        except Exception as e:
            logger.error(f"Error downloading model weights: {e}")
            raise RuntimeError(f"Failed to download model weights: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess an image for inference.
        
        Args:
            image (PIL.Image): Input image
            
        Returns:
            torch.Tensor: Preprocessed image tensor
        """
        # Convert to RGB if needed
        image = image.convert("RGB")
        
        # Apply transformations
        tensor = self.transform(image).unsqueeze(0)
        return tensor.to(self.device)
    
    def _postprocess_image(self, tensor: torch.Tensor) -> Image.Image:
        """
        Convert a tensor back to a PIL Image.
        
        Args:
            tensor (torch.Tensor): The output tensor from the model
            
        Returns:
            PIL.Image: Processed image
        """
        # Denormalize
        tensor = tensor.squeeze(0).cpu()
        tensor = tensor * torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1) + \
                torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        tensor = torch.clamp(tensor, 0, 1)
        
        # Convert to PIL Image
        array = tensor.permute(1, 2, 0).numpy()
        array = (array * 255).astype(np.uint8)
        
        return Image.fromarray(array)
    
    def apply_style(self, image: Image.Image, strength: float = 1.0) -> Image.Image:
        """
        Apply the selected style to an image.
        
        Args:
            image (PIL.Image): Input image
            strength (float): Style strength (0.0 to 1.0)
            
        Returns:
            PIL.Image: Stylized image
        """
        # Load model if not loaded
        if self.model is None:
            self.load_model()
        
        # Save original size for later
        original_size = image.size
        
        # Preprocess
        tensor = self._preprocess_image(image)
        
        # Run inference
        with torch.no_grad():
            output_tensor = self.model(tensor)
        
        # Postprocess
        stylized_image = self._postprocess_image(output_tensor)
        
        # Resize back to original size if needed
        if stylized_image.size != original_size:
            stylized_image = stylized_image.resize(original_size, Image.LANCZOS)
        
        # If strength is less than 1.0, blend with the original image
        if strength < 1.0:
            blend_factor = strength
            original_image = image.resize(stylized_image.size)
            stylized_image = Image.blend(original_image, stylized_image, blend_factor)
        
        return stylized_image

    @staticmethod
    def get_available_styles() -> List[Dict[str, str]]:
        """
        Get a list of available style models.
        
        Returns:
            List[Dict[str, str]]: List of style dictionaries with 'id' and 'name' keys
        """
        return [
            {"id": style_id, "name": style_info["name"]}
            for style_id, style_info in STYLE_MODELS.items()
        ]

# Helper functions for loading and saving images from/to base64
def load_image_from_base64(base64_string: str) -> Image.Image:
    """
    Load an image from a base64 string.
    
    Args:
        base64_string (str): Base64-encoded image string
        
    Returns:
        PIL.Image: Loaded image
    """
    try:
        # Check if the string starts with a URL data prefix
        if ',' in base64_string and ';base64,' in base64_string:
            # Split off the prefix
            base64_string = base64_string.split(',', 1)[1]
        
        # Decode base64 string
        image_data = base64.b64decode(base64_string)
        
        # Open image from bytes
        return Image.open(BytesIO(image_data))
    except Exception as e:
        logger.error(f"Error loading image from base64: {e}")
        raise ValueError(f"Invalid image data: {e}")

def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    Convert an image to a base64 string.
    
    Args:
        image (PIL.Image): Image to convert
        format (str): Output format (PNG, JPEG, etc.)
        
    Returns:
        str: Base64-encoded image string
    """
    try:
        buffered = BytesIO()
        image.save(buffered, format=format)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        raise ValueError(f"Failed to convert image to base64: {e}")

# Main function to process an image for style transfer
def process_style_transfer(
    image_data: str, 
    style_name: str = "mosaic",
    strength: float = 1.0,
    use_gpu: bool = True
) -> str:
    """
    Process an image for style transfer.
    
    Args:
        image_data (str): Base64-encoded image data
        style_name (str): Name of the style to apply
        strength (float): Style strength (0.0 to 1.0)
        use_gpu (bool): Whether to use GPU for inference if available
        
    Returns:
        str: Base64-encoded stylized image
    """
    try:
        # Load the image
        image = load_image_from_base64(image_data)
        
        # Create and load the model
        model = StyleTransferModel(style_name=style_name, use_gpu=use_gpu)
        
        # Apply style
        result_image = model.apply_style(image, strength=strength)
        
        # Convert result to base64
        result_base64 = image_to_base64(result_image)
        
        return result_base64
    except Exception as e:
        logger.error(f"Error in style transfer: {e}")
        raise RuntimeError(f"Style transfer failed: {e}")

def get_available_styles() -> List[Dict[str, str]]:
    """
    Get a list of available style models.
    
    Returns:
        List[Dict[str, str]]: List of style dictionaries with 'id' and 'name' keys
    """
    return StyleTransferModel.get_available_styles()
