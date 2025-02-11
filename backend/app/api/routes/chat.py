import uuid
import openai
import os
import requests
import json
import urllib.request

from dotenv import load_dotenv
from fastapi import APIRouter
from sqlmodel import func, select

from app.api.routes.utils import OPENAI_API_KEY, OPENAI_MODEL_NAME
from app.models import TaxDocumentResponse

router = APIRouter(prefix="/chats", tags=["chats"])

load_dotenv()

# Read from dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")


@router.post("/chat_with_openai", response_model=TaxDocumentResponse)
async def chat_with_openai(message: str) -> dict:
    """
    Endpoint to generate a response using OpenAI gpt-4o model
    """
    prompt = """
        you are making a tax document assistant
    """

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
        timeout=200
    ).choices[0].message.content.strip()

    return TaxDocumentResponse(message=response)


@router.post("/chat_with_llama", response_model=TaxDocumentResponse)
async def chat_with_llama(message: str) -> dict:
    """
    Proxy request to another backend with the given message as raw text.
    """

    remote_url = "http://3.89.25.141:5000/chat"

    # Prepare the payload
    payload = json.dumps({"message": message}).encode("utf-8")

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Create a request object
    req = urllib.request.Request(remote_url, data=payload, headers=headers, method="POST")

    try:
        # Make the POST request
        with urllib.request.urlopen(req) as response:
            # Read and decode the response
            response_data = response.read()
            return TaxDocumentResponse(message=response_data)

    except urllib.error.HTTPError as e:
        # Handle HTTP errors
        error_message = e.read().decode("utf-8")
        return {
            "error": "Failed to fetch data from remote backend",
            "status_code": e.code,
            "details": error_message,
        }


