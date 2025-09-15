import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont
from streamlit_drawable_canvas import st_canvas
import zipfile
from io import BytesIO
import colorsys

# ------------------ Functions ------------------
def apply_edits(image, saturation, brightness, contrast, effect, hue_shift, r_scale, g_scale, b_scale):
    """Apply enhancements and effects"""
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Contrast(image).enhance(contrast)

    # Effect filters
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

    # Hue shift
    if hue_shift != 0:
        image = adjust_hue(image, hue_shift)

    # Color balance
    image = adjust_color_balance(image, r_scale, g_scale, b_scale)

    return image

def adjust_hue(image, shift):
    """Adjust hue by shift (-0.5 to 0.5)"""
    img = image.convert("RGB")
    pixels = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b = pixels[x, y]
            h, l, s = colorsys.rgb_to_hls(r/255., g/255., b/255.)
            h = (h + shift) % 1.0
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            pixels[x, y] = (int(r*255), int(g*255), int(b*255))
    return img

def adjust_color_balance(image, r_scale, g_scale, b_scale):
    """Adjust color balance for R, G, B channels"""
    r, g, b = image.split()
    r = r.point(lambda i: min(255, i * r_scale))
    g = g.point(lambda i: min(255, i * g_scale))
    b = b.point(lambda i: min(255, i * b_scale))
    return Image.merge("RGB", (r, g, b))

def add_logo(image, logo_file, scale, pos):
    """Overlay logo at given position"""
    if not logo_file or pos is None:
        return image
    logo = Image.open(logo_file).convert("RGBA")
    logo_w = int(image.width * scale)
    logo_h = int(logo_w * logo.size[1] / logo.size[0])
    logo_resized = logo.resize((logo_w, logo_h))
    image.paste(logo_resized, pos, logo_resized)
    return image

def add_lower_third(image, text, font_size, color, position):
    """Add lower third text overlay"""
    if not text:
        return image
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text_w, text_h = draw.textsize(text, font=font)
    img_w, img_h = image.size

    if position == "Bottom":
        xy = (img_w//2 - text_w//2, img_h - text_h - 20)
    elif position == "Top":
        xy = (img_w//2 - text_w//2, 20)
    elif position == "Left":
        xy = (20, img_h - text_h - 20)
    else:  # Right
        xy = (img_w - text_w - 20, img_h - text_h - 20)

    draw.text(xy, text, font=font, fill=color)
    return image

def process_batch(images, saturation, brightness, contrast, effect,
                  hue_shift, r_scale, g_scale, b_scale,
                  logo_file, logo_scale, logo_pos,
                  lower_text, font_size, font_color, lower_pos):
    """Process multiple images and return a ZIP file"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, file in enumerate(images):
            image = Image.open(file).convert("RGB")
            image = apply_edits(image, saturation, brightness, contrast, effect,
                                hue_shift, r_scale, g_scale, b_scale)
            image = add_logo(image, logo_file, logo_scale, logo_pos)
            image = add_lower_third(image, lower_text, font_size, font_color, lower_pos)

            # Save each image in memory
            img_bytes = BytesIO()
            image.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            zip_file.writestr(f"edited_{i+1}.jpg", img_bytes.read())

    zip_buffer.seek(0)
    return zip_buffer

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Smart Image Editor", layout="wide")
st.title("✨ Smart Image Editor")
st.markdown("Upload images, adjust settings, preview, and download!")

# File uploads
with st.sidebar:
    st.header("📂 Uploads")
    uploaded_files = st.file_uploader("Upload JPG/PNG images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    logo_file = st.file_uploader("Upload Logo (PNG)", type=["png"])

    st.header("🎨 Adjustments")
    saturation = st.slider("Saturation", 0.0, 3.0, 1.2, 0.1)
    brightness = st.slider("Brightness", 0.0, 3.0, 1.1, 0.1)
    contrast = st.slider("Contrast", 0.0, 3.0, 1.2, 0.1)

    hue_shift = st.slider("Hue Shift", -0.5, 0.5, 0.0, 0.01)
    r_scale = st.slider("Red Balance", 0.0, 3.0, 1.0, 0.1)
    g_scale = st.slider("Green Balance", 0.0, 3.0, 1.0, 0.1)
    b_scale = st.slider("Blue Balance", 0.0, 3.0, 1.0, 0.1)

    effect = st.selectbox("Effect", ["None", "Black & White", "Invert", "Sepia"])

    st.header("🖼️ Logo")
    logo_scale = st.slider("Logo Size (relative)", 0.01, 0.3, 0.05, 0.01)

    st.header("✍️ Lower Third")
    lower_text = st.text_input("Text (e.g., Church Name)")
    font_size = st.slider("Font Size", 10, 100, 40)
    font_color = st.color_picker("Text Color", "#FFFFFF")
    lower_pos = st.selectbox("Position", ["Bottom", "Top", "Left", "Right"])

# Preview and drag-drop logo
logo_position = None
if uploaded_files:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("🔍 Preview of First Image")
        first_img = Image.open(uploaded_files[0]).convert("RGB")

        # Apply edits (without logo yet)
        edited_preview = apply_edits(first_img.copy(), saturation, brightness, contrast, effect,
                                     hue_shift, r_scale, g_scale, b_scale)
        edited_preview = add_lower_third(edited_preview, lower_text, font_size, font_color, lower_pos)

        if logo_file:
            st.write("👉 Drag your logo into position")
            canvas_result = st_canvas(
                background_image=edited_preview,
                update_streamlit=True,
                width=edited_preview.width,
                height=edited_preview.height,
                drawing_mode="transform",  # allows drag + resize
                key="canvas"
            )

            if canvas_result.json_data is not None:
                objects = canvas_result.json_data.get("objects", [])
                if objects:
                    obj = objects[-1]
                    logo_x, logo_y = int(obj["left"]), int(obj["top"])
                    logo_w = int(edited_preview.width * logo_scale)
                    logo_h = int(logo_w * Image.open(logo_file).size[1] / Image.open(logo_file).size[0])
                    logo_position = (logo_x, logo_y)
                    edited_preview = add_logo(edited_preview, logo_file, logo_scale, logo_position)

        show_original = st.checkbox("👁 Show Original")
        if show_original:
            st.image(first_img, caption="Original", use_column_width=True)
        else:
            st.image(edited_preview, caption="Edited Preview", use_column_width=True)

    with col2:
        st.info("✅ Adjust edits on the left sidebar.\n✅ Drag logo directly on the preview.\n✅ Apply to all with 'Process All Images'.")

# Batch process
if uploaded_files and st.button("🚀 Process All Images"):
    zip_file = process_batch(uploaded_files, saturation, brightness, contrast, effect,
                             hue_shift, r_scale, g_scale, b_scale,
                             logo_file, logo_scale, logo_position,
                             lower_text, font_size, font_color, lower_pos)
    st.download_button(
        label="⬇️ Download All Edited Images (ZIP)",
        data=zip_file,
        file_name="edited_images.zip",
        mime="application/zip"
    )
