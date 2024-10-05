from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError
from pdf2image import convert_from_bytes
import pytesseract
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

class PDFRequest(BaseModel):
    pdf_url: str

@app.post("/extract_text")
async def extract_text_from_pdf(request: PDFRequest):
    pdf_url = request.pdf_url
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        pdf_content = response.content
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

    try:
        # まずpdfminerでテキストを抽出
        text = extract_text(BytesIO(pdf_content))
        if text.strip():
            return {"text": text}
        else:
            # テキストが抽出できない場合、OCRを試みる
            images = convert_from_bytes(pdf_content)
            ocr_text = ""
            for image in images:
                ocr_text += pytesseract.image_to_string(image, lang='jpn')  # 日本語の場合 'jpn'
            if ocr_text.strip():
                return {"text": ocr_text}
            else:
                raise HTTPException(status_code=500, detail="No text found in PDF.")
    except PDFSyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")


origins = [
    "*",  # 必要に応じて制限
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
