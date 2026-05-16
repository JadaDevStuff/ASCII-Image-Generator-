from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
import tkinter as tk
from tkinter import scrolledtext
import tkinter.font as tkfont
import numpy as np
import cv2
import os


# ── Settings ──────────────────────────────────────────────────────────────────
font_size = 4
ascii_chars = "   .,:;+*=#%@"
threshold = 0
detail = 180
input_path = "demo.jpg"
output_path = "democolored2x.png"


depth = True
colored = True


grid_width = detail
grid_height = detail
char_ratio = 0.53


root = tk.Tk()


# ── Image loading ─────────────────────────────────────────────────────────────
img = Image.open(input_path).convert("L")
img_cv = np.array(img)


clahe = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8))
img_clahe = clahe.apply(img_cv).astype(np.uint8)
img_clahe = cv2.medianBlur(img_clahe, 3)
img = Image.fromarray(img_clahe)
img = ImageEnhance.Contrast(img).enhance(2.34)
img = ImageEnhance.Brightness(img).enhance(1.5)


gamma = 0.8
img_np = np.power(np.array(img) / 255.0, gamma)
img = Image.fromarray(np.uint8(img_np * 255))


color_img = Image.open(input_path).convert("RGB")
color_img = ImageEnhance.Color(color_img).enhance(1.2)




# ── Core functions ────────────────────────────────────────────────────────────
def sort_chars_by_density(chars, font):
    densities = []
    for char in chars:
        bbox = font.getbbox(char)
        w = max(1, bbox[2] - bbox[0])
        h = max(1, bbox[3] - bbox[1])
        tmp = Image.new("L", (w, h), 0)
        ImageDraw.Draw(tmp).text((-bbox[0], -bbox[1]), char, fill=255, font=font)
        densities.append((np.array(tmp).mean(), char))
    densities.sort(key=lambda x: x[0])
    return "".join(c for _, c in densities)




def calculate_parameters():
    global ascii_chars, grid_width, grid_height, char_ratio, font_size, step_w, step_h, scale
    scale = 2
    grid_width = detail
    font_size = img.width * scale // grid_width
    font = ImageFont.truetype("CourierPrime-Regular.ttf", font_size)
    ascii_chars = sort_chars_by_density(ascii_chars, font)


    bbox = font.getbbox("A")
    step_w = int(font.getlength("A"))
    step_h = bbox[3] - bbox[1]
    char_ratio = step_w / step_h
    grid_height = int(grid_width * (img.height / img.width) * char_ratio)




def image_to_ascii(image=img):
    local_colored_chars = []
    rows = []


    image = image.resize((grid_width, grid_height), Image.Resampling.LANCZOS)
    resized_color = color_img.resize((grid_width, grid_height), Image.Resampling.LANCZOS)


    pixels = list(image.getdata())
    color_pixels = list(resized_color.getdata())
    brightness_map = []


    for h in range(grid_height):
        row = []
        row_chars = []
        for w in range(grid_width):
            index = h * grid_width + w
            brightness = max(0, min(255, pixels[index]))
            brightness_map.append(brightness)
            color = color_pixels[index]
            char = ascii_chars[brightness * (len(ascii_chars) - 1) // 255]
            if brightness > threshold:
                row.append((char, color))
            else:
                row.append((" ", (0, 0, 0)))
            row_chars.append(char)
        local_colored_chars.append(row)
        rows.append("".join(row_chars))


    return "\n".join(rows), local_colored_chars, brightness_map




def show_ascii(ascii_str):
    MAX_PREVIEW_WIDTH = 1200
    MAX_PREVIEW_HEIGHT = 800


    temp_font = tkfont.Font(family="Courier New", size=font_size)
    char_width = temp_font.measure("A")
    char_height = temp_font.metrics("linespace")


    render_width = grid_width * char_width
    render_height = grid_height * char_height


    preview_scale = min(MAX_PREVIEW_WIDTH / render_width, MAX_PREVIEW_HEIGHT / render_height, 1.0)
    preview_font_size = max(2, int(font_size * preview_scale))
    font = tkfont.Font(family="Courier New", size=preview_font_size)


    text = scrolledtext.ScrolledText(
        root,
        bg="black",
        fg="white",
        font=font,
        wrap=tk.NONE,
        borderwidth=0,
        highlightthickness=0,
    )
    text.pack(fill=tk.BOTH, expand=True)
    text.insert(tk.END, ascii_str)
    text.config(state=tk.DISABLED)


    root.update_idletasks()
    root.geometry(f"{render_width}x{render_height}")
    root.mainloop()




def ascii_to_png(colors, output_path="output.png", brightness=[]):
    global scale, font_size, step_w, step_h
    try:
        font = ImageFont.truetype("CourierPrime-Regular.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()


    canvas = Image.new(
        "RGB",
        (step_w * grid_width, step_h * grid_height),
        (20, 25, 18) if colored else (0, 0, 0),
    )
    draw = ImageDraw.Draw(canvas)


    for h in range(grid_height):
        for w in range(grid_width):
            index = h * grid_width + w
            char, color = colors[h][w]
            if not colored:
                v = brightness[index] if depth else 255
                color = (v, v, v)
            draw.text((w * step_w, h * step_h), char, fill=color, font=font)
    canvas.save(output_path)




# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    calculate_parameters()
    result, colors, b = image_to_ascii(img)
    ascii_to_png(colors, output_path, b)
    show_ascii(result)