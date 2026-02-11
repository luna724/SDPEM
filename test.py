import asyncio
import logger
from init_model import init_models
from modules.utils.health import a1111
import logging
logger.setup_logger("TEST", logging.DEBUG)

init_models()
async def setup():
  tasks = []
  tasks.append(asyncio.create_task(a1111.checker()))
  return tasks

if __name__ == "__main__":
  # asyncio.run(setup())

  from modules.database.inference import load_default_engine

  engine = load_default_engine()
  prompt = engine.generate_prompt_text(
    ["1girl", "<lora:Tentacles_Rape_XL:-1>", "tentacles", "smile"],
    temperature=0.4,
    top_k=15,
    similarity_threshold=0.7,
  )
  print(prompt)