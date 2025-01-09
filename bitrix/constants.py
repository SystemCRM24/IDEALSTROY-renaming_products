from dotenv import dotenv_values
from fast_bitrix24 import BitrixAsync
import logging


ENV = dotenv_values()
BX = BitrixAsync(ENV['BITRIX_WEBHOOK'], verbose=False)


logger = logging.getLogger("uvicorn")