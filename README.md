# Google_cloud_Vision_OCR

This program takes in a pdf file and calls Google Cloud Vision API to scan the text and save the main data into a csv and header footer data into a txt.

# Requirements: 
- Create a folder 
- Save all the code into the folder
- Run requirements.txt
- Create a Google Cloud account, download the JSON KEY and save it into the folder

# How to run the code:
- Update pdf and key path in Google_OCR_PDF.py
- Run Google_OCR_PDF.py


# Technical Workflow:
1. Input pdf
2. Preprocess:
    a. Create a folder called (pdf_name + “_to_image”)
    b. Create sub folder called data (used to store CSV), footer_header (store header footer of each page), pages (original metadata of pdf into a png for API)
    c. Extract original image (display that image for testing)
    d. Scale image (2x)
    e. Check orientation (if width < height, rotate 90 CW, then check if text is upside down -> rotate 180 if upside down)
    f. Save the preprocessed image in the folder
3. Call Google Cloud vision API 
4. Draw bounding boxes around the text detected (display image) (testing)
5. Align text such that it is in a table format
6. Merge any boxes that are close together
7. Look for header or footer:
    a. If header dectected first, pass
    b. If footer detected first, reverse entires
8. For only body:
    a. Clean data based on the expected data type 
    b. Flag any missing or potentially incorrect lines 
    c. If page is not orientated correctly flip the rows
9. Save the page’s body data to a CSV, save header_footer into txt
10. Combine all CSV together 
