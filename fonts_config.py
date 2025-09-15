from PIL import ImageFont

# Map font names to their file paths
FONTS = {
    "DejaVu Sans": "fonts/DejaVuSans.ttf",
    "Roboto": "fonts/Roboto-Regular.ttf",
    "Times New Roman": "fonts/TimesNewRoman.ttf",
    "Courier New": "fonts/CourierNew.ttf",
}

def load_font(name, size):
    """Safely load a font from FONTS dict"""
    try:
        return ImageFont.truetype(FONTS[name], size)
    except Exception:
        return ImageFont.load_default()
