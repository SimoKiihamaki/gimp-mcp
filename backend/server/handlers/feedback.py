"""
Feedback handler for the MCP server.

This module handles feedback submissions from the GIMP plugin.
"""
import os
import json
import logging
import datetime
import uuid
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Default directory for storing feedback
DEFAULT_FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "feedback")

async def handle_submit_feedback(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a feedback submission.
    
    Args:
        params: Parameters for the request, including:
            - feedback (dict): Feedback data
            
    Returns:
        dict: Response with status and message
    """
    try:
        # Extract parameters
        feedback = params.get("feedback")
        if not feedback:
            raise ValueError("Missing required parameter: feedback")
        
        # Generate a unique ID for the feedback
        feedback_id = str(uuid.uuid4())
        
        # Add additional metadata
        feedback["id"] = feedback_id
        feedback["received_timestamp"] = datetime.datetime.now().isoformat()
        
        # Check if there's a subject, if not, generate one
        if not feedback.get("subject"):
            feedback_type = feedback.get("type", "General Feedback")
            category = feedback.get("category", "General")
            feedback["subject"] = f"{feedback_type} - {category}"
        
        # Store the feedback
        store_feedback(feedback)
        
        # Return success
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_id
        }
    except Exception as e:
        logger.exception(f"Error handling feedback submission: {e}")
        raise RuntimeError(f"Failed to submit feedback: {str(e)}")

def store_feedback(feedback: Dict[str, Any]) -> None:
    """
    Store feedback data.
    
    Args:
        feedback (dict): Feedback data to store
    """
    try:
        # Get the feedback directory
        feedback_dir = os.environ.get("MCP_FEEDBACK_DIR", DEFAULT_FEEDBACK_DIR)
        
        # Create the directory if it doesn't exist
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Organize feedback by type and category
        feedback_type = feedback.get("type", "General Feedback").replace(" ", "_").lower()
        category = feedback.get("category", "General").replace(" ", "_").lower()
        
        # Create subdirectories for type and category
        type_dir = os.path.join(feedback_dir, feedback_type)
        category_dir = os.path.join(type_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Generate a filename based on the ID
        feedback_id = feedback.get("id", str(uuid.uuid4()))
        filename = f"{feedback_id}.json"
        filepath = os.path.join(category_dir, filename)
        
        # Save the feedback to the file
        with open(filepath, "w") as f:
            json.dump(feedback, f, indent=2)
        
        logger.info(f"Feedback stored: {filepath}")
        
        # Create an index file of all feedback
        update_feedback_index(feedback, feedback_dir)
        
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise RuntimeError(f"Failed to store feedback: {str(e)}")

def update_feedback_index(feedback: Dict[str, Any], feedback_dir: str) -> None:
    """
    Update the feedback index file.
    
    Args:
        feedback (dict): Feedback data
        feedback_dir (str): Feedback directory
    """
    try:
        # Create an index file path
        index_file = os.path.join(feedback_dir, "index.json")
        
        # Load existing index if it exists
        index = {}
        if os.path.exists(index_file):
            with open(index_file, "r") as f:
                index = json.load(f)
        
        # Extract data for the index
        feedback_id = feedback.get("id")
        feedback_type = feedback.get("type", "General Feedback")
        category = feedback.get("category", "General")
        subject = feedback.get("subject", "No subject")
        timestamp = feedback.get("received_timestamp")
        name = feedback.get("name", "Anonymous")
        
        # Add to the index
        index[feedback_id] = {
            "type": feedback_type,
            "category": category,
            "subject": subject,
            "timestamp": timestamp,
            "name": name
        }
        
        # Save the index
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)
        
        logger.info(f"Feedback index updated: {index_file}")
        
    except Exception as e:
        logger.error(f"Error updating feedback index: {e}")
        # Don't raise an exception here - this is just a helper function

async def handle_get_feedback(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a request to get feedback.
    
    Args:
        params: Parameters for the request, including:
            - feedback_id (str, optional): ID of the specific feedback to retrieve
            - type (str, optional): Filter by feedback type
            - category (str, optional): Filter by category
            - limit (int, optional): Maximum number of items to return
            - offset (int, optional): Offset for pagination
            
    Returns:
        dict: Response with feedback data
    """
    try:
        # Get the feedback directory
        feedback_dir = os.environ.get("MCP_FEEDBACK_DIR", DEFAULT_FEEDBACK_DIR)
        
        # Check if the directory exists
        if not os.path.exists(feedback_dir):
            return {
                "status": "success",
                "feedback": [],
                "total": 0
            }
        
        # Get parameters
        feedback_id = params.get("feedback_id")
        feedback_type = params.get("type")
        category = params.get("category")
        limit = int(params.get("limit", 100))
        offset = int(params.get("offset", 0))
        
        # Check if a specific feedback ID is requested
        if feedback_id:
            # Find the feedback file
            feedback_file = None
            for root, dirs, files in os.walk(feedback_dir):
                if f"{feedback_id}.json" in files:
                    feedback_file = os.path.join(root, f"{feedback_id}.json")
                    break
            
            if feedback_file:
                with open(feedback_file, "r") as f:
                    feedback_data = json.load(f)
                
                return {
                    "status": "success",
                    "feedback": feedback_data
                }
            else:
                raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        # Load the index
        index_file = os.path.join(feedback_dir, "index.json")
        if not os.path.exists(index_file):
            return {
                "status": "success",
                "feedback": [],
                "total": 0
            }
        
        with open(index_file, "r") as f:
            index = json.load(f)
        
        # Filter the index
        filtered_index = {}
        for id, data in index.items():
            if feedback_type and data.get("type") != feedback_type:
                continue
            if category and data.get("category") != category:
                continue
            filtered_index[id] = data
        
        # Sort by timestamp (newest first)
        sorted_ids = sorted(
            filtered_index.keys(),
            key=lambda id: filtered_index[id].get("timestamp", ""),
            reverse=True
        )
        
        # Apply pagination
        paginated_ids = sorted_ids[offset:offset + limit]
        
        # Load the feedback data for the paginated IDs
        feedback_data = []
        for id in paginated_ids:
            # Find the feedback file
            feedback_file = None
            for root, dirs, files in os.walk(feedback_dir):
                if f"{id}.json" in files:
                    feedback_file = os.path.join(root, f"{id}.json")
                    break
            
            if feedback_file:
                with open(feedback_file, "r") as f:
                    feedback_data.append(json.load(f))
        
        # Return the feedback data
        return {
            "status": "success",
            "feedback": feedback_data,
            "total": len(filtered_index),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.exception(f"Error getting feedback: {e}")
        raise RuntimeError(f"Failed to get feedback: {str(e)}")
