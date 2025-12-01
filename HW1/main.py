import os
import json
from openai import OpenAI
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

MOCK_DB = {
    "101": {"name": "Bluetooth Speaker", "description": "Portable speaker with deep bass", "price": 59.99},
    "202": {"name": "Noise Cancelling Headphones", "description": "High fidelity wireless ANC headphones", "price": 129.99},
    "303": {"name": "Smart Fitness Watch", "description": "Tracks heart rate, sleep, and activity", "price": 89.99},
}

MOCK_DISCOUNTS = {
    "101": 50,
    "202": 20,
    "303": 15,
}

def get_product_info(product_id: str):
    product = MOCK_DB.get(product_id)
    return product if product else {"error": "Product not found"}

def get_discount(product_id: str):
    discount = MOCK_DISCOUNTS.get(product_id)
    return {"discount_percentage": discount} if discount is not None else {"discount_percentage": 0}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_product_info",
            "description": "Get product information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID such as '101'"
                    }
                },
                "required": ["product_id"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_discount",
            "description": "Get active discount percentage for a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID such as '101'"
                    }
                },
                "required": ["product_id"]
            },
        }
    }
]

available_functions = {
    "get_product_info": get_product_info,
    "get_discount": get_discount,
}

def get_completion_loop(messages, model="gpt-4o", max_iterations=10):
    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg

        for tool_call in msg.tool_calls:

            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_id = tool_call.id

            print(f"Tool call requested: {function_name}({function_args})")

            function_to_call = available_functions[function_name]
            function_result = function_to_call(**function_args)

            print("Tool result:", function_result)

            messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": json.dumps(function_args),
                        }
                    }
                ]
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": function_name,
                "content": json.dumps(function_result),
            })

    raise Exception("Max iterations reached without completion.")

messages = [
    {"role": "system", "content": "You are an e-shop marketing copywriter. Write short promotional campaign texts."},
    {"role": "user", "content": "Write a campaign text for product 202."},
]

final_answer = get_completion_loop(messages)

print("Final answer:")
print(final_answer.content)