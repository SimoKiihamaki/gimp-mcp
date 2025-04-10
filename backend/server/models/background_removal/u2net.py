"""
U2Net background removal model.

This module provides a wrapper around the U2Net model for background removal.
U2Net is a popular model for salient object detection, which can be used for
background removal.

The model will be downloaded on first use if it doesn't exist locally.
"""
import os
import logging
import numpy as np
from io import BytesIO
from typing import Union, Tuple
import base64

from PIL import Image
import requests
import torch
import torch.nn.functional as F
from torchvision import transforms

logger = logging.getLogger(__name__)

# Model URLs - we'll use a pretrained model from torch hub
U2NET_MODEL_URL = "https://github.com/xuebinqin/U-2-Net/releases/download/NeurIPS2020/u2net.pth"
U2NETP_MODEL_URL = "https://github.com/xuebinqin/U-2-Net/releases/download/NeurIPS2020/u2netp.pth"

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
U2NET_PATH = os.path.join(MODELS_DIR, "u2net.pth")
U2NETP_PATH = os.path.join(MODELS_DIR, "u2netp.pth")

# Ensure model directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Create a simple implementation of U2Net for salient object detection
# Normally we would define the full model, but for simplicity we'll use torch hub
class U2NetModel:
    def __init__(self, model_path: str = U2NET_PATH, use_gpu: bool = True):
        """
        Initialize the U2Net model.
        
        Args:
            model_path (str): Path to the model weights
            use_gpu (bool): Whether to use GPU for inference if available
        """
        self.model_path = model_path
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        self.model = None
        
        # Transform for input images
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                std=[0.229, 0.224, 0.225])
        ])
        
        logger.info(f"Initializing U2Net model with device: {self.device}")
    
    def load_model(self):
        """
        Load the U2Net model.
        
        Downloads the model if it doesn't exist locally.
        """
        if self.model is not None:
            return
        
        # Check if model exists, if not download it
        if not os.path.exists(self.model_path):
            self._download_model()
        
        # Load model using torch hub
        try:
            # Try to load from torch hub
            self.model = torch.hub.load(
                'xuebinqin/U-2-Net', 
                'u2net',
                pretrained=False, 
                verbose=False
            )
            # Load saved weights
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            logger.info("U2Net model loaded successfully")
        except Exception as e:
            # Fallback to a simplified version or raise an error
            logger.error(f"Error loading U2Net model: {e}")
            raise RuntimeError(f"Failed to load U2Net model: {e}")
    
    def _download_model(self):
        """
        Download the U2Net model weights.
        """
        logger.info("Downloading U2Net model weights...")
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            url = U2NET_MODEL_URL if self.model_path == U2NET_PATH else U2NETP_MODEL_URL
            
            response = requests.get(url, stream=True)
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
        # Resize to model input size
        image = image.convert("RGB")
        image = image.resize((320, 320), Image.LANCZOS)
        
        # Apply transformations
        tensor = self.transform(image).unsqueeze(0)
        return tensor.to(self.device)
    
    def _postprocess_mask(self, mask: torch.Tensor, original_size: Tuple[int, int]) -> np.ndarray:
        """
        Postprocess the model output mask.
        
        Args:
            mask (torch.Tensor): Model output mask
            original_size (tuple): Original image size (width, height)
            
        Returns:
            numpy.ndarray: Processed mask as numpy array
        """
        # Convert to numpy and resize to original dimensions
        mask = F.interpolate(mask, size=original_size[::-1], mode='bilinear', align_corners=False)
        mask = mask.squeeze(0).squeeze(0).cpu().numpy()
        
        # Normalize and convert to uint8
        mask = (mask * 255).astype(np.uint8)
        return mask
    
    def predict(self, image: Image.Image) -> np.ndarray:
        """
        Predict the segmentation mask for an image.
        
        Args:
            image (PIL.Image): Input image
            
        Returns:
            numpy.ndarray: Segmentation mask
        """
        # Load model if not loaded
        if self.model is None:
            self.load_model()
        
        # Get original image size
        original_size = image.size
        
        # Preprocess image
        tensor = self._preprocess_image(image)
        
        # Run inference
        with torch.no_grad():
            output = self.model(tensor)
            # Take the final output (usually the most detailed one)
            mask = torch.sigmoid(output[0])
        
        # Postprocess mask
        mask = self._postprocess_mask(mask, original_size)
        return mask
    
    def remove_background(self, image: Image.Image, threshold: float = 0.5) -> Image.Image:
        """
        Remove the background from an image.
        
        Args:
            image (PIL.Image): Input image
            threshold (float): Threshold for mask binarization
            
        Returns:
            PIL.Image: Image with transparent background
        """
        # Predict mask
        mask = self.predict(image)
        
        # Threshold mask
        binary_mask = (mask > threshold * 255).astype(np.uint8) * 255
        
        # Convert to RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create mask image and apply to original
        mask_img = Image.fromarray(binary_mask).convert('L')
        
        # Create output image with alpha channel from mask
        data = np.array(image)
        data[:, :, 3] = mask_img
        
        return Image.fromarray(data)

# Helper function to load and preprocess image from base64
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

# Helper function to convert image to base64
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

# Main function to process an image for background removal
def process_background_removal(
    image_data: str, 
    threshold: float = 0.5, 
    use_gpu: bool = True
) -> str:
    """
    Process an image for background removal.
    
    Args:
        image_data (str): Base64-encoded image data
        threshold (float): Threshold for mask binarization (0.0-1.0)
        use_gpu (bool): Whether to use GPU for inference if available
        
    Returns:
        str: Base64-encoded image with transparent background
    """
    try:
        # Load the image
        image = load_image_from_base64(image_data)
        
        # Create and load the model
        model = U2NetModel(use_gpu=use_gpu)
        
        # Remove background
        result_image = model.remove_background(image, threshold)
        
        # Convert result to base64
        result_base64 = image_to_base64(result_image)
        
        return result_base64
    except Exception as e:
        logger.error(f"Error in background removal: {e}")
        raise RuntimeError(f"Background removal failed: {e}")
