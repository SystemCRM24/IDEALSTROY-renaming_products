import asyncio
from typing import Generator

from .bitrix import BX, get_deal, get_products, update_products
from .constants import DealUserFields
from .logger import logger


async def rename_instrument(deal_id: int) -> list:
    """Основная функция переименования инструмента"""
    deal, products = await asyncio.gather(
        get_deal_with_tool(deal_id),
        get_products(deal_id)
    )
    handled_products = handle_products(deal, products)
    updated_products = await update_products(handled_products)
    asyncio.create_task(log_updates(updated_products))
    return updated_products


async def get_deal_with_tool(deal_id) -> dict:
    deal = await get_deal(deal_id)
    tool: dict = await BX.call(
        method='crm.item.get',
        items={
            'entityTypeId': 1056, 
            'id': deal[DealUserFields.tool][0]
        },
        raw=True
    )
    deal[DealUserFields.tool] = tool['result']['item']
    return deal


def handle_products(deal: dict, products: list[dict]) -> Generator[dict]:
    """Ищет нужные продукты и обновляет их"""
    rent_product = None
    for product in products:
        if product['PRODUCT_ID'] == 1439 or product['PRODUCT_NAME'].startswith('Доставка'):
            yield rename_delivery_product(product, deal)
        elif product['PRODUCT_NAME'].startswith("Прокат"):
            rent_product = product
    if rent_product is not None:
        yield rename_rent_product(rent_product, deal)


def rename_delivery_product(product: dict, deal: dict) -> dict:
    address: str = deal.get(DealUserFields.delivery_address, '')
    address = address.split('|')[0]
    product['PRODUCT_NAME'] = f'Доставка до адреса: {address}'
    return product


def rename_rent_product(rent_product: dict, deal: dict) -> dict:
    tool = deal.get(DealUserFields.tool, {})
    rent_product['PRODUCT_NAME'] = f'Прокат {tool.get('title', '')}'
    return rent_product


async def log_updates(products: list):
    """Логгирует обновления в продуктах"""
    for row in products:
        row = row['productRow']
        logger.info(f"Product id: {row['productId']} from deal {row['ownerId']} renamed to -> {row['productName']}")
