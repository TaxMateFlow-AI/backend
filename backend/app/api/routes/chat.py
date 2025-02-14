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

from dotenv import load_dotenv
from fastapi import APIRouter
from sqlalchemy import false
from sqlmodel import func, select

from langchain_openai import ChatOpenAI

from app.models import TaxDocumentResponse, ChatRequest

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

    system_prompt = """
        You are making Tax document Assistant for 1040 Form in US
        
        I'm trying to auto filling into 1040 Form from provided data.
        I've already get data from attached document. it was W-2 form.
        But some of fields in 1040 Form is empty and it's too much for known from user.
        so for filling fields, you should ask to client one by one.
        
        These are provided fields from W-2 document
          #############
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
          #############
        And these are fields we should fill automatically from Form 1040
          #############
            {
              "filing_status": "",  // Single, Married filing jointly, etc.
              "spouse_social_security_number": "",  // If filing jointly
              "spouse_first_name": "",  // If applicable
              "spouse_last_name": "",  // If applicable
              "digital_assets": {
                "did_receive_or_dispose": false  // Digital asset transactions (Yes/No)
              },
              "adjusted_gross_income": "",  // Total income minus adjustments
              "standard_deduction_or_itemized_deductions": "",  // Standard or itemized
              "taxable_income": "",  // Final taxable income
              "child_tax_credit": "",  // Credit for children
              "other_credits": "",  // Additional credits
              "total_tax": "",  // Total tax amount
              "earned_income_credit": "",  // Earned income tax credit
            }
          #############
        
        - Everytime you should ask to user using question, questions are related for getting undefiend information in 1040 form
        - Do not answer for user's questions very kindly and keep going to make conversation. so that you should get information from user.
        - If you don't need to answer anymore, then say to user what almost complete. and say thank you for your cooperation etc..
        - Do not make too long response, it's more better 1 ~ 2 sentences. 
        - if you want to display some options, then display option. like this 📑 option1 📑 option2 etc..
    """

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
            return TaxDocumentResponse(message=generate_openai_response(user_input))
        else:
            return TaxDocumentResponse(message=validation_result["message"])

    ai_msg = generate_openai_response(user_input)
    print("AI result: ", ai_msg)
    return TaxDocumentResponse(message=ai_msg)

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
    system_prompt = """
        Analyze the last question of the chatbot and the user's answer to check.
        If the answer is in the correct format, then the return type is Yes, the key is the field name, and the value is the user's input value. In here we need to get only the value from the user input.
        If user input sentence, but you should get only value from it. 
        If the input values are almost similar, the return type is yes. That is, recognize it as yes most of the time. 
        Do not recognize uppercase and lowercase letters differently.
        
        For example, the user can input only the value or input in sentence format, but we can output only the value of the user input in JSON format.

        If the user input is irrelevant, incorrectly formatted, or not the requested field value, the type is No and the key is Message. please include example type of input and these input value is related 1040 Form for US tax document. just make message by yourself .
                
        Confirm again, if the type is correct,
        {
         "type": "yes",
         "field_name": "value" (value is user's input)
        }
        if type is incorrect
        {
          "type": "no",
          "message": "message response."
        }
        #######################
        These are valid field names when type is yes
        {
          "filing_status": "",  // Single, Married filing jointly, etc.
          "spouse_social_security_number": "",  // If filing jointly
          "spouse_first_name": "",  // If applicable
          "spouse_last_name": "",  // If applicable
          "digital_assets": {
            "did_receive_or_dispose": false  // Digital asset transactions (Yes/No)
          },
          "adjusted_gross_income": "",  // Total income minus adjustments
          "standard_deduction_or_itemized_deductions": "",  // Standard or itemized
          "taxable_income": "",  // Final taxable income
          "child_tax_credit": "",  // Credit for children
          "other_credits": "",  // Additional credits
          "total_tax": "",  // Total tax amount
          "earned_income_credit": "",  // Earned income tax credit
        }
        ######################
    """

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