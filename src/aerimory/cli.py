import asyncio
import logging
import os

from aerimory import AerimoryClient
from aerimory.llm import OpenAILLM
from aerimory.types import ChromaConfig, ChromaOpenAIEmbeddingsConfig, Memory, OpenAILLMConfig
from aerimory.vector_stores import ChromaVectorStore


def format_memory(memory: Memory) -> str:
    result = f"ID: {memory.id}\nФакт: {memory.memory}\nДистанция: {memory.distance:.4f}\n"
    result += f"Создано: {memory.created_at}, Обновлено: {memory.updated_at}"

    return result


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        force=True,
        encoding="utf-8",
    )

    openai_key = os.environ["OPENAI_KEY"]
    chroma_host = os.environ["CHROMA_HOST"]
    chroma_port = int(os.environ["CHROMA_PORT"])

    open_ai_llm_config = OpenAILLMConfig(api_key=openai_key, model="gpt-4o-mini")
    chroma_config = ChromaConfig(
        host=chroma_host,
        port=chroma_port,
        openai_embeddings=ChromaOpenAIEmbeddingsConfig(
            api_key=openai_key, embedding_model="text-embedding-3-small"
        ),
    )

    client = AerimoryClient(
        vector_store=ChromaVectorStore(chroma_config), llm=OpenAILLM(open_ai_llm_config)
    )

    print("Aerimory CLI - Система управления памятью")
    print("Доступные команды:")
    print("  add - добавить воспоминание")
    print("  search - найти похожие воспоминания")
    print("  exit - выйти из программы")

    while True:
        command = input("\n> ")

        if command == "add":
            object_id = input("ID пользователя: ")
            memory = input("Факт: ")

            await client.add_memory(object_id, memory, 10)
            print("Факт успешно сохранен!")

            similar = await client.search(object_id, memory)
            if similar:
                print("Похожие факты в памяти:")
                for i, mem in enumerate(similar):
                    print(f"\n--- Факт {i + 1} ---")
                    print(format_memory(mem))

        elif command == "search":
            object_id = input("ID пользователя: ")
            query = input("Поисковый запрос: ")

            results = await client.search(object_id, query)

            if results:
                print("Результаты поиска:")
                for i, mem in enumerate(results):
                    print(f"\n--- Результат {i + 1} ---")
                    print(format_memory(mem))
            else:
                print("Ничего не найдено.")

        elif command == "exit":
            break
        else:
            print("Неизвестная команда.")


def cli():
    """Wrapper for command line"""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Stopped!")


if __name__ == "__main__":
    cli()
