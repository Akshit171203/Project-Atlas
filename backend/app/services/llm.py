from google import genai

from app.core.config import settings


class GeminiProvider:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.model = settings.GEMINI_MODEL

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "automatic_function_calling": {"disable": True},
            },
        )

        if response.text is None:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text


gemini_provider = GeminiProvider()