import aiohttp
import pymorphy2
import pytest
from sys import platform
import asyncio

import process_articles

if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# @pytest.fixture(scope="function")
@pytest.yield_fixture(scope="function")
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(scope="session")
def morph():
    return pymorphy2.MorphAnalyzer()


# @pytest.fixture(scope="session")
@pytest.yield_fixture(scope="session")
def charged_words():
    yield process_articles.get_charged_words()


