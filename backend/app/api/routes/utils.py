from http.client import HTTPException

from fastapi import APIRouter, Depends, FastAPI, File, UploadFile
from dotenv import load_dotenv
import shutil
import openai
import os
import json
import aiofiles
from pathlib import Path
from pydantic.networks import EmailStr
import mimetypes
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import OpenAI
import pytesseract
from PIL import Image

from app.api.deps import get_current_active_superuser

from app.models import (
    Message,
    W2FormModel, TaxDocumentResponse
)
from app.utils import generate_test_email, send_email

load_dotenv();

router = APIRouter(prefix="/utils", tags=["utils"])

# Read dotenv
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "public")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

openai.api_key = OPENAI_API_KEY

MAX_FILE_SIZE = 20 * 1024 * 1024

@router.post("/upload", response_model=W2FormModel)
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to upload a single file.
    """
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    print("------> Incoming File...", file.filename)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds the maximum limit.")
    file.file.seek(0)
    try:
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        async with aiofiles.open(file_location, "wb") as buffer:
            await buffer.write(await file.read())
        print("------> Saving File into:", file_location)
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")

    # Detect file type
    file_type, _ = mimetypes.guess_type(file_location)

    pdf_parse_content = ""
    llm_response = ""

    if file_type == "application/pdf":
        # Extract text from PDF using LangChain
        loader = PyPDFLoader(file_location)
        pages = loader.load()
        text_extracted = ""
        for page in pages:
            if page.page_content.strip():  # Check if text can be selected
                text_extracted += page.page_content + "\n"
            else:  # Process as image if no selectable text
                image = Image.open(page.to_image_file())  # Assume PyPDFLoader can export pages as images
                text_extracted += pytesseract.image_to_string(image) + "\n"

        pdf_parse_content = text_extracted

    elif file_type in ["image/png", "image/jpeg"]:
        # Extract text from image using OCR : using pytesseract
        image = Image.open(file_location)
        text = pytesseract.image_to_string(image)
        pdf_parse_content = text

    print("PDF parse Result: ", pdf_parse_content)

    prompt = """        
            Get structurable data from tax W-2 scanned data. this data is getting from ocr result and all of data is related about tax in US.
            These are order of document value per field. This is scanned data : {data}

            A: Employee's Social Security Number
            B: Employer identification number
            C: Employer's name, address and zip code
            D: Control Number
            E: Employee's first name and initial
            F: Employee's address and zip code
            1: Wages, tips, other compensation
            2: Federal income tax withheld
            3: Social security wages
            4: Social security tax withheld
            5: Medicare wages and tips
            6: Medicare tax withheld
            7: Social security tips
            8: Alocated tips
            10: Dependent care benefits
            11: Nonqualified plans
            12: See instructions for box 12
              (this is 4 input fields 12a, 12b, 12c and 12d)
            13: statutory employee(checkbox), Retirement plan(checkbox), Third-party sick pay(checkbox)
            14: Other
            15: State and Employer's state ID Number
            16: State wages, tips, etc
            17: State income tax
            18: Local wages, tips, etc..
            19: Local income tax
            20: Locality name

            Based on this data, return the values in the JSON structure. you can get value from scanned data.
            valid output: 
            {
             "field Name1": value1,
             "field Name2": value2, 
              ...
            }
            Note: Do not include other sentences for response. just return json data.
            If you can't find specific value, then return empty string like this: ''
        """

    response = openai.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": f'{prompt}, Message {pdf_parse_content}'}],
        max_tokens=1000,
        timeout=200  # Increase timeout to 20 seconds
    )

    response_content = response.choices[0].message.content.strip('```').strip().strip(
        'json').strip()  # Remove surrounding triple quotes, curly braces, "json" tag, and whitespace

    result_json = json.loads(response_content)

    print("Result json: ", result_json)

    return W2FormModel(
        employee_ssn=result_json.get("Employee's Social Security Number", ""),
        employer_ein=result_json.get("Employer identification number", ""),
        employer_name_address_zip=result_json.get("Employer's name, address and zip code", ""),
        control_number=result_json.get("Control Number", ""),
        employee_first_name_initial=result_json.get("Employee's first name and initial", ""),
        employee_address_zip=result_json.get("Employee's address and zip code", ""),
        wages_tips_other_compensation=result_json.get("Wages, tips, other compensation", ""),
        federal_income_tax_withheld=result_json.get("Federal income tax withheld", ""),
        social_security_wages=result_json.get("Social security wages", ""),
        social_security_tax_withheld=result_json.get("Social security tax withheld", ""),
        medicare_wages_tips=result_json.get("Medicare wages and tips", ""),
        medicare_tax_withheld=result_json.get("Medicare tax withheld", ""),
        social_security_tips=result_json.get("Social security tips", ""),
        allocated_tips=result_json.get("Allocated tips", ""),
        dependent_care_benefits=result_json.get("Dependent care benefits", ""),
        nonqualified_plans=result_json.get("Nonqualified plans", ""),
        box_12a=result_json.get("12a", ""),
        box_12b=result_json.get("12b", ""),
        box_12c=result_json.get("12c", ""),
        box_12d=result_json.get("12d", ""),
        other=result_json.get("Other", ""),
        state_employer_state_id=result_json.get("State and Employer's state ID Number", ""),
        state_wages_tips=result_json.get("State wages, tips, etc", ""),
        state_income_tax=result_json.get("State income tax", ""),
        local_wages_tips=result_json.get("Local wages, tips, etc", ""),
        local_income_tax=result_json.get("Local income tax", ""),
        locality_name=result_json.get("Locality name", ""),
    )


@router.post("/upload-multiple")
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    """ =
    Endpoint to upload multiple files.
    """
    file_paths = []
    for file in files:
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_location)

    return {"file_paths": file_paths}


@router.post(
    "/test-email",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.post("/generate-response",
             response_model=TaxDocumentResponse)
async def generate_response(message: str) -> dict:
    """
    Endpoint to generate a response from a given input message using LangChain LLM.
    """
    prompt = "You are making a tax document assistant."
    response = openai.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": message
            }
        ],
        max_tokens=1000,
        timeout=200  # Increase timeout to 20 seconds
    ).choices[0].message.content.strip()
    print("Response: ", response)
    return TaxDocumentResponse(message=response)


@router.get("/health-check/")
async def health_check() -> bool:
    return True
