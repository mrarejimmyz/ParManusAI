"""
Create a simple test image file to test Ollama vision directly.
"""

import numpy as np
from PIL import Image

# Create a simple 100x100 red square
image = Image.new("RGB", (100, 100), color="red")

# Add some text
from PIL import ImageDraw, ImageFont

draw = ImageDraw.Draw(image)

# Try to use default font
try:
    # Use a basic font
    draw.text((10, 40), "TEST", fill="white")
except:
    # If no font available, just draw a simple shape
    draw.rectangle([20, 20, 80, 80], fill="blue")

# Save the image
image.save("test_image.png")
print("✅ Created test_image.png")
