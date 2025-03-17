from .bitrix import BX
from .logger import logger


async def call_process(process_id: str, deal_id: str):
    response = await BX.call(
        'bizproc.workflow.start',
        {
            'TEMPLATE_ID': process_id,
            'DOCUMENT_ID': [
                'crm',
                'CCrmDocumentDeal',
                f'DEAL_{deal_id}'
            ]
        },
        raw=True
    )
    logger.info(f'Business process #{process_id} was started')
    # return response
