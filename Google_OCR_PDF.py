import fitz  
import os
from google.cloud import vision


import pre_process
import main_process
import post_process
import CSV_header_footer_saving

pdf_path = r"your\pdf\path\___.pdf"  # Replace with your PDF file path
key_path = r"your\key\path\___.json"  # Replace with your Google Cloud Vision API key path


if __name__ == "__main__":
    parent_folder, data_folder, header_footer_folder = pre_process.create_pdf_output_folders(pdf_path)
    pages_folder = os.path.join(parent_folder, "pages")
    os.makedirs(pages_folder, exist_ok=True)  
    doc = fitz.open(pdf_path)


    # pages_to_process = [8]  # for testing certain pages
    pages_to_process = list(range(1, len(doc) + 1))
    

    # Pre Process
    for i in range(len(doc)):
        if (i + 1) in pages_to_process:
            img_path = pre_process.save_pdf_page_as_image(doc, i, pages_folder, dpi=400)
            # Overwrite with upscaled version
            pre_process.preprocess_image(img_path, scale_factor=2.0, output_path=img_path)
            pre_process.page_orientation(img_path)


    # Main Processing
    for i in range(len(doc)):

        if (i + 1) in pages_to_process:
            img_path = os.path.join(pages_folder, f"page_{i+1}.png")
            # main_process.ocr_and_draw_boxes(img_path, key_path)  # For testing bounding box of text detected
            client = vision.ImageAnnotatorClient.from_service_account_json(key_path)
            with open(img_path, 'rb') as img_file:
                content = img_file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            annotation = response.full_text_annotation
            ocr_results = []
            if annotation and annotation.pages:
                for page in annotation.pages:
                    for block in page.blocks:
                        for para in block.paragraphs:
                            for word in para.words:
                                word_text = ''.join([s.text for s in word.symbols])
                                vertices = word.bounding_box.vertices
                                if len(vertices) == 4:
                                    x_min = min(v.x for v in vertices)
                                    x_max = max(v.x for v in vertices)
                                    y_min = min(v.y for v in vertices)
                                    y_max = max(v.y for v in vertices)
                                    ocr_results.append({
                                        'text': word_text,
                                        'x_min': x_min,
                                        'x_max': x_max,
                                        'y_min': y_min,
                                        'y_max': y_max
                                    })

            raw_rows, header_footer_rows = main_process.extract_raw_ocr_rows(ocr_results)
            post_process.clean_and_save_ocr_rows(
                raw_rows,
                data_folder=data_folder,
                pdf_name=os.path.splitext(os.path.basename(pdf_path))[0],
                page_number=i+1
            )
            CSV_header_footer_saving.header_footer_saving(
                header_footer_rows,
                data_folder=header_footer_folder,
                pdf_name=os.path.splitext(os.path.basename(pdf_path))[0],
                page_number=i+1
            )

    CSV_header_footer_saving.combine_csvs_in_data_folder(pdf_path)
    print(f"Processed pages: {pages_to_process}")

