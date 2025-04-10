# User Guide

This guide provides instructions for installing and using the GIMP AI Integration Addon.

## Installation

### Prerequisites

- GIMP 2.10 or later
- Python 3.8 or later
- Required Python packages (see requirements.txt files)

### Setup Steps

1. **Clone or download the repository**
   ```
   git clone https://github.com/yourusername/gimp-ai-integration.git
   ```

2. **Install backend dependencies**
   ```
   cd gimp-ai-integration
   pip install -r backend/requirements.txt
   ```

3. **Install frontend dependencies**
   ```
   pip install -r frontend/requirements.txt
   ```

4. **Copy plugin to GIMP's plugin directory**

   - **Linux**: Copy or symlink `frontend/gimp_plugin` to `~/.config/GIMP/2.10/plug-ins/`
   - **Windows**: Copy `frontend/gimp_plugin` to `C:\Users\YOUR_USERNAME\AppData\Roaming\GIMP\2.10\plug-ins\`
   - **macOS**: Copy `frontend/gimp_plugin` to `~/Library/Application Support/GIMP/2.10/plug-ins/`

5. **Start the MCP server**
   ```
   python backend/server/app.py
   ```

6. **Launch GIMP**
   
   The AI tools should be available under "Filters > AI Tools"

## Using AI Features

### Background Removal

1. Open an image in GIMP
2. Select "Filters > AI Tools > Remove Background"
3. In the dialog that appears:
   - Adjust the **Threshold slider** (lower values remove more of the background, higher values preserve more)
   - Toggle **Use GPU** option based on your system capabilities
4. Click "OK" to process the image
5. Wait for processing to complete (a progress bar will show the status)
6. The result will appear as a new layer with the background removed and transparency
7. You can further refine the result using GIMP's standard tools (eraser, layer mask, etc.)

**Tip:** For best results, use images where the subject is clearly distinct from the background. The feature works best with portraits, product photos, and other images with clear foreground subjects.

### Inpainting

1. Open an image in GIMP
2. Use any selection tool (Rectangle, Free Select, Fuzzy Select, etc.) to select the area you want to inpaint
3. Select "Filters > AI Tools > Inpainting"
4. In the dialog that appears:
   - Check "Expand mask slightly" to help with blending at the edges (recommended)
   - Toggle "Use GPU" based on your system capabilities
   - Choose whether to create a new layer or modify the existing one
5. Click "OK" to process
6. Wait for processing to complete (a progress bar will show the status)
7. The selected area will be filled with AI-generated content that matches the surroundings

**Tip:** Inpainting works best when removing unwanted objects, filling in missing areas, or removing text from images. For complex structures, you may need to make multiple smaller selections and inpaint them one at a time.

### Style Transfer

1. Open an image in GIMP
2. Select "Filters > AI Tools > Style Transfer"
3. In the dialog that appears:
   - Choose a style from the dropdown menu (Starry Night, Mosaic, etc.)
   - Adjust the strength slider (higher values give stronger stylization)
   - Choose whether to create a new layer
   - Toggle "Use GPU" based on your system capabilities
4. Click "OK" to process
5. Wait for processing to complete (a progress bar will show the status)
6. The stylized image will appear either on a new layer or replacing the current one

**Tip:** Style transfer works best on photographs with clear subjects and not too many fine details. Try different styles and strength settings to find the look you want. Lower strength settings blend the style with the original image for a more subtle effect.

### Image Upscaling

1. Open an image in GIMP
2. Select "Filters > AI Tools > Upscale Image"
3. In the dialog that appears:
   - Choose a **Scale Factor** (2x, 4x, or 8x) - note that larger factors require more processing time and memory
   - Adjust the **Denoise Level** slider to reduce noise or artifacts (0.0 = off, 1.0 = maximum)
   - Toggle **Apply sharpening** to enhance details after upscaling
   - Choose whether to create a new image or add to the current image
   - Toggle **Use GPU** based on your system capabilities
4. Click "OK" to process
5. Wait for processing to complete (a progress bar will show the status)
6. The upscaled image will appear either as a new image or as a new layer in the current image

**Tip:** For large images, use a smaller scale factor (2x) to avoid memory issues. For small images that need significant enlargement, you can try 4x or 8x. The denoise option helps reduce artifacts in the output, while sharpening can help restore some detail clarity.

## Troubleshooting

- **Plugin doesn't appear in GIMP**: Make sure the plugin is in the correct directory and has executable permissions
- **Connection error**: Ensure the MCP server is running before using AI features
- **Slow processing**: AI operations may take time depending on your hardware and the complexity of the task
- **Memory errors**: Try working with smaller images or regions for complex AI operations

For more help, please open an issue on the GitHub repository.
