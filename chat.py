import anthropic
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
import os
import sys
import json
from db import insert_conversation
import requests

# TODO:
# - Add a way to pass the history to the container - done
# - Add a way to pass the config file to the container 

client = anthropic.Anthropic(
    api_key=os.environ['ANTHROPIC_API_KEY']
)

def response() -> None:
    # Get messages from file and add user prompt
    messages_json = sys.argv[1] if len(sys.argv) > 1 else None
    if not messages_json:
        raise ValueError("Please provide messages as a JSON string argument")
    
    messages = json.loads(messages_json)

    # error if not valid json
    if not isinstance(messages, list):
        raise ValueError("Messages must be a valid JSON list")

    print("sending request with messages:", messages)

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=messages
    )

    content = message.content[0]

    if isinstance(content, TextBlock):
        print(content.text)
        insert_conversation(messages_json, content.text)
        send_request(messages)
    elif isinstance(content, ToolUseBlock):
        print(content.model_dump_json())
        insert_conversation(messages_json, content.model_dump_json())
        send_request(messages)
    else:
        print(content)
        raise ValueError("Unknown response content type")

# send a request to the service

def send_request(messages: list) -> None:
    host = "svc"
    port = 8080
    url = f"http://{host}:{port}/api/v1"
    response = requests.post(url, json={"messages": messages})
    print(response.status_code)
    print(response.text)

if __name__ == "__main__":
    response()