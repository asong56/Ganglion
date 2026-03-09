import os
import json
import asyncio
import google.generativeai as genai
from pathlib import Path

api_key = os.environ.get("GOOGLE_AISTUDIO_API_KEY")
if not api_key:
    raise ValueError("Please first set up GOOGLE_AISTUDIO_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-3.1-pro-preview')

TARGET_EXTENSIONS = {'.html', '.sh', '.css', '.scss', '.py', '.c'}
IGNORE_DIRS = {'node_modules', '.git', 'build', 'dist', '__pycache__'}

semaphore = asyncio.Semaphore(1) 

async def generate_instruction(code_snippet, ext):
    prompt = f"""
    Read the following {ext} code. It lacks documentation.
    Your task is to write a short, clear, 1-2 sentence instruction that would prompt an AI to write exactly this code.
    Do NOT explain the code. ONLY output the instruction.
    
    Code:
    ```
    {code_snippet}
    ```
    """
    
    async with semaphore:
        try:
            response = await model.generate_content_async(prompt)
            
            await asyncio.sleep(4) 
            
            return response.text.strip()
        except Exception as e:
            print(f"API request failed: {e}")
            await asyncio.sleep(10)
            return None

async def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().strip()
        
    if not content or len(content) < 20: 
        return None

    ext = file_path.suffix
    print(f"⏳ Getting prompt: {file_path.name} ...")
    
    instruction = await generate_instruction(content, ext)
    
    if instruction:
        print(f"✅ Success: {file_path.name}")
        return {
            "messages": [
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": f"```{ext.replace('.', '')}\n{content}\n```"}
            ]
        }
    return None

async def main(repo_path, output_jsonl):
    tasks = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in TARGET_EXTENSIONS:
                tasks.append(process_file(file_path))
                
    print(f"🔍 Found {len(tasks)} suitable files, connecting Gemini 3.1 Pro...")
    
    results = await asyncio.gather(*tasks)
    
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        valid_count = 0
        for res in results:
            if res:
                f.write(json.dumps(res, ensure_ascii=False) + '\n')
                valid_count += 1
                
    print(f"🎉 Got {valid_count} training data, saved at {output_jsonl}")

if __name__ == "__main__":
    asyncio.run(main('./my_repos', 'omni_agent_dataset.jsonl'))