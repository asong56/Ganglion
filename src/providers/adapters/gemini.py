import os
import json
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def get_completion(messages, tools_schema=None, model="gemini-3.1-pro-preview"):
    if not client:
        return {
            "role": "assistant",
            "content": f"Missing API Key for {model}",
            "tool_calls": None,
        }

    try:
        system_instr = next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )

        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role, parts=[types.Part.from_text(text=m["content"])]
                )
            )

        gemini_tools = []
        if tools_schema:
            functions = []
            for t in tools_schema:
                functions.append(
                    types.FunctionDeclaration(
                        name=t["name"],
                        description=t.get("description", ""),
                        parameters=t["parameters"],
                    )
                )
            gemini_tools.append(types.Tool(function_declarations=functions))

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instr,
                tools=gemini_tools if gemini_tools else None,
            ),
        )

        content_text = ""
        tool_calls = []

        for part in response.candidates[0].content.parts:
            if part.text:
                content_text += part.text
            if part.function_call:
                call = part.function_call
                mock_call = type(
                    "obj",
                    (object,),
                    {
                        "id": f"call_{call.name}",
                        "type": "function",
                        "function": type(
                            "obj",
                            (object,),
                            {"name": call.name, "arguments": json.dumps(call.args)},
                        ),
                    },
                )
                tool_calls.append(mock_call)

        return {
            "role": "assistant",
            "content": content_text if content_text else None,
            "tool_calls": tool_calls if tool_calls else None,
        }

    except Exception as e:
        return {
            "role": "assistant",
            "content": f"E ({model}): {str(e)}",
            "tool_calls": None,
        }
