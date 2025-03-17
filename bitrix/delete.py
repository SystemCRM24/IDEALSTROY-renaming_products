import asyncio

from .bitrix import BX
from .logger import logger


async def delete_cabin(sp_id: str, to_delete: str) -> list:
    """Основной метод удаления продукта Бытовка из счета"""
    products = await get_products_from_invoice(sp_id)
    product = await pop_cabin(products, to_delete)
    if product is not None:
        asyncio.create_task(delete_cabin_product(product))
    return products


async def get_products_from_invoice(sp_id: str) -> list:
    """Получает список товарных позиций из счета."""
    response: dict = await BX.call(
        'crm.item.productrow.list',
        {'filter': {
            '=ownerType': 'SI',     # Идентификатор типа Счет(новый) https://apidocs.bitrix24.ru/api-reference/crm/data-types.html#object_type
            '=ownerId': sp_id
        }},
        raw=True
    )
    try:
        return response['result']['productRows']
    except KeyError:
        return []


async def pop_cabin(products: list, to_delete: str) -> dict:
    """Находим словарь бытовки. Исключаем бытовку из списка продуктов"""
    product_index = product = None
    for index, position in enumerate(products):
        if position['productName'] == to_delete:
            product_index = index
            product = position
    if product_index is not None:
        del products[product_index]
        return product


async def delete_cabin_product(product: dict):
    """Делает запрос и удаляет кабину (бытовки)"""
    await BX.call(
        'crm.item.productrow.delete',
        {'id': product['id']}
    )
    logger.info(f'Product ({product['productName']}) was deleted from smart invoice #{product['ownerId']}')
