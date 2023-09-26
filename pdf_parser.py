import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from decouple import AutoConfig
from fastapi import FastAPI, UploadFile
app = FastAPI()
tesseract_path = AutoConfig("TESSERACT_PATH")
def extract_pdf_txt(file):
    with BytesIO(file) as file_handle:
        reader = PyPDF2.PdfReader(file_handle, strict = False)
        extracted_text = ""
        for page in reader.pages:
            content = page.extract_text()
            extracted_text += content
    return(extracted_text)

def extract_pdf_imagetext(file):
    images = convert_from_bytes(file)
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    extracted_text = ""
    for image in images:
        text = pytesseract.image_to_string(image)
        extracted_text += text
    return(extracted_text)

@app.post("/upload_pdf/")
async def extract_pdf(pdf_file: UploadFile):
    if pdf_file is None:
        return ("Error: No PDF file uploaded")
    pdf_content = await pdf_file.read()
    try:
        the_text = extract_pdf_txt(pdf_content)
        if not the_text.strip():
            the_text = extract_pdf_imagetext(pdf_content)
        if not the_text.strip():
            raise Exception("No text could be extracted from the PDF")
        return the_text
    except Exception as e:
        print(f"Exception: {str(e)}")
        return("Invalid file format: Please upload a valid text-based or image-based pdf file")
    
    
