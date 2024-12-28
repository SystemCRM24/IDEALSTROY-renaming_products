from fastapi import FastAPI
from bitrix import rename_products
import logging


app = FastAPI(
    title='Renaming Products',
    description='Вебхук для переименования продуктов в сделках для компании Идеалстрой'
)


logger = logging.getLogger("uvicorn")


@app.get('/ping/', status_code=200, tags=['Main'])
async def ping():
    return {'Message': 'Pong'}


@app.get('/rename/', status_code=200, tags=['Main'])
async def main(deal_id: int):
    """Переименовывает продукты в сделке"""
    products = await rename_products(deal_id)
    await log_updates(products)
    return products 


async def log_updates(products: list):
    """Логгирует обновления в продуктах"""
    for row in products:
        row = row['productRow']
        logger.info(f"Product id: {row['productId']} from deal {row['ownerId']} renamed to -> {row['productName']}")
