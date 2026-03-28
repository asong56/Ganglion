import os
from openai import OpenAI

def get_completion(messages, tools_schema=None, model="llama-3.3-70b-versatile"):
    api_key = None
    base_url = None

    if "deepseek" in model.lower():
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = "https://api.deepseek.com"
    elif "gpt" in model.lower():
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = "https://api.openai.com/v1"
    elif any(kw in model.lower() for kw in ["local", "ollama", "lmstudio", "vllm"]):
        api_key = os.getenv("LOCAL_API_KEY", "not-needed") 
        base_url = os.getenv("LOCAL_API_BASE", "http://localhost:11434/v1")

        if model.lower().startswith("local/"):
            model = model[6:]
    else:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
    
    if not api_key:
        return {"role": "assistant", "content": f"Missing API Key for {model}", "tool_calls": None}
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        formatted_tools = []
        if tools_schema:
            for t in tools_schema:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["parameters"]
                    }
                })
        
        response = client.chat.completions.create(
            model = model,
            messages = messages,
            tools = formatted_tools if formatted_tools else None
        )

        message = response.choices[0].message

        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        }

    except Exception as e:
        return {"role": "assistant", "content": f"E ({model}): {str(e)}", "tool_calls": None}