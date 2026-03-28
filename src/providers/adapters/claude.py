import anthropic
import os
import json

api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None

def get_completion(messages, tools_schema=None, model="claude-sonnet-4-6"):
    if not client:
        return {"role": "assistant", "content": f"Missing API Key for {model}", "tool_calls": None}
    
    try:
        system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
        filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]

        anthropic_tools = []
        if tools_schema:
            for t in tools_schema:
                anthropic_tools.append({
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t["parameters"]
                })
        
        response = client.messages.create(
            model = model,
            max_tokens = 4096,
            system = system_prompt,
            messages = filtered_messages,
            tools = anthropic_tools if anthropic_tools else anthropic.NOT_GIVEN
        )

        content_text = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                mock_call = type('obj', (object,), {
                    "id": block.id,
                    "type": "function",
                    "function": type('obj', (object,), {
                        "name": block.name,
                        "arguments": json.dumps(block.input) 
                    })
                })
                tool_calls.append(mock_call)
        return {
            "role": "assistant",
            "content": content_text if content_text else None,
            "tool_calls": tool_calls if tool_calls else None
        }
    
    except Exception as e:
        return {"role": "assistant", "content": f"E ({model}): {str(e)}", "tool_calls": None}