import aiohttp
import settings
import logging

logger = logging.getLogger(__name__)


class SDError(Exception):
    pass


class QueueIsBusy(SDError):
    pass


async def get_session(error_on_queue=False) -> aiohttp.ClientSession:
    session = aiohttp.ClientSession(base_url=settings.SD_WEBUI_URL)
    if error_on_queue:
        resp = await session.post("/internal/progress", json={})
        progress = await resp.json()
        logger.debug(progress)
        if resp.status == 200 and progress["eta"] != None:
            await session.close()
            raise QueueIsBusy("Queue is busy. Wait for last request to finish.")
    return session
