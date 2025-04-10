"""
Implementation for Diffusion-based Style Transfer model.

This file contains the implementation of the DiffusionStyleTransferModel class and helper functions.
"""
import os
import logging
import numpy as np
from io import BytesIO
from typing import Union, Tuple, Dict, Any, List, Optional
import base64
import time

from PIL import Image
import requests
import torch
import torch.nn.functional as F
from diffusers import StableDiffusionImg2ImgPipeline, AutoencoderKL, DDIMScheduler

from .diffusion_style import DIFFUSION_MODELS, MODELS_DIR

logger = logging.getLogger(__name__)

class DiffusionStyleTransferModel:
    def __init__(
        self,
        model_id: str = "sd1.5",
        use_gpu: bool = True,
        use_half_precision: bool = True,
    ):
        """
        Initialize the Diffusion Style Transfer model.
        
        Args:
            model_id (str): ID of the diffusion model to use (must be in DIFFUSION_MODELS)
            use_gpu (bool): Whether to use GPU for inference if available
            use_half_precision (bool): Whether to use half precision (float16) for faster inference
        """
        if model_id not in DIFFUSION_MODELS:
            raise ValueError(f"Unknown model '{model_id}'. Available models: {', '.join(DIFFUSION_MODELS.keys())}")
        
        self.model_id = model_id
        self.model_info = DIFFUSION_MODELS[model_id]
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.use_half_precision = use_half_precision and self.use_gpu
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        self.torch_dtype = torch.float16 if self.use_half_precision else torch.float32
        self.pipeline = None
        
        # Path to store the model locally
        self.model_path = os.path.join(MODELS_DIR, model_id)
        
        logger.info(f"Initializing Diffusion Style Transfer model: {self.model_info['name']} on device: {self.device}")
    
    def load_model(self):
        """
        Load the diffusion model.
        
        Downloads and caches the model if it doesn't exist locally.
        """
        if self.pipeline is not None:
            return
        
        try:
            # Using img2img pipeline for style transfer
            scheduler = DDIMScheduler.from_pretrained(
                self.model_info.get("model_id"),
                subfolder="scheduler",
                torch_dtype=self.torch_dtype
            )
            
            self.pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                self.model_info.get("model_id"),
                scheduler=scheduler,
                torch_dtype=self.torch_dtype,
            )
            
            if self.use_gpu:
                self.pipeline = self.pipeline.to(self.device)
                
            # Enable memory optimization if available
            if hasattr(self.pipeline, "enable_attention_slicing"):
                self.pipeline.enable_attention_slicing()
                
            logger.info(f"Diffusion model {self.model_info['name']} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading diffusion model: {e}")
            raise RuntimeError(f"Failed to load diffusion model: {e}")
    
    def apply_style_with_text(
        self,
        image: Image.Image,
        style_prompt: str,
        negative_prompt: str = "",
        strength: float = 0.75,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """
        Apply style to an image using a text prompt.
        
        Args:
            image (PIL.Image): Input image
            style_prompt (str): Text prompt describing the desired style
            negative_prompt (str): Text prompt describing what to avoid
            strength (float): Amount of noise to add (0.0 to 1.0)
            guidance_scale (float): How closely to follow the prompt (higher = more faithful to prompt)
            num_inference_steps (int): Number of denoising steps (more = higher quality but slower)
            seed (int, optional): Random seed for reproducible results
            
        Returns:
            PIL.Image: Stylized image
        """
        # Load model if not loaded
        if self.pipeline is None:
            self.load_model()
        
        # Save original size for later
        original_size = image.size
        
        # Prepare the image (resize if needed)
        if max(image.size) > 1024:
            ratio = 1024 / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Set random seed for reproducibility if provided
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # Run the diffusion pipeline
        start_time = time.time()
        result = self.pipeline(
            prompt=style_prompt,
            negative_prompt=negative_prompt,
            image=image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        ).images[0]
        
        inference_time = time.time() - start_time
        logger.info(f"Style transfer completed in {inference_time:.2f} seconds using text prompt")
        
        # Resize back to original size if needed
        if result.size != original_size:
            result = result.resize(original_size, Image.LANCZOS)
        
        return result
    
    def apply_style_with_image(
        self,
        content_image: Image.Image,
        style_image: Image.Image,
        strength: float = 0.75,
        content_strength: float = 0.5,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """
        Apply style to an image using a reference style image.
        
        Note: This is a simplified implementation of reference-based style transfer.
        For production use, consider implementing DreamBooth fine-tuning or textual inversion.
        
        Args:
            content_image (PIL.Image): Input content image
            style_image (PIL.Image): Input style image
            strength (float): Amount of noise to add (0.0 to 1.0)
            content_strength (float): How much to preserve content vs. style (0.0 to 1.0)
            guidance_scale (float): How closely to follow the derived style (higher = more stylized)
            num_inference_steps (int): Number of denoising steps (more = higher quality but slower)
            seed (int, optional): Random seed for reproducible results
            
        Returns:
            PIL.Image: Stylized image
        """
        # Load model if not loaded
        if self.pipeline is None:
            self.load_model()
        
        # Save original size for later
        original_size = content_image.size
        
        # Prepare the content image (resize if needed)
        if max(content_image.size) > 1024:
            ratio = 1024 / max(content_image.size)
            new_size = (int(content_image.size[0] * ratio), int(content_image.size[1] * ratio))
            content_image = content_image.resize(new_size, Image.LANCZOS)
        
        # Convert to RGB if needed
        if content_image.mode != "RGB":
            content_image = content_image.convert("RGB")
        if style_image.mode != "RGB":
            style_image = style_image.convert("RGB")
            
        # For reference-based style transfer, we use a technique where we derive a prompt
        # This is a simplified approach - more advanced methods would use textual inversion or fine-tuning
        style_prompt = "An image in the style of the reference image, artistic style transfer"
        
        # Set random seed for reproducibility if provided
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # SDEdit approach: add noise then denoise with guidance
        start_time = time.time()
        
        # In a real implementation, we would extract style features or use CLIP to derive text prompts
        # For now, we'll use a simple approach with img2img and the generic prompt
        result = self.pipeline(
            prompt=style_prompt,
            negative_prompt="blurry, distorted, ugly, poorly drawn",
            image=content_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        ).images[0]
        
        inference_time = time.time() - start_time
        logger.info(f"Style transfer completed in {inference_time:.2f} seconds using reference image")
        
        # Resize back to original size if needed
        if result.size != original_size:
            result = result.resize(original_size, Image.LANCZOS)
        
        return result
    
    @staticmethod
    def get_available_models() -> List[Dict[str, str]]:
        """
        Get a list of available diffusion models.
        
        Returns:
            List[Dict[str, str]]: List of model dictionaries with 'id', 'name', and 'description' keys
        """
        return [
            {
                "id": model_id,
                "name": model_info["name"],
                "description": model_info.get("description", ""),
                "strengths": model_info.get("strengths", [])
            }
            for model_id, model_info in DIFFUSION_MODELS.items()
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

# Main function to process an image for diffusion-based style transfer
def process_diffusion_style_transfer(
    image_data: str,
    style_type: str = "text",  # "text" or "image"
    style_prompt: str = "Oil painting in the style of Van Gogh",
    style_image_data: Optional[str] = None,
    model_id: str = "sd1.5",
    strength: float = 0.75,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 30,
    seed: Optional[int] = None,
    use_gpu: bool = True,
    use_half_precision: bool = True,
) -> str:
    """
    Process an image for diffusion-based style transfer.
    
    Args:
        image_data (str): Base64-encoded image data
        style_type (str): Type of style guidance - "text" or "image"
        style_prompt (str): Text prompt describing the style (used if style_type is "text")
        style_image_data (str, optional): Base64-encoded style reference image (used if style_type is "image")
        model_id (str): ID of the diffusion model to use
        strength (float): Amount of noise to add (0.0 to 1.0)
        guidance_scale (float): How closely to follow the style guidance
        num_inference_steps (int): Number of denoising steps
        seed (int, optional): Random seed for reproducibility
        use_gpu (bool): Whether to use GPU for inference if available
        use_half_precision (bool): Whether to use half precision for faster inference
        
    Returns:
        str: Base64-encoded stylized image
    """
    try:
        # Load the content image
        content_image = load_image_from_base64(image_data)
        
        # Create and load the model
        model = DiffusionStyleTransferModel(
            model_id=model_id,
            use_gpu=use_gpu,
            use_half_precision=use_half_precision
        )
        
        # Apply style based on the style type
        if style_type == "text":
            # Text-guided style transfer
            result_image = model.apply_style_with_text(
                image=content_image,
                style_prompt=style_prompt,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                seed=seed
            )
        elif style_type == "image" and style_image_data:
            # Reference image style transfer
            style_image = load_image_from_base64(style_image_data)
            result_image = model.apply_style_with_image(
                content_image=content_image,
                style_image=style_image,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                seed=seed
            )
        else:
            raise ValueError("Invalid style_type or missing style_image_data for image-based style transfer")
        
        # Convert result to base64
        result_base64 = image_to_base64(result_image)
        
        return result_base64
    except Exception as e:
        logger.error(f"Error in diffusion style transfer: {e}")
        raise RuntimeError(f"Diffusion style transfer failed: {e}")

def get_available_models() -> List[Dict[str, Any]]:
    """
    Get a list of available diffusion models.
    
    Returns:
        List[Dict[str, Any]]: List of model dictionaries with details
    """
    return DiffusionStyleTransferModel.get_available_models()
