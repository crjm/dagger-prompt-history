import anthropic
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
import os
import sys
import json
from db import insert_conversation
import requests
from typing import Dict, Iterable
from anthropic.types import MessageParam  # Add this import at the top

# TODO:
# - Add a way to pass the history to the container - done
# - Add a way to pass the config file to the container 

client = anthropic.Anthropic(
    api_key=os.environ['ANTHROPIC_API_KEY']
)

def response() -> None:
    # Get messages from file and add user prompt
    input_json = sys.argv[1] if len(sys.argv) > 1 else None
    if not input_json:
        raise ValueError("Please provide messages as a JSON string argument")
    
    messages: list[MessageParam] = json.loads(input_json)

    print("sending request with messages:", messages)

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=messages
    )

    event = {
        "session_id": message.id,
        "messages": messages,
        "response": None,
        "model": message.model,
        "stop_reason": message.stop_reason,
        "type": message.type,
        "role": message.role,
        "cache_read_input_tokens": message.usage.cache_read_input_tokens,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens
    }

    content = message.content[0]

    if isinstance(content, TextBlock):
        print(content.text)
        insert_conversation(input_json, content.text)
        event["response"] = content.model_dump_json()
        send_request(event)
    elif isinstance(content, ToolUseBlock):
        print(content.model_dump_json())
        insert_conversation(input_json, content.model_dump_json())
        event["response"] = content.model_dump_json()
        send_request(event)
    else:
        print(content)
        raise ValueError("Unknown response content type")

# send a request to the service

def send_request(event: dict) -> None:
    host = "svc"
    port = 8080
    url = f"http://{host}:{port}/api/v1"
    response = requests.post(url, json=event)
    print(response.status_code)
    print(response.text)

if __name__ == "__main__":
    response()