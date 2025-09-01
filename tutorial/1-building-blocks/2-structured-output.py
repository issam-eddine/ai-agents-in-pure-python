import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Step 1: Define the response format in a Pydantic model

# the `BaseModel` class is a Pydantic class that defines the structure of the response
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

# Step 2: Call the model

# the `parse` method is used to parse the response into the defined structure
completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Extract the event information."
        },
        {
            "role": "user",
            "content": "Alice and Bob are going to a science fair on Friday.",
        },
    ],
    response_format=CalendarEvent,
)

# Step 3: Parse the response

# the `parsed` attribute is used to get the response in the defined structure
event = completion.choices[0].message.parsed

print("Name: {}".format(event.name))
print("Date: {}".format(event.date))
print("Participants: {}".format(event.participants))
