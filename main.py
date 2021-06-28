from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse
from time import monotonic
import async_timeout
import anyio
import aiohttp
import asyncio
from sys import platform

import pymorphy2
from anyio import create_task_group

import settings
from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate, get_charged_words, get_title_from_html


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class ArticleAnalysisResult:
    title: str
    url: str = ""
    status: ProcessingStatus = ProcessingStatus.OK
    score: float = None
    words_count: int = None
    processing_article_duration: float = None

    def __repr__(self):
        # if self.status == ProcessingStatus.OK:
        return f"Заголовок: {self.title}\nСтатус: {self.status.value}\nРейтинг: {self.score}\nСлов в рейтинге: {self.words_count}\nINFO:{self.get_info()}"

    def get_info(self):
        if self.status == ProcessingStatus.OK:
            return f"Анализ закончен за {self.processing_article_duration:.2f} сек."

        return f"Анализ не был проведен"


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()

import timeout_decorator
from multiprocessing import Process


async def dodo(html,morph, sanitize):
    # processing_article_start_time = monotonic()
    clean_text = sanitize(html)
    article_words = split_by_words(morph=morph, text=clean_text)
    # processing_article_duration = monotonic() - processing_article_start_time
    return article_words



from contextlib import asynccontextmanager
from contextvars import ContextVar

tm = ContextVar('tm')

async def process_article(session, morph, charged_words, url, res, title=None):

    news_domain = urlparse(url).netloc
    try:
        sanitize = SANITIZERS[news_domain]
    except KeyError:
        res.append(ArticleAnalysisResult(title=f"Статья на {news_domain}", status=ProcessingStatus.PARSING_ERROR))
        return

    try:
        html = await fetch(session, url)
    except asyncio.exceptions.TimeoutError:
        res.append(ArticleAnalysisResult(title=url, status=ProcessingStatus.TIMEOUT))
        return
    except aiohttp.ClientError as err:
        res.append(ArticleAnalysisResult(title=str(err), status=ProcessingStatus.FETCH_ERROR))
        return

    if not title:
        title = get_title_from_html(html)

    try:

        async with async_timeout.timeout(timeout=.2) as cm:
        # async with anyio.create_task_group() as tgg:
            # async with anyio.fail_after(.1) as cm:
            print(title, 'start', cm.remaining)

            clean_text = await sanitize(html)
            article_words = await split_by_words(morph=morph, text=clean_text)
            print(title,'ok', cm.remaining)

            # print('завершилось ',title,processing_article_duration )

    except (TimeoutError, asyncio.exceptions.TimeoutError):
        print(title, 'timeout',cm.remaining)
        res.append(ArticleAnalysisResult(title=title, status=ProcessingStatus.TIMEOUT))
        return

    score = calculate_jaundice_rate(
        article_words=article_words,
        charged_words=charged_words,
    )

    res.append(
        ArticleAnalysisResult(
            title=title,
            score=score,
            words_count=len(article_words),
            processing_article_duration=0,
        )
    )


async def main():
    res = []
    charged_words = get_charged_words()
    morph = pymorphy2.MorphAnalyzer()
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(settings.FETCH_NEWS_TIMEOUT)) as session:
        async with create_task_group() as tg:
            for url in settings.TEST_ARTICLE_URLS:
                tg.start_soon(process_article, session, morph, charged_words, url, res)
                # await process_article(session, morph, charged_words, url)
    for result in res:
        print(result, "\n")


if __name__ == "__main__":

    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
