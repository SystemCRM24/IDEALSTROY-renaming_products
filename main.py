from fastapi import FastAPI
from bitrix import rename_products, delete_cabin, call_process, rename_instrument
import asyncio


app = FastAPI(
    title='Renaming Products',
    description='Вебхук для переименования продуктов в сделках для компании Идеалстрой'
)


@app.get('/ping', status_code=200, tags=['Main'])
async def ping():
    return {'Message': 'Pong'}


@app.post('/rename/', status_code=200, tags=['Main'])
async def rename(deal_id: int) -> list:
    """
    Переименовывает продукты в сделке
    Дополнительно запускает бизнес процесс № 285
    """
    result = await rename_products(deal_id)
    asyncio.create_task(call_process('285', deal_id))
    return result


@app.post('/delete/', status_code=200, tags=['Main'])
async def delete(sp_id: str, product: str) -> list:
    """
    Удаляет продукт <product> из продуктов в смарт-процессе, если есть такой продукт.
    sp_id - ид смарт процесса. Он может прийти в формате SI_2827, поэтому, парсим его как строку.
    product - Название продукта, который нужно удалить из товарных позиций смарт-процесса.
    """
    if sp_id.startswith('SI_'):
        sp_id = sp_id[3:]
    return await delete_cabin(sp_id, product)


@app.post('/rename_instrument/', status_code=200, tags=['Main'])
async def rename_instr(deal_id: int) -> list:
    """
    Переименовывает продукты в сделке с воронки Прокат инструментов.
    """
    result = await rename_instrument(deal_id)
    return result
