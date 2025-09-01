from openai import OpenAI


class LLM:
    def __init__(self, api_key: str, system_prompt: str, model: str = "gemini-2.5-flash"):
        self.client = OpenAI(
            api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model = model
        self.system_prompt = system_prompt

    def generate_text(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content if response.choices[0].message.content else ""
