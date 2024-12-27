from fastapi import FastAPI
from bitrix import rename_products


app = FastAPI(
    title='Renaming Products',
    description='Вебхук для переименования продуктов в сделках для компании Идеалстрой'
)


@app.get('/ping/', status_code=200, tags=['Main'])
async def ping():
    return {'Message': 'Pong'}


@app.patch('/rename/', status_code=200, tags=['Main'])
async def main(deal_id: int):
    """Переименовывает продукты в сделке"""
    return await rename_products(deal_id)
