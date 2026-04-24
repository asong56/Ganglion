from ..providers import CLIENT_MAP
from .state import SessionState


class Orchestrator:
    def __init__(
        self, model="llama-3.3-70b-versatile", tools_schema=None, session_id="default"
    ):
        self.model = model
        self.tools_schema = tools_schema
        self.state_manager = SessionState(session_id)
        self.messages = self.state_manager.load()

        if "claude" in model.lower():
            self.handler = CLIENT_MAP.get("claude")
        elif "gemini" in model.lower():
            self.handler = CLIENT_MAP.get("gemini")
        else:
            self.handler = CLIENT_MAP.get("openai")

        if not self.handler:
            raise ValueError(f"{model} not found")

    def chat(self, user_prompt):
        self.messages.append({"role": "user", "content": user_prompt})

        for _ in range(13):
            response = self.handler(
                messages=self.messages, tools_schema=self.tools_schema, model=self.model
            )

            if response["content"]:
                print(f"[{self.model}] AI: {response['content']}")
                self.messages.append(response)

            if response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    print(f"[{self.model}] Calling {tool_call.function.name}")

                    observation = "Success"
                    self.messages.append(
                        {
                            "role": "tool",
                            "content": observation,
                            "tool_call_id": tool_call.id,
                        }
                    )
                continue
            else:
                break

        self.state_manager.save(self.messages)
