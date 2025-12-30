
import re
import os

HEADER = ['ITEM', 'DESCRIPTION', 'ITEM QTY', 'SELL PRICE', 'EXT. SELL PRICE', 'SALVAGE %', 'SALVAGE AMOUNT', 'FLAG', '', '']
PAGE_WRONG = ['page', int, 'oriented', 'wrong', 'needs', 'rotation','', bool]

def header_footer_saving(data, data_folder, pdf_name, page_number):
    """
    Saves the header/footer rows for a page as a .txt file.
    Each row in data is written as a line in the text file.
    """
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    txt_name = f"{page_number}_header_footer_{pdf_name}.txt"
    txt_path = os.path.join(data_folder, txt_name)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for row in data:
            if isinstance(row, (list, tuple)):
                f.write(', '.join(str(item) for item in row) + '\n')
            else:
                f.write(str(row) + '\n')
    print(f'Saved header/footer as {txt_path}')


def natural_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def combine_csvs_in_data_folder(pdf_path):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    parent_folder = f"{pdf_name}_pages"
    data_folder = os.path.join(parent_folder, "data")
    
    data_folder = os.path.join(parent_folder, "data")

    # Use natural sort for file order
    all_files = [os.path.join(data_folder, f) for f in sorted(os.listdir(data_folder), key=natural_key) if f.endswith('.csv')]
    output_csv = os.path.join(data_folder, f"{pdf_name}_csv_all.csv")

    # Write HEADER as the first row
    with open(output_csv, 'w', newline='', encoding='utf-8') as out_f:
        import csv
        writer = csv.writer(out_f)
        writer.writerow(HEADER)
        for f in all_files:
            try:
                with open(f, 'r', encoding='utf-8') as in_f:
                    reader = csv.reader(in_f)
                    for row in reader:
                        # Only write rows that are not empty and not a header
                        if row and row != HEADER:
                            # Pad or trim row to match HEADER length
                            if len(row) < len(HEADER):
                                row += [''] * (len(HEADER) - len(row))
                            elif len(row) > len(HEADER):
                                row = row[:len(HEADER)]
                            writer.writerow(row)
            except Exception as e:
                print(f"Error reading {f}: {e}")
    print(f"Combined CSV saved as {output_csv}")