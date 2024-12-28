"""Запросы к битриксу"""
from fast_bitrix24 import BitrixAsync
from dotenv import dotenv_values
import asyncio, calendar
from typing import Generator
from datetime import datetime, timedelta


ENV = dotenv_values()
BX = BitrixAsync(ENV['BITRIX_WEBHOOK'], verbose=False)


class DealUserFields:
    delivery_address = "UF_CRM_1721643706847"
    rent_date_start = "UF_CRM_1720449634376"
    cabin = "UF_CRM_1728385086"                 # Бытовка


MONTHS = (
    'Январь', 
    'Февраль', 
    'Март', 
    'Апрель', 
    'Май', 
    'Июнь', 
    'Июль', 
    'Август', 
    'Сентябрь', 
    'Октябрь', 
    'Ноябрь', 
    'Декабрь'
)


# @handle_exception
async def rename_products(deal_id: int) -> list:
    """Основной метод переименования продкутов"""
    deal, products = await asyncio.gather(
        get_deal(deal_id), 
        get_products(deal_id)
    )
    handled_products = handle_products(deal, products)
    return await update_products(handled_products)


async def get_deal(deal_id: int) -> dict:
    """Получает информацию о сделке"""
    # тестим сделку 7207
    deal: dict = await BX.call(
        method='crm.deal.get',
        items={'id': deal_id},
        raw=True
    )
    deal = deal['result']
    # получение карточки бытовки
    card_id = deal[DealUserFields.cabin][0] if deal[DealUserFields.cabin] else '1'
    card: dict = await BX.call(
        method='crm.item.get',
        items={'entityTypeId': 1064, 'id': card_id},
        raw=True
    )
    deal[DealUserFields.cabin] = card['result']['item']['title']
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
    # TODO переписать под ID
    rent_start = date_var = datetime.fromisoformat(deal[DealUserFields.rent_date_start])
    rent_flag = True
    for product in products:
        if product['PRODUCT_NAME'].startswith("Прокат") and rent_flag:
            product, date_var = update_from_month_name(product, deal=deal, date_var=date_var)
            rent_flag = False
            yield product
        if product['PRODUCT_ID'] == 1437:           # .startswith("Сумма аренды"): Он же остаток
            yield update_from_month_range(product, deal=deal, rent_start=rent_start)
        if product['PRODUCT_ID'] == 1439:           # product['PRODUCT_NAME'].startswith("Доставка"):
            yield update_from_delivery_address(product, deal=deal)


def update_from_month_name(product: dict, **context) -> dict:
    """Обновляет имя продукта. Добавляет к названию название месяца и год."""
    date_var = context['date_var']
    deal = context['deal']
    current_month_num = date_var.month
    while current_month_num == date_var.month:
        date_var += timedelta(days=1)
    product['PRODUCT_NAME'] = (
        f"Прокат {deal[DealUserFields.cabin]} за "
        f"{MONTHS[date_var.month - 1]} {date_var.year} г."
    )
    return product, date_var


def update_from_month_range(product: dict, **context) -> dict:
    """Обновляет имя продукта. Добавляет в поле дату старта проката и последнюю дату месяца старта проката"""
    deal, rent_start = context['deal'], context['rent_start']
    month_range = calendar.monthrange(rent_start.year, rent_start.month)
    product['PRODUCT_NAME'] = (
        f"Прокат {deal[DealUserFields.cabin]} " 
        f"с {rent_start.strftime(r"%d.%m.%Y")} г. "
        f"по {month_range[-1]}{rent_start.strftime(r".%m.%Y")} г."
    )
    return product


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


async def update_products(updated_products: Generator[dict]) -> list:
    """Посылает запросы и обновляет продукты новыми именами"""
    # Тестим продукт 3797
    batch_sample = "crm.item.productrow.update?id={0}&fields[productName]={1}"
    requests = {i: batch_sample.format(p['ID'], p['PRODUCT_NAME']) for i, p in enumerate(updated_products)}
    return await BX.call_batch(params={'halt': 0, 'cmd': requests})
