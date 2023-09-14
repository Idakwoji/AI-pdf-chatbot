import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from decouple import config
from fastapi import FastAPI
app = FastAPI()
tesseract_path = config("TESSERACT_PATH")
def extract_pdf_txt(file_name: str):
    with open(file_name, "rb") as file_handle:
        reader = PyPDF2.PdfReader(file_handle, strict = False)
        extracted_text = ""
        for page in reader.pages:
            content = page.extract_text()
            extracted_text += content
    return(extracted_text)

def extract_pdf_imagetext(file_path: str):
    images = convert_from_path(file_path)
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    extracted_text = ""
    for image in images:
        text = pytesseract.image_to_string(image)
        extracted_text += text
    return(extracted_text)

@app.post("/Extract_pdf/")
async def extract_pdf(pdf_content: bytes):
    if pdf_content is None:
        return ("Error: No PDF file uploaded")
    try:
        the_text = extract_pdf_txt(pdf_content)
        if the_text == "":
            the_text = extract_pdf_imagetext(pdf_content)
        return the_text
    except Exception:
        return("Invalid file format: Please upload a valid text-based or image-based pdf file")
    