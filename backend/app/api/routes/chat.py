import uuid
import openai
import os
import requests
import json
import urllib.request

from dotenv import load_dotenv
from fastapi import APIRouter
from sqlmodel import func, select

from app.models import TaxDocumentResponse, ChatRequest

router = APIRouter(prefix="/chats", tags=["chats"])

load_dotenv()

# Read from dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")


@router.post("/chat_with_openai", response_model=TaxDocumentResponse)
async def chat_with_openai(request: ChatRequest) -> dict:
    """
    Endpoint to generate a response using OpenAI gpt-4o model
    """
    message = request.message
    prompt = """
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
            Primary Info
              - For the year Jan. 1–Dec. 31, 2024, or other tax year beginning
              - 2024, ending
              - Your first name and middle initial
              - Last name
              - If joint return, spouse’s first name and middle initial
              - Last name,
              - Home address (number and street). If you have a P.O. box, see instructions.
              - City, town, or post office. If you have a foreign address, also complete spaces below. 
              - State
              - Zip Code
              - Foreign country name
              - Foreign province/state/country
              - Foreign postal code
            Digital Assets: 
              - At any time during 2024, did you: (a) receive (as a reward, award, or payment for property or services); or (b) sell, exchange, or otherwise dispose of a digital asset (or a financial interest in a digital asset)? (See instructions.) 
            Standard Deduction:
              - Someone 
            Dependents: If more than four dependents,see instructions and check here. 
                > First and Last name, > SSN, > Relationship to you, > child tax credit, > credit for other dependents
        
            Income: Attach Form(s) W-2 here. Also attach Forms W-2G and 1099-R if tax was withheld. If you did not get a Form W-2, see instructions  
              - 1a: Total amount from Form(s) W-2, box 1 (see instructions) 
              - b: Household employee wages not reported on Form(s) W-2
              - c: Tip income not reported on line 1a (see instructions)
              - d: Medicaid waiver payments not reported on Form(s) W-2 (see instructions)
              - e: Taxable dependent care benefits from Form 2441, line 26
              - f: Employer-provided adoption benefits from Form 8839, line 29
              - g: Wages from Form 8919, line 6
              - h: Other earned income (see instructions)
              - i: Nontaxable combat pay election (see instructions)
              - z: Add lines 1a through 1h
              - 2a: Tax-exempt interest.  2b: Taxable interest
              - 3a: Qualified dividends.  3b: Ordinary dividents
              - 4a: IRA distributions.    4b: Taxable amount
              - 5a: Pensions and annuities. 5b: Taxable amount
              - 6a: Social security benefits. 6b: Taxable amount
              - c: If you elect to use the lump-sum election method, check here (see instructions)
              - 7: Capital gain or (loss). Attach Schedule D if required. If not required, check here
              - 8: Additional income from Schedule 1, line 10
              - 9: Add lines 1z, 2b, 3b, 4b, 5b, 6b, 7, and 8. This is your total income
              - 10: Adjustments to income from Schedule 1, line 26 
              - 11: Subtract line 10 from line 9. This is your adjusted gross income
              - 12: Standard deduction or itemized deductions (from Schedule A) 
              - 13 Qualified business income deduction from Form 8995 or Form 8995-A
              - 14 Add lines 12 and 13
              - 15 Subtract line 14 from line 11. If zero or less, enter -0-. This is your taxable income
            Tax and Credits  
              - 16 Tax (see instructions). Check if any from Form(s):
              - 17 Amount from Schedule 2, line 3
              - 18 Add lines 16 and 17
              - 19 Child tax credit or credit for other dependents from Schedule 8812
              - 20 Amount from Schedule 3, line 8
              - 21 Add lines 19 and 20
              - 22 Subtract line 21 from line 18. If zero or less, enter -0-
              - 23 Other taxes, including self-employment tax, from Schedule 2, line 21 
              - 24 Add lines 22 and 23. This is your total tax
            Payments
              - 25 Federal income tax withheld from:
                a: Forms W-2 
                b: Forms 1099
                c: Other forms (see instructions)
                d: Add lines 25a through 25c
              - 26 2024 estimated tax payments and amount applied from 2023 return
              - 27 Earned income credit (EIC)
              - 28 Additional child tax credit from Schedule 8812
              - 29 American opportunity credit from Form 8863, line 8
              - 30 Reserved for future use
              - 31 Amount from Schedule 3, line 15
              - 32 Add lines 27, 28, 29, and 31. These are your total other payments and refundable credits
              - 33 Add lines 25d, 26, and 32. These are your total payments 
            Refund   
              - 34 If line 33 is more than line 24, subtract line 24 from line 33. This is the amount you overpaid 
              - 35
                > a Amount of line 34 you want refunded to you. If Form 8888 is attached, check here
                > b Routing number 
                > c Type (checking, savings)
                > d Account number
              - 36 Amount of line 34 you want applied to your 2025 estimated tax
            Amount You Owe
              - 37 Subtract line 33 from line 24. This is the amount you owe. For details on how to pay, go to www.irs.gov/Payments or see instructions
              - 38 Estimated tax penalty (see instructions)
            Third Party Designee
              - Do you want to allow another person to discuss this return with the IRS? See instructions  (Yes. Complete bellow,  No)
                > Designee's name
                > Phone no 
                > Personal identification number(PIN)
          #############
        
        - Everytime you should ask to user using question, questions are related for getting undefiend information in 1040 form
        - Do not answer for user's questions very kindly and keep going to make conversation. so that you should get information from user.
        - If you don't need to answer anymore, then say to user what almost complete. and say thank you for your cooperation etc..
        - Do not make too long response, it's more better 1 ~ 2 sentences. 
        - if you want to display some options, then display option. like this 📑 option1 📑 option2 
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
