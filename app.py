import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import zipfile
from io import BytesIO
import colorsys
from fonts_config import load_font, FONTS

# ---------------- Functions ----------------
def apply_edits(image, saturation, brightness, contrast, effect, hue_shift, r_scale, g_scale, b_scale):
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

    if hue_shift != 0:
        image = adjust_hue(image, hue_shift)
    image = adjust_color_balance(image, r_scale, g_scale, b_scale)
    return image

def adjust_hue(image, shift):
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
    r, g, b = image.split()
    r = r.point(lambda i: min(255, i * r_scale))
    g = g.point(lambda i: min(255, i * g_scale))
    b = b.point(lambda i: min(255, i * b_scale))
    return Image.merge("RGB", (r, g, b))

def add_logo(image, logo_file, scale, pos):
    if not logo_file or pos is None:
        return image
    logo = Image.open(logo_file).convert("RGBA")
    logo_w = int(image.width * scale)
    logo_h = int(logo_w * logo.size[1] / logo.size[0])
    logo_resized = logo.resize((logo_w, logo_h))
    image.paste(logo_resized, pos, logo_resized)
    return image

def add_lower_third(image, text, font_name, font_size, color, position="bottom"):
    if not text:
        return image
    draw = ImageDraw.Draw(image)
    font = load_font(font_name, font_size)
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    except AttributeError:
        text_w, text_h = font.getsize(text)
    img_w, img_h = image.size
    margin = 20
    if position.lower() == "bottom":
        x, y = (img_w - text_w)//2, img_h - text_h - margin
    elif position.lower() == "top":
        x, y = (img_w - text_w)//2, margin
    elif position.lower() == "left":
        x, y = margin, img_h - text_h - margin
    elif position.lower() == "right":
        x, y = img_w - text_w - margin, img_h - text_h - margin
    else:
        x, y = (img_w - text_w)//2, img_h - text_h - margin
    draw.text((x,y), text, font=font, fill=color)
    return image

def process_batch(images, saturation, brightness, contrast, effect,
                  hue_shift, r_scale, g_scale, b_scale,
                  logo_file, logo_scale, logo_pos,
                  lower_text, font_name, font_size, font_color, lower_pos):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i, file in enumerate(images):
            image = Image.open(file).convert("RGB")
            image = apply_edits(image, saturation, brightness, contrast, effect,
                                hue_shift, r_scale, g_scale, b_scale)
            image = add_logo(image, logo_file, logo_scale, logo_pos)
            image = add_lower_third(image, lower_text, font_name, font_size, font_color, lower_pos)
            img_bytes = BytesIO()
            image.save(img_bytes, format="JPEG", quality=95)
            img_bytes.seek(0)
            zip_file.writestr(f"edited_{i+1}.jpg", img_bytes.read())
    zip_buffer.seek(0)
    return zip_buffer

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Smart Image Editor", layout="wide")
st.title("✨ Smart Image Editor")
st.markdown("Upload images, adjust settings, preview quickly, and export full quality.")

# Sidebar
with st.sidebar:
    st.header("📂 Uploads")
    uploaded_files = st.file_uploader("Upload JPG/PNG images", type=["jpg","jpeg","png"], accept_multiple_files=True)
    logo_file = st.file_uploader("Upload Logo (PNG)", type=["png"])

    st.header("🎨 Adjustments")
    saturation = st.slider("Saturation", 0.0, 3.0, 1.2, 0.1)
    brightness = st.slider("Brightness", 0.0, 3.0, 1.1, 0.1)
    contrast = st.slider("Contrast", 0.0, 3.0, 1.2, 0.1)
    hue_shift = st.slider("Hue Shift", -0.5, 0.5, 0.0, 0.01)
    r_scale = st.slider("Red Balance", 0.0, 3.0, 1.0, 0.1)
    g_scale = st.slider("Green Balance", 0.0, 3.0, 1.0, 0.1)
    b_scale = st.slider("Blue Balance", 0.0, 3.0, 1.0, 0.1)
    effect = st.selectbox("Effect", ["None","Black & White","Invert","Sepia"])

    st.header("🖼️ Logo")
    logo_scale = st.slider("Logo Size", 0.01, 0.3, 0.05, 0.01)
    logo_x = st.slider("Logo X Position", 0, 1000, 980)
    logo_y = st.slider("Logo Y Position", 0, 1000, 20)

    st.header("✍️ Lower Third")
    lower_text = st.text_input("Text (e.g., Church Name)")
    font_name = st.selectbox("Font", list(FONTS.keys()))
    font_size = st.slider("Font Size", 10, 100, 40)
    font_color = st.color_picker("Text Color", "#FFFFFF")
    lower_pos = st.selectbox("Position", ["Bottom","Top","Left","Right"])

# Preview
if uploaded_files:
    st.subheader("🔍 Preview of First Image")
    first_img = Image.open(uploaded_files[0]).convert("RGB")

    # Downscale for speed
    max_width = 800
    preview_img = first_img.copy()
    if preview_img.width > max_width:
        ratio = max_width / preview_img.width
        new_size = (int(preview_img.width*ratio), int(preview_img.height*ratio))
        preview_img = preview_img.resize(new_size, Image.LANCZOS)

    # Scale factor between preview and original
    scale_factor = first_img.width / preview_img.width

    # Adjust logo size for full-resolution export
    orig_logo_scale = logo_scale * scale_factor

    # Adjust logo position for full-resolution export
    orig_logo_x = int(logo_x * scale_factor)
    orig_logo_y = int(logo_y * scale_factor)
    orig_logo_pos = (orig_logo_x, orig_logo_y)

    # Adjust font size for export
    orig_font_size = int(font_size * scale_factor)

    # Adjust logo position and size
    orig_logo_x = int(logo_x * scale_factor)
    orig_logo_y = int(logo_y * scale_factor)
    orig_logo_pos = (orig_logo_x, orig_logo_y)

    # Adjust logo size
    logo_img = Image.open(logo_file).convert("RGBA")
    logo_w = int(logo_img.width * logo_scale * scale_factor)
    logo_h = int(logo_w * logo_img.height / logo_img.width)
    resized_logo = logo_img.resize((logo_w, logo_h))

    # Paste at scaled position
    first_img.paste(resized_logo, orig_logo_pos, resized_logo)

    # Adjust font size for original size
    orig_font_size = int(font_size * scale_factor)

    edited_preview = apply_edits(preview_img.copy(), saturation, brightness, contrast, effect,
                                 hue_shift, r_scale, g_scale, b_scale)
    edited_preview = add_lower_third(edited_preview, lower_text, font_name, font_size, font_color, lower_pos)
    edited_preview = add_logo(edited_preview, logo_file, logo_scale, (logo_x, logo_y))

    st.image(edited_preview, caption="Edited Preview", use_column_width=True)

# Batch Process
if uploaded_files and st.button("🚀 Process All Images"):
    zip_file = process_batch(
        uploaded_files, saturation, brightness, contrast, effect,
        hue_shift, r_scale, g_scale, b_scale,
        logo_file, orig_logo_scale, orig_logo_pos,
        lower_text, font_name, orig_font_size, font_color, lower_pos
    )
    st.download_button(
        label="⬇️ Download All Edited Images (ZIP)",
        data=zip_file,
        file_name="edited_images.zip",
        mime="application/zip"
    )
