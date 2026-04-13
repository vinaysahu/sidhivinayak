import os
from langchain_core.messages import HumanMessage
import re
import json
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id="deepseek-ai/DeepSeek-R1-0528",
    task="text-generation",
    huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_TOKEN")
)

model = ChatHuggingFace(llm=llm)

bill_details = {
    "title":"Review",
    "description":"",
    "type": "object",
    "properties":{
        "supplier_name": {
            "type":"string",
            "description":"Supplier name or shop name from where order is comming."
        },
        "supplier_address": {
            "type":"string",
            "description":"Supplier address or shop address from where order is comming."
        },
        "material": {
            "type":"array",
            "items":{
                "name":"string",
                "quantity":{
                    "type":"number",
                    "description":"write the exact quantity of material means how much material there is."
                    },
                "unit_price":{
                    "type":"float",
                    "description":"write the exact amount of per peice of material means how much material per unit price is."
                    },
                "amount":{
                    "type":"float",
                    "description":"write the exact amount of material means material per piece multiply by material quantity."
                    },
            },
            "description":"Give matrial details like material name, quanity, unit price and amount of metrial "
        },
        "recieved_date":{
            "type":"date",
            "description":"Write the date when order is recieved."
        },
        "sub_total":{
            "type":"float",
            "description":"Write the sub total of order."
        },
        "gst":{
            "type":"float",
            "description":"Write the gst if applicable."
        },
        "total":{
            "type":"float",
            "description":"Write the total amount of order."
        },
        "round_total":{
            "type":"number",
            "description":"Write the round off of total amount of order."
        }
    },
    "required":["supplier_name","supplier_address","round_total"]

}

import logging

# Set up logging
logger = logging.getLogger(__name__)

def extract_bill_data(raw_text):
    try:
        structured_model = model.with_structured_output(bill_details)
        res = structured_model.invoke(raw_text)
        return res
    except Exception as e:
        logger.error(f"Error extracting bill data from HuggingFace API: {str(e)}", exc_info=True)
        return None

    