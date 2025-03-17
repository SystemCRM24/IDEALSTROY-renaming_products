from typing import Generator

from dotenv import dotenv_values
from fast_bitrix24 import BitrixAsync


ENV = dotenv_values()
BX = BitrixAsync(ENV['BITRIX_WEBHOOK'], verbose=False)


async def get_deal(deal_id: int) -> dict:
    """Получение информации о сделке"""
    response: dict = await BX.call(
        method='crm.deal.get',
        items={'id': deal_id},
        raw=True
    )
    return response['result']


async def get_products(deal_id: int) -> list:
    """Получает продукты сделки"""
    response: dict = await BX.call(
        method='crm.deal.productrows.get',
        items={'id': deal_id},
        raw=True
    )
    return response['result']


async def update_products(updated_products: Generator[dict]) -> list:
    """Посылает запросы и обновляет продукты новыми именами"""
    # Тестим продукт 3797
    batch_sample = "crm.item.productrow.update?id={0}&fields[productName]={1}"
    requests = {i: batch_sample.format(p['ID'], p['PRODUCT_NAME']) for i, p in enumerate(updated_products)}
    return await BX.call_batch(params={'halt': 0, 'cmd': requests})
