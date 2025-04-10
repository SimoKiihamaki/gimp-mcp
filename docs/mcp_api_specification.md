# GIMP AI Integration MCP API Specification

This document provides a comprehensive reference for the Model Context Protocol (MCP) API that enables AI systems like Claude Desktop to directly control GIMP for image creation and editing.

## Overview

The GIMP AI Integration MCP API allows AI systems to:

1. Create new images
2. Edit existing images 
3. Apply filters and effects
4. Analyze image content
5. Execute sequences of commands

All communication is done via JSON-RPC 2.0 over HTTP. The default endpoint is `http://localhost:8000/jsonrpc`.

## Authentication

Authentication is optional but recommended when exposing the API over a network. An API key can be provided in the `X-API-Key` header.

## Common Response Structure

All responses follow the JSON-RPC 2.0 specification and include:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success" | "error",
    "message": "Description of the result or error",
    ...additional fields specific to the method
  },
  "id": 1 // The request ID
}
```

## Session-Based Operations

Many operations can be performed within a session, which maintains state between multiple API calls. Sessions are identified by a unique `session_id` that is generated when starting a new operation.

## API Methods

### 1. MCP Operation

Execute a single MCP operation on an image.

**Method:** `mcp_operation`

**Parameters:**
- `operation` (string, required): The operation to perform
- `session_id` (string, optional): Session ID for persistent state
- `image_data` (string, optional): Base64-encoded image data for new sessions
- Additional parameters specific to the operation

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "mcp_operation",
  "params": {
    "operation": "create_new_image",
    "width": 800,
    "height": 600,
    "color": [255, 255, 255, 255]
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "Created new 800x600 image",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "image_dimensions": {
      "width": 800,
      "height": 600
    }
  },
  "id": 1
}
```

### 2. Execute GIMP Commands

Execute a sequence of GIMP commands in a single request.

**Method:** `execute_gimp_commands`

**Parameters:**
- `commands` (array, required): List of commands to execute
- `image_data` (string, optional): Base64-encoded image data
- `session_id` (string, optional): Session ID for persistent state
- `include_image_data` (boolean, optional): Whether to include the resulting image data

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "execute_gimp_commands",
  "params": {
    "commands": [
      {
        "operation": "create_new_image",
        "params": {
          "width": 800,
          "height": 600,
          "color": [255, 255, 255, 255]
        }
      },
      {
        "operation": "apply_blur",
        "params": {
          "radius": 5.0
        }
      }
    ],
    "include_image_data": true
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "results": [
      {
        "success": true,
        "message": "Created new 800x600 image"
      },
      {
        "success": true,
        "message": "Applied Gaussian blur with radius 5.0"
      }
    ],
    "image_dimensions": {
      "width": 800,
      "height": 600
    },
    "image_data": "base64_encoded_image_data..."
  },
  "id": 1
}
```

### 3. Close MCP Session

Close an MCP image session and clean up resources.

**Method:** `mcp_close_session`

**Parameters:**
- `session_id` (string, required): Session ID to close

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "mcp_close_session",
  "params": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "Session 550e8400-e29b-41d4-a716-446655440000 closed successfully"
  },
  "id": 1
}
```

### 4. Image Analysis

Analyze the content of an image.

**Method:** `image_analysis`

**Parameters:**
- `image_state` (object, required): State of the GIMP image or base64-encoded image data
- `analysis_type` (string, optional): Type of analysis to perform (basic, detailed)

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "image_analysis",
  "params": {
    "image_data": "base64_encoded_image_data...",
    "analysis_type": "detailed"
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "analysis": {
      "dimensions": {
        "width": 800,
        "height": 600,
        "aspect_ratio": 1.33
      },
      "color_analysis": {
        "average_color": {
          "rgb": [120, 120, 120],
          "hex": "#787878"
        },
        "brightness": 120,
        "contrast": 30,
        "is_grayscale": false,
        "dominant_colors": ["Gray", "White"]
      }
    },
    "status": "success"
  },
  "id": 1
}
```

### 5. AI Assistant

Get AI assistance for image editing.

**Method:** `ai_assistant`

**Parameters:**
- `message` (string, required): User message
- `conversation_history` (array, optional): Previous conversation
- `image_state` (object, optional): State of the GIMP image
- `analysis_results` (object, optional): Results of image analysis

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ai_assistant",
  "params": {
    "message": "Make this image brighter",
    "image_state": {
      "metadata": {
        "width": 800,
        "height": 600
      }
    }
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": "I can increase the brightness of your image. Would you like me to do that?",
    "suggestion": {
      "type": "adjustment",
      "operation": "adjust_brightness_contrast",
      "parameters": {
        "brightness": 30,
        "contrast": 0
      }
    },
    "status": "success"
  },
  "id": 1
}
```

## Supported Operations

Here's a list of operations supported by the `mcp_operation` method:

### Image Creation and Management

- `create_new_image`: Create a new blank image
  - Parameters: `width`, `height`, `color`

- `open_image`: Open an existing image
  - Parameters: `image_data` (base64 encoded)

- `save_image`: Save the current image
  - Parameters: `format` (PNG, JPEG, etc.), `quality`

### Image Transformations

- `resize_image`: Resize the image
  - Parameters: `width`, `height`

- `crop_image`: Crop the image
  - Parameters: `x`, `y`, `width`, `height`

- `rotate_image`: Rotate the image
  - Parameters: `angle`, `expand`

### Layer Operations

- `create_layer`: Create a new layer
  - Parameters: `name`, `width`, `height`, `type_id`, `opacity`, `mode`, `position`

- `duplicate_layer`: Duplicate a layer
  - Parameters: `layer_id`

- `merge_layers`: Merge visible layers
  - Parameters: `merge_type`

### Selections

- `create_rectangle_selection`: Create a rectangular selection
  - Parameters: `x`, `y`, `width`, `height`, `operation`, `feather`

- `create_ellipse_selection`: Create an elliptical selection
  - Parameters: `x`, `y`, `width`, `height`, `operation`, `feather`

- `select_none`: Clear the current selection
  - Parameters: none

### Filters and Adjustments

- `apply_blur`: Apply a blur filter
  - Parameters: `blur_type`, `radius`

- `apply_sharpen`: Apply a sharpen filter
  - Parameters: `amount`

- `adjust_brightness_contrast`: Adjust brightness and contrast
  - Parameters: `brightness`, `contrast`

- `adjust_hue_saturation`: Adjust hue, saturation, and lightness
  - Parameters: `hue`, `saturation`, `lightness`

### Drawing Operations

- `fill_selection`: Fill the current selection
  - Parameters: `fill_type`

- `draw_brush_stroke`: Draw a brush stroke
  - Parameters: `stroke_points`, `brush_name`, `brush_size`, `color`

### Text Operations

- `add_text_layer`: Add a text layer
  - Parameters: `text`, `font`, `size`, `color`, `x`, `y`

## AI-Driven Workflows

Claude Desktop can use this API to create sophisticated image editing workflows:

1. Create a new image or open an existing one
2. Analyze the image content to understand what's in it
3. Apply a series of edits based on user instructions
4. Save the final result

Here's an example workflow:

1. Create a new image: `create_new_image`
2. Add a text layer: `add_text_layer`
3. Apply a blur filter: `apply_blur`
4. Save the image: `save_image`

## Error Handling

All operations return a `success` flag and a `message` that describes the result or error. In case of an error, the `success` flag will be `false` and the `message` will contain information about what went wrong.

## Best Practices

1. Always close sessions when you're done with them to free up resources
2. Use the `execute_gimp_commands` method for complex operations to reduce network overhead
3. Set `include_image_data` to `false` when you don't need the image data to improve performance
4. Before applying operations, analyze the image to understand its content
5. Use short-lived sessions for simple operations and long-lived sessions for complex editing sessions
