from fastapi import FastAPI
from bitrix import rename_products, delete_cabin


app = FastAPI(
    title='Renaming Products',
    description='Вебхук для переименования продуктов в сделках для компании Идеалстрой'
)


@app.get('/ping/', status_code=200, tags=['Main'])
async def ping():
    return {'Message': 'Pong'}


@app.post('/rename/', status_code=200, tags=['Main'])
async def rename(deal_id: int) -> list:
    """Переименовывает продукты в сделке"""
    return await rename_products(deal_id)


@app.post('/delete/', status_code=200, tags=['Main'])
async def delete(sp_id: str) -> list:
    """
    Удаляет продукт Бытовка из продуктов в сделке, если есть продукт прокат.
    sp_id - ид смарт процесса. Он приходит в формате SI_2827, поэтому, парсим его как строку.
    """
    if sp_id.startswith('SI_'):
        sp_id = sp_id[3:]
    return await delete_cabin(sp_id)
