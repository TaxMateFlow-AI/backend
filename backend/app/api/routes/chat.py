import uuid
from typing import Any, Coroutine

from langchain.chains.question_answering.map_rerank_prompt import output_parser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import JsonOutputKeyToolsParser
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

import openai
import os
import requests
import json
import urllib.request
import ast

from dotenv import load_dotenv
from fastapi import APIRouter
from sqlalchemy import false
from sqlmodel import func, select

from langchain_openai import ChatOpenAI

from app.models import TaxDocumentResponse, ChatRequest
from app.prompt import Prompt

router = APIRouter(prefix="/chats", tags=["chats"])

load_dotenv()

# Read from dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

openai_llm = ChatOpenAI(
    model=OPENAI_MODEL_NAME,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=OPENAI_API_KEY,
)

@router.post("/chat_with_openai", response_model=TaxDocumentResponse)
async def chat_with_openai(request: ChatRequest) -> TaxDocumentResponse:
    """
    Endpoint to generate a response using OpenAI gpt-4o model
    """
    user_input = request.message

    system_prompt = Prompt.Chat_system_prompt

    def generate_openai_response(user_message: str) -> str:
        messages = [
            (
                "system",
                system_prompt
            ),
            (
                "user",
                user_input
            ),
        ]
        return openai_llm.invoke(messages).content

    if request.isFirst:
        validation_result = validation_user_input(user_input)

        if validation_result["type"] == "yes":
            for key, value in validation_result.items():
                if key != "type":
                    ai_response = generate_openai_response(user_input)
                    message = get_text_from_response(ai_response)
                    print("ai_response: ", message)
                    options = get_string_list_from_response(ai_response)
                    print("options: ", options)

                    return TaxDocumentResponse(message=message,keyword=key, value=value, options=options)
        else:
            return TaxDocumentResponse(message=validation_result["message"], keyword="", value="", list=[])

    ai_response = generate_openai_response(user_input)
    print("AI result: ", ai_response)
    message = get_text_from_response(ai_response)
    print("ai_response: ", message)
    options = get_string_list_from_response(ai_response)
    print("options: ", options)
    return TaxDocumentResponse(message=message, keyword="", value="", options=options)

@router.post("/chat_with_llama", response_model=TaxDocumentResponse)
async def chat_with_llama(request: ChatRequest) -> dict:
    """
    Proxy request to another backend with the given message as raw text.
    """

    remote_url = "http://3.89.25.141:5000/chat"

    # Prepare the payload
    payload = json.dumps({"message": request.message}).encode("utf-8")

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Create a request object
    req = urllib.request.Request(remote_url, data=payload, headers=headers, method="POST")

    try:
        # Make the POST request
        with urllib.request.urlopen(req) as response:
            # Read and decode the response
            response_data = response.read()
            print(response_data)
            return TaxDocumentResponse(message=response_data)

    except urllib.error.HTTPError as e:
        # Handle HTTP errors
        error_message = e.read().decode("utf-8")
        return {
            "error": "Failed to fetch data from remote backend",
            "status_code": e.code,
            "details": error_message,
        }

def validation_user_input(input: str) -> dict:
    """
    Function that Validate for user's input
    """

    user_input = input
    system_prompt = Prompt.Validation_system_prompt

    messages = [
        (
            "system",
            system_prompt
        ),
        (
            "user",
            user_input
        ),
    ]

    ai_msg = openai_llm.invoke(messages)
    print("AI result: ", ai_msg)

    response_content = ai_msg.content.strip('```').strip().strip('json').strip()  # Remove surrounding triple quotes, curly braces, "json" tag, and whitespace
    result_json = json.loads(response_content)
    print("Result json: ", result_json)

    return result_json

def get_text_from_response(ai_response: str) -> str:
    if "###STRINGLIST" not in ai_response:
        return ai_response
    print("ai_response: ", ai_response)
    print("detect: ", ai_response.split("###STRINGLIST")[0].strip())
    return ai_response.split("###STRINGLIST")[0].strip()

def get_string_list_from_response(ai_response: str) -> list:
    # Check if "###STRINGLIST" is in the response
    if "###STRINGLIST" not in ai_response:
        return []  # Return an empty list if the keyword is not found

    # Extract the part after "###STRINGLIST"
    list_string = ai_response.split("###STRINGLIST", 1)[1].strip()

    try:
        # Safely evaluate the list string using ast.literal_eval
        result_list = ast.literal_eval(list_string)

        # Check if the result is a valid list
        if not isinstance(result_list, list):
            raise ValueError("Parsed value is not a list")

        return result_list
    except (ValueError, SyntaxError):
        # Return an empty list if parsing fails
        return []