# from modules.prompt_placeholder import placeholder
from modules.prompt_processor import PromptProcessor
import asyncio
import logger
import logging
logger.setup_logger("TEST", logging.DEBUG)

p = PromptProcessor(input("in: "))
print(asyncio.run(p.process()))