from aiohttp import ClientSession
from openai import AsyncClient

from aerith_cbot.services.abstractions import VoiceTranscriber


class OpenAIVoiceTranscriber(VoiceTranscriber):
    def __init__(self, openai_client: AsyncClient, aiohttp_client: ClientSession):
        self._openai_client = openai_client
        self._aiohttp_client = aiohttp_client

    async def transcribe(self, audio_url: str) -> str:
        async with self._aiohttp_client.get(audio_url) as response:
            audio_data = await response.read()

        filename = audio_url.split("/")[-1]

        result = await self._openai_client.audio.transcriptions.create(
            file=(filename, audio_data), model="whisper-1"
        )

        return result.text
