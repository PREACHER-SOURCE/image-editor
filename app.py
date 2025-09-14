import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import os
import zipfile
from io import BytesIO

# ------------------ Functions ------------------
def apply_edits(image, saturation, brightness, contrast, effect):
    """Apply enhancements and effects"""
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)

    if effect == "Black & White":
        image = image.convert("L").convert("RGB")
    elif effect == "Invert":
        image = ImageOps.invert(image)
    elif effect == "Sepia":
        sepia = []
        for i in range(255):
            sepia.extend((int(i * 240 / 255), int(i * 200 / 255), int(i * 145 / 255)))
        image = image.convert("L")
        image.putpalette(sepia)
        image = image.convert("RGB")

    return image

def add_logo(image, logo_file):
    """Overlay logo on top-right corner"""
    if not logo_file:
        return image

    logo = Image.open(logo_file).convert("RGBA")
    img_w, img_h = image.size
    logo_w = img_w // 20
    logo_h = int(logo_w * logo.size[1] / logo.size[0])
    logo_resized = logo.resize((logo_w, logo_h))

    position = (img_w - logo_w - 10, 10)
    image.paste(logo_resized, position, logo_resized)
    return image

def process_batch(images, saturation, brightness, contrast, effect, logo_file):
    """Process multiple images and return a ZIP file"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, file in enumerate(images):
            image = Image.open(file).convert("RGB")
            image = apply_edits(image, saturation, brightness, contrast, effect)
            image = add_logo(image, logo_file)

            # Save each image in memory
            img_bytes = BytesIO()
            image.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            zip_file.writestr(f"edited_{i+1}.jpg", img_bytes.read())

    zip_buffer.seek(0)
    return zip_buffer

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Smart Image Editor", layout="centered")
st.title("✨ Smart Image Editor")

st.markdown("Upload images, adjust settings, preview, and download!")

# Uploads
uploaded_files = st.file_uploader("📂 Upload one or more JPG/PNG images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
logo_file = st.file_uploader("🖼️ Upload your Logo (PNG)", type=["png"])

# Sliders
saturation = st.slider("🎨 Saturation", 0.0, 3.0, 1.2, 0.1)
brightness = st.slider("💡 Brightness", 0.0, 3.0, 1.1, 0.1)
contrast = st.slider("⚡ Contrast", 0.0, 3.0, 1.2, 0.1)

# Effect
effect = st.selectbox("✨ Effect", ["None", "Black & White", "Invert", "Sepia"])

# Preview
if uploaded_files:
    st.subheader("🔍 Preview of First Image")
    first_img = Image.open(uploaded_files[0]).convert("RGB")
    preview = apply_edits(first_img, saturation, brightness, contrast, effect)
    preview = add_logo(preview, logo_file)
    st.image(preview, caption="Preview", use_column_width=True)

# Batch process
if uploaded_files:
    if st.button("🚀 Process All Images"):
        zip_file = process_batch(uploaded_files, saturation, brightness, contrast, effect, logo_file)
        st.download_button(
            label="⬇️ Download All Edited Images (ZIP)",
            data=zip_file,
            file_name="edited_images.zip",
            mime="application/zip"
        )
