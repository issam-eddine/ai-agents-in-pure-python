import json
import os
from dotenv import load_dotenv

import requests
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"

# Step 1: Define the tool (function) that we want to call

def get_weather(latitude, longitude):
    """This is a publically available API that returns the weather for a given location."""
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    data = response.json()
    return data["current"]

# Step 2: Call model with get_weather tool defined

tools = [
    {
        "type": "function",  # Specifies that this is a function tool
        "function": {
            "name": "get_weather",  # The name of the function to call
            "description": "Get current temperature for provided coordinates in celsius.",  # Description helps the model understand when to use this tool
            "parameters": {
                "type": "object",  # Parameters are structured as a JSON object
                "properties": {
                    "latitude": {"type": "number"},  # Geographic latitude coordinate (required)
                    "longitude": {"type": "number"},  # Geographic longitude coordinate (required)
                },
                "required": ["latitude", "longitude"],  # Both coordinates are mandatory for the API call
                "additionalProperties": False,  # Prevents the model from adding unexpected parameters
            },
            "strict": True,  # Enforces strict schema validation for the function parameters
        },
    },
]

messages = [
    {"role": "system", "content": "You are a helpful weather assistant."},
    {"role": "user", "content": "What's the weather like in Paris right now?"},
]

completion1 = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tools,
)

response1 = completion1.choices[0].message

print(response1.model_dump())

# Step 3: Model decides to call function(s)

print(completion1.model_dump())

# Step 4: Execute get_weather function

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)

for i, tool_call in enumerate(completion1.choices[0].message.tool_calls):
    print(f"tool call {i + 1}: name = {tool_call.function.name}")
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    messages.append(completion1.choices[0].message.model_dump())  # this is the message from the model that called the tool

    result = call_function(name, args)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result),
        }  # this is the message as a response to the tool call
    )

# Step 5: Supply result and call model again

# define the response format using Pydantic
class WeatherResponse(BaseModel):
    location: str = Field(description="the name of the location for which the weather is being requested")
    latitude: float = Field(description="the latitude of the location for which the weather is being requested")
    longitude: float = Field(description="the longitude of the location for which the weather is being requested")
    temperature: float = Field(description="the current temperature in celsius for the given location")
    response: str = Field(description="a natural language response to the user's question")

completion2 = client.beta.chat.completions.parse(
    model=model,
    messages=messages,
    tools=tools,
    response_format=WeatherResponse,
)

response2 = completion2.choices[0].message.parsed

print(response2)

messages.append(completion2.choices[0].message.model_dump())

# Step 6: Check model response

print(completion2.model_dump())

for key, value in response2.model_dump().items():
    print(f"{key}: {value}")

# Step 7: print the history of messages

for i, message in enumerate(messages):
    print()
    print(json.dumps(message, indent=4))
