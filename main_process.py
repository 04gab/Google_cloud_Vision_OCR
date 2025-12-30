from google.cloud import vision
from PIL import Image
from PIL import ImageDraw

TYPE_LIST = [float, str, float, float, float, float, float, str]

#--- MAIN PROCESS---
def ocr_and_draw_boxes(image_path, key_path): # testing purpose
    client = vision.ImageAnnotatorClient.from_service_account_json(key_path)
    with open(image_path, 'rb') as img_file:
        content = img_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    annotation = response.full_text_annotation
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    if annotation and annotation.pages:
        for page in annotation.pages:
            for block in page.blocks:
                for para in block.paragraphs:
                    for word in para.words:
                        vertices = word.bounding_box.vertices
                        if len(vertices) == 4:
                            box = [(v.x, v.y) for v in vertices]
                            draw.polygon(box, outline='red', width=2)
    img.show()


def merge_close_words(row, x_threshold = 120): # parameter
    if not row:
        return []
    row = sorted(row, key=lambda w: w['x_min'])
    merged = [row[0].copy()]
    for w in row[1:]:
        prev = merged[-1]
        if w['x_min'] - prev['x_max'] < x_threshold:
            # Merge text (only spaces)
            prev['text'] += ' ' + w['text']
            prev['x_max'] = max(prev['x_max'], w['x_max'])
            prev['x_min'] = min(prev['x_min'], w['x_min'])
        else:
            merged.append(w.copy())
    return merged

def extract_raw_ocr_rows(ocr_results):
    if not ocr_results:
        print("No OCR results provided.")
        return []
    for w in ocr_results:
        w['y_center'] = (w['y_min'] + w['y_max']) / 2
    ocr_results = sorted(ocr_results, key=lambda w: (w['y_center'], w['x_min']))
    img_height = max([w['y_max'] for w in ocr_results]) if ocr_results else 1000
    y_tol = img_height * 0.01
    lines = []
    used = set()
    for i, w in enumerate(ocr_results):
        if i in used:
            continue
        line = [w]
        used.add(i)
        y0 = w['y_center']
        for j, w2 in enumerate(ocr_results):
            if j in used:
                continue
            if abs(w2['y_center'] - y0) <= y_tol:
                used.add(j)
                line.append(w2)
        line = sorted(line, key=lambda w: w['x_min'])
        lines.append(line)
    merged_lines = [merge_close_words(line) for line in lines]
    temp_rows = []
    header_targets = ["ITEM", "DESCRIPTION", 'QTY', 'PRICE']
    footer_targets = ['MERCHANDISE', 'TOTAL SELL', 'TOTAL SALVAGE', 'MGR', 'ADMIN']
    temp_data = []
    collecting = False
    first_target = None  # 'header' or 'footer'
    for idx, line in enumerate(merged_lines):
        row = [w['text'] for w in line]
        temp_data.append(row)
        print('Raw detected text:', row)

        if len(row) < len(TYPE_LIST):
            row += [None] * (len(TYPE_LIST) - len(row))
        elif len(row) > len(TYPE_LIST):
            row = row[:len(TYPE_LIST)]

        header_matches = sum(
            any(t.lower() in str(cell).lower() for cell in row if cell is not None)
            for t in header_targets
        )
        footer_matches = sum(
            any(f.lower() in str(cell).lower() for cell in row if cell is not None)
            for f in footer_targets
        )
        header_found = header_matches >= 2
        footer_found = footer_matches >= 1

        if not collecting:
            if header_found:
                print('Header detected first:', row)
                first_target = 'header'
                collecting = True
                continue  
            elif footer_found:
                print('Footer detected first:', row)
                first_target = 'footer'
                collecting = True
                continue 
        else:
            if first_target == 'header' and footer_found:
                print('Footer detected after header:', row)
                break  
            elif first_target == 'footer' and header_found:
                print('Header detected after footer:', row)
                break  
            else:
                temp_rows.append(row)
    temp_data = [row for row in temp_data if row not in temp_rows]

    # If footer detected first, reverse entries in each row and reverse the order of rows
    if first_target == 'footer' and temp_rows:
        #main dataset
        temp_rows = [list(reversed(r)) for r in temp_rows]
        temp_rows = list(reversed(temp_rows))

        # Move all None values in each row to the end
        for i, r in enumerate(temp_rows):
            nones = [x for x in r if x is None]
            not_nones = [x for x in r if x is not None]
            temp_rows[i] = not_nones + nones
        # Reverse the order of words in each string element of each row if it contains spaces
        for i, r in enumerate(temp_rows):
            temp_rows[i] = [
                ' '.join(reversed(str(item).split())) if isinstance(item, str) and ' ' in item else item
                for item in r
            ]
        
        print('Reversed and flipped rows after footer detected first:')
    
    if first_target == 'footer' and temp_data:
        # header and footer
        temp_data = [list(reversed(r)) for r in temp_data]
        temp_data = list(reversed(temp_data))

        for i, r in enumerate(temp_data):
            temp_data[i] = [
                ' '.join(reversed(str(item).split())) if isinstance(item, str) and ' ' in item else item
                for item in r
            ]   

    for r in temp_data:
        print('temp_data', r)
    
    return temp_rows, temp_data

