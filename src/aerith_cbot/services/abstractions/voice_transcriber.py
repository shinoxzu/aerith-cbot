from abc import ABC, abstractmethod


class VoiceTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_url: str) -> str:
        raise NotImplementedError
