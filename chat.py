import anthropic
from anthropic.types.text_block import TextBlock
from anthropic.types.tool_use_block import ToolUseBlock
import os
import sys
import json
from db import insert_conversation, dump_db_to_file

client = anthropic.Anthropic(
    api_key=os.environ['ANTHROPIC_API_KEY']
)

def response(filename: str) -> None:
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
        # dump_db_to_file(filename)
    elif isinstance(content, ToolUseBlock):
        print(content.model_dump_json())
        insert_conversation(messages_json, content.model_dump_json())
        # dump_db_to_file(filename)
    else:
        print(content)
        raise ValueError("Unknown response content type")

if __name__ == "__main__":
    response("conversations.json")