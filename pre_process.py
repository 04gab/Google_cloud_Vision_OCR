import os
from PIL import Image


#--- PRE PROCESS---
def create_pdf_output_folders(pdf_path):  
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    parent_folder = f"{base_name}_pages"
    os.makedirs(parent_folder, exist_ok=True)
    
    data_folder = os.path.join(parent_folder, "data")
    header_footer_folder = os.path.join(parent_folder, "header_footer")
    os.makedirs(data_folder, exist_ok=True)
    os.makedirs(header_footer_folder, exist_ok=True)
    return parent_folder, data_folder, header_footer_folder


def save_pdf_page_as_image(doc, page_number, pages_folder, dpi=400):
    page = doc[page_number]
    pix = page.get_pixmap(dpi=dpi)
    img_path = os.path.join(pages_folder, f"page_{page_number+1}.png")
    pix.save(img_path)
    # print(f"Saved page {page_number+1} as {img_path}")
    return img_path

def preprocess_image(image_path, scale_factor=2.0, output_path=None):
    img = Image.open(image_path)
    # Upscale the image
    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
    upscaled = img.resize(new_size, Image.LANCZOS)

    if output_path:
        upscaled.save(output_path)
        return output_path
    else:
        return upscaled

def page_orientation(image_path):

    img = Image.open(image_path)
    w, h = img.size
    # print(f"Image size: width={w}, height={h}")
    if w > h: # Landscape
        # print(f"{image_path}: Already landscape, no rotation needed. ")
        pass
        
    else:
        img = img.rotate(90, expand=True)
        w, h = img.size
        img.save(image_path)
        # print(f"{image_path}: Detected portrait, rotating 90 degrees for analysis.")
