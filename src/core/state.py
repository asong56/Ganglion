import json
import os


class SessionState:
    def __init__(self, session_id="default"):
        self.file_path = f"history/{session_id}.json"
        os.makedirs("history", exist_ok=True)

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self, messages):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
