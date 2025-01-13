from .constants import BX, logger
import asyncio


async def delete_cabin(id: str) -> list:
    """Основной метод удаления продукта Бытовка из счета"""
    products = await get_products_from_invoice(id)
    cabin = await pop_cabin(products)
    if cabin is not None:
        asyncio.create_task(delete_cabin_product(cabin))
    return products


async def get_products_from_invoice(id: str) -> list:
    """Получает список товарных позиций из счета."""
    response: dict = await BX.call(
        'crm.item.productrow.list',
        {'filter': {
            '=ownerType': 'SI',     # Идентификатор типа Счет(новый) https://apidocs.bitrix24.ru/api-reference/crm/data-types.html#object_type
            '=ownerId': id
        }},
        raw=True
    )
    try:
        return response['result']['productRows']
    except KeyError:
        return []


async def pop_cabin(products: list) -> dict:
    """Находим словарь бытовки. Исключаем бытовку из списка продуктов"""
    cabin = None
    cabin_index = None
    is_rent = False
    for index, product in enumerate(products):
        if product['productName'].startswith('Прокат'):
            is_rent = True
        if product['productName'].startswith('БК'):
            cabin = product
            cabin_index = index
    if cabin_index is not None:
        del products[cabin_index]
    return cabin if is_rent else None


async def delete_cabin_product(cabin: dict):
    """Делает запрос и удаляет кабину (бытовки)"""
    await BX.call(
        'crm.item.productrow.delete',
        {'id': cabin['id']}
    )
    logger.info(f'Cabin ({cabin['productName']}) was deleted from invoice #{cabin['ownerId']}')
