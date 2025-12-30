import pandas as pd
import numpy as np
import os
import re
import numpy as np

TYPE_LIST = [float, str, float, float, float, float, float]

def contains_non_english(text):
    
    return bool(re.search(r'[^\x00-\x7F]', str(text)))

# Flag if inner value (not first/last) is NaN or None
def flag_row(row):
    vals = row.tolist()
    if pd.isnull(vals[0]) or pd.isnull(vals[-1]):
        return True
    for v in vals[1:-1]:
        if pd.isnull(v) or v is None:
            return True
    return False

def flag_non_english_in_row(row):
    
    for val in row:
        if contains_non_english(val):
            return True
    return False


def missing_entires(row):
        missing = sum(pd.isnull(x) or x is None or (isinstance(x, str) and not x.strip()) for x in row)
        return missing >= 3

def flag_ocr_dataframe(df):
    # Apply all flag sources, blank if no flag, 'True' if flagged
    flag_row_result = df.apply(flag_row, axis=1)
    flag_non_english_result = df.apply(flag_non_english_in_row, axis=1)
    df['FLAG'] = flag_row_result.apply(lambda x: 'True' if x else '')
    df['FLAG'] = flag_non_english_result.apply(lambda x: 'True' if x else '')
    
    # Flag if (SALVAGE %) is greater than 100
    if df.shape[1] > 5:
        salvage_col = df.columns[5]
        df['FLAG'] = df[salvage_col].apply(
            lambda x: 'True' if pd.notna(x) and str(x).strip() != '' and float(x) > 100 else ''
        )
    return df

def remove_inner_nans(row):
        vals = row.tolist()
        first = next((i for i, v in enumerate(vals) if pd.notna(v)), 0)
        last = len(vals) - 1 - next((i for i, v in enumerate(reversed(vals)) if pd.notna(v)), 0)
        new_row = vals[:first] + [v for v in vals[first:last+1] if pd.notna(v)] + vals[last+1:]
        new_row += [None] * (len(vals) - len(new_row))
        return pd.Series(new_row)

def clean_and_save_ocr_rows(temp_rows, data_folder=None, pdf_name=None, page_number=None):

    cleaned_rows = []
    for row in temp_rows:
        if len(row) < len(TYPE_LIST):
            row += [None] * (len(TYPE_LIST) - len(row))
        elif len(row) > len(TYPE_LIST):
            row = row[:len(TYPE_LIST)]
        cleaned_row = []
        for index, entry in enumerate(row):
            expected_type = TYPE_LIST[index]
            cleaned = str(entry) if entry is not None else ''
            if expected_type == float:
                cleaned = re.sub(r"[^\d.-]", "", cleaned)
                if cleaned.count('.') > 1:
                    parts = cleaned.split('.')
                    cleaned = parts[0] + '.' + ''.join(parts[1:])
                cleaned = re.sub(r"^\.+", "", cleaned)
            elif expected_type == str:
                cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)
                cleaned = cleaned.strip()
                while True:
                    new_cleaned = re.sub(r'^[^A-Za-z0-9]+', '', cleaned)
                    new_cleaned = re.sub(r'[^A-Za-z0-9]+$', '', new_cleaned)
                    if new_cleaned == cleaned:
                        break
                    cleaned = new_cleaned
            cleaned_row.append(cleaned)
        cleaned_rows.append(cleaned_row)
    rows = cleaned_rows
    for i, row in enumerate(rows):
        for index, entry in enumerate(row):
            expected_type = TYPE_LIST[index]
            try:
                if expected_type == float:
                    cleaned_entry = re.sub(r"[^\d.-]", "", str(entry)) if entry is not None else ''
                    if cleaned_entry.count('.') > 1:
                        parts = cleaned_entry.split('.')
                        cleaned_entry = parts[0] + '.' + ''.join(parts[1:])
                    cleaned_entry = re.sub(r"^\.+", "", cleaned_entry)
                    row[index] = float(cleaned_entry) if cleaned_entry not in (None, '') else np.nan
                elif expected_type == str:
                    row[index] = str(entry) if entry is not None else ''
            except Exception:
                row[index] = np.nan if expected_type == float else ''

    col_names = [f'col_{i}' for i in range(len(TYPE_LIST))]
    df = pd.DataFrame(rows, columns=col_names)
    for idx, col_type in enumerate(TYPE_LIST):
        if col_type == float:
            df.iloc[:, idx] = pd.to_numeric(df.iloc[:, idx], errors='coerce')
        elif col_type == str:
            df.iloc[:, idx] = df.iloc[:, idx].astype(str)
    
    df = df.apply(remove_inner_nans, axis=1)
    df = flag_ocr_dataframe(df)
    # remove any 'garbage' rows
    df = df[~df.apply(missing_entires, axis=1)]
    
    print(df)
    if data_folder and pdf_name and page_number is not None:
        csv_name = f"{page_number}_page_{[pdf_name]}.csv"
        csv_path = os.path.join(data_folder, csv_name)
        df.to_csv(csv_path, index=False, header=False)
        print(f'Saved OCR output as {csv_path}')
    else:
        df.to_csv('ocr_output.csv', index=False, header=False)
        print('Saved OCR output as ocr_output.csv')
    
