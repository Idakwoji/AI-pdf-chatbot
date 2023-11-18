import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from decouple import AutoConfig
from fastapi import FastAPI, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cachetools
import uuid
import requests

app = FastAPI()
#Initialize in-memory cache
cache = cachetools.LRUCache(maxsize=1000)
#Allow all origins, methods and headers in order to handle the front-end CORS errors
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
#handling environmental variables
config = AutoConfig()
tesseract_path = config("TESSERACT_PATH", default="tesseract")
#define functions
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

#create a fast api dependency to generate a unique user id
def get_user_id():
    return str(uuid.uuid4())


#define end point
@app.post("/upload_pdf/")
async def extract_pdf(pdf_file: UploadFile, user_id: str= Depends(get_user_id)):
    if pdf_file is None:
        return ("Error: No PDF file uploaded")
    pdf_content = await pdf_file.read()
    try:
        the_text = extract_pdf_txt(pdf_content)
        if not the_text.strip():
            the_text = extract_pdf_imagetext(pdf_content)
        if not the_text.strip():
            raise Exception("No text could be extracted from the PDF")
        cache[user_id] = the_text
        return the_text
    except Exception as e:
        #print(f"Exception: {str(e)}")
        return("Invalid file format: Please upload a valid text-based or image-based pdf file")
    
class UserQuestion(BaseModel):
    question: str
api_key = ""
api_url = "https://api.openai.com/v1/engines/gpt-3.5-turbo/completions"
# Set up the headers with your API key
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

app.post("/ask")
async def ask_question(question_data: UserQuestion, user_id: str=Depends(get_user_id)):
    question = question_data.question

    cached_text = cache.get(user_id)
    if cached_text:
        # Combine the cached text and the new question
        prompt = f"{cached_text}\n\nQuestion: {question}"
    else:
        prompt = question 
    # Send the prompt to GPT-3.5
    data = {
        "prompt": prompt,
        "max_tokens": 70  # You can adjust the number of tokens as needed
    }
    response = requests.post(api_url, headers=headers, json=data)
    # Check if the request was successful
    if response.status_code == 200:
        # Get the generated response from GPT-3.5
        gpt_response = response.json()["choices"][0]["text"]
        return {"response": gpt_response}
    else:
        return {"error": "Failed to retrieve GPT-3.5 response"}