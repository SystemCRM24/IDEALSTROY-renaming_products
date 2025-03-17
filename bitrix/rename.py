import asyncio, calendar
from typing import Generator
from datetime import datetime, timedelta

from .logger import logger
from .bitrix import BX, get_deal, get_products, update_products
from .constants import DealUserFields, MONTHS


async def rename_products(deal_id: int) -> list:
    """Основной метод переименования продкутов"""
    deal, products = await asyncio.gather(
        get_deal_with_cabin(deal_id), 
        get_products(deal_id)
    )
    handled_products = handle_products(deal, products)
    updated_products = await update_products(handled_products)
    asyncio.create_task(log_updates(updated_products))
    return updated_products


async def get_deal_with_cabin(deal_id: int) -> dict:
    """Получает информацию о сделке"""
    # тестим сделку 7207
    deal = await get_deal(deal_id)
    # получение карточки бытовки
    if deal[DealUserFields.cabin]:
        card_id = deal[DealUserFields.cabin][0]
        entity_type_id = 1064
    else:
        card_id = deal[DealUserFields.tool][0]
        entity_type_id = 1056
    card: dict = await BX.call(
        method='crm.item.get',
        items={'entityTypeId': entity_type_id, 'id': card_id},
        raw=True
    )
    if entity_type_id == 1064:
        deal[DealUserFields.cabin] = card['result']['item']['title']
    if entity_type_id == 1056:
        deal[DealUserFields.tool] = card['result']['item']['title']
    return deal


async def get_products(deal_id: int) -> list:
    """Получает продукты сделки"""
    response: dict = await BX.call(
        method='crm.deal.productrows.get',
        items={'id': deal_id},
        raw=True
    )
    return response['result']


def handle_products(deal: dict, products: list) -> Generator[dict]:
    """Ищет нужные продукты и обновляет их"""
    if deal[DealUserFields.cabin_rent_date_start]:
        rent_start = date_var = datetime.fromisoformat(deal[DealUserFields.cabin_rent_date_start])
    else:
        rent_start = date_var = datetime.fromisoformat(deal[DealUserFields.tool_rent_date_start])
    rent_flag = True
    for product in products:
        if product['PRODUCT_NAME'].startswith("Прокат") and not "инструмента" in product['PRODUCT_NAME'] and rent_flag:
            product, date_var = update_from_month_name(product, deal=deal, date_var=date_var)
            rent_flag = False
            yield product
        if product['PRODUCT_ID'] == 3569 or product['PRODUCT_ID'] == 4231:           # .startswith("Сумма аренды"): Он же остаток
            yield update_from_month_range(product, deal=deal, rent_start=rent_start)
        if product['PRODUCT_ID'] == 3561:           # .startswith("Доставка"):
            yield update_from_delivery_address(product, deal=deal)


def update_from_month_name(product: dict, **context) -> dict:
    """Обновляет имя продукта. Добавляет к названию название месяца и год."""
    date_var = context['date_var']
    deal = context['deal']
    current_month_num = date_var.month
    current_day = date_var.day
    last_month_day = last_day_of_month(date_var)
    while current_month_num == date_var.month:
        date_var += timedelta(days=1)
    product['PRODUCT_NAME'] = (
        f"Прокат {deal[DealUserFields.cabin]} за "
        f"{MONTHS[date_var.month - 1 + int(last_month_day-current_day < 25)]} {date_var.year} г."
    )
    return product, date_var


def update_from_month_range(product: dict, **context) -> dict:
    """Обновляет имя продукта. Добавляет в поле дату старта проката и последнюю дату месяца старта проката"""
    deal, rent_start = context['deal'], context['rent_start']
    month_range = calendar.monthrange(rent_start.year, rent_start.month)
    logger.info(deal[DealUserFields.cabin])
    logger.info(deal[DealUserFields.tool])
    if deal[DealUserFields.cabin]:
        product_name = deal[DealUserFields.cabin]
    else:
        product_name = deal[DealUserFields.tool]
    logger.info(deal[DealUserFields.cabin])
    logger.info(deal[DealUserFields.tool])
    if deal[DealUserFields.cabin]:
        product_name = deal[DealUserFields.cabin]
    else:
        product_name = deal[DealUserFields.tool]
    product['PRODUCT_NAME'] = (
        f"Прокат {product_name} " 
        f"с {rent_start.strftime(r"%d.%m.%Y")} г. "
        f"по {month_range[-1]}{rent_start.strftime(r".%m.%Y")} г."
    )
    return product


def last_day_of_month(any_day):
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = any_day.replace(day=28) + timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return (next_month - timedelta(days=next_month.day)).day


def update_from_delivery_address(product: dict, **context) -> dict:
    """Обновляет имя продукта. Добавляет в строчку адресс"""
    production_address = "г. Киров, Производственная, д. 27A"
    delivery_address: str = context['deal'][DealUserFields.delivery_address].split('|')[0]
    delivery_address = delivery_address.split(', ')
    if len(delivery_address) >= 3:                          # Если адрес правильный
        # Удаление индекса из строки адреса
        if delivery_address[-2][0].isdigit():               
            delivery_address[-2] = delivery_address[-2][7:]     
        # Удаление страны из адреса
        del delivery_address[-1]
    product['PRODUCT_NAME'] = (
        f"Доставка бытовки: "
        f"{production_address} - до "
        f"{', '.join(delivery_address[::-1])}"
        f" - {production_address}"
    )
    return product


async def log_updates(products: list):
    """Логгирует обновления в продуктах"""
    for row in products:
        row = row['productRow']
        logger.info(f"Product id: {row['productId']} from deal {row['ownerId']} renamed to -> {row['productName']}")
