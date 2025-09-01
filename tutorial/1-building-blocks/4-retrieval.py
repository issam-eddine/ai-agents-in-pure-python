import json
import os

from dotenv import load_dotenv

from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"

# Define the knowledge base retrieval tool

def search_kb(question: str):
    """
    Load the whole knowledge base from the JSON file.
    (This is a mock function for demonstration purposes, we don't search)
    """
    with open("workflows/1-introduction/kb.json", "rb") as f:
        return json.load(f)

# Step 1: Call model with search_kb tool defined

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Get the answer to the user's question from the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

system_prompt = "You are a helpful assistant that answers questions from the knowledge base about our e-commerce store."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What is the return policy?"},
]

completion = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)

# Step 2: Model decides to call function(s)

print(json.dumps(completion.model_dump(), indent=4))

# Step 3: Execute search_kb function

def call_function(name, args):
    if name == "search_kb":
        return search_kb(**args)

for tool_call in completion.choices[0].message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    messages.append(completion.choices[0].message)

    result = call_function(name, args)
    messages.append(
        {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)}
    )

# Step 4: Supply result and call model again

class KBResponse(BaseModel):
    answer: str = Field(description="The answer to the user's question.")
    source: int = Field(description="The record id of the answer.")

completion_2 = client.beta.chat.completions.parse(
    model=model,
    messages=messages,
    tools=tools,
    response_format=KBResponse,
)

# Step 5: Check model response

final_response = completion_2.choices[0].message.parsed
final_response.answer
final_response.source

# --------------------------------------------------------------
# Question that doesn't trigger the tool
# --------------------------------------------------------------

system_prompt = "You are a helpful assistant that answers questions from the knowledge base about our e-commerce store."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "What is the weather in Tokyo, Japan?"},
]

completion1_ = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)

print(json.dumps(completion1_.choices[0].message.model_dump(), indent=4))

completion2_ = client.beta.chat.completions.parse(
    model=model,
    messages=messages,
    tools=tools,
    response_format=KBResponse,
)

print(json.dumps(completion2_.choices[0].message.parsed.model_dump(), indent=4))

