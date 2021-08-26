import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from sys import platform
from typing import List, Optional
from urllib.parse import urlparse

import aiohttp
import pymorphy2
from anyio import create_task_group

import settings
from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate, get_charged_words, get_title_from_response


class ProcessingStatus(str, Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"
    PENDING = "PENDING"


@dataclass
class ArticleAnalysisResult:
    title: str = "unknown"
    url: str = ""
    status: ProcessingStatus = ProcessingStatus.PENDING
    score: Optional[float] = None
    words_count: Optional[int] = None

    def __repr__(self):
        return f"""Заголовок: {self.title}
Статус: {self.status.value}
Рейтинг: {self.score}
Слов в рейтинге: {self.words_count}"""


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(
    session: aiohttp.ClientSession,
    morph: pymorphy2.MorphAnalyzer,
    charged_words: list,
    url: str,
    process_article_result_list: list,
    title: str = None,
):

    article_analysis_result = ArticleAnalysisResult(url=url)

    news_domain = urlparse(url).netloc
    try:
        sanitize = SANITIZERS[news_domain]
    except KeyError:
        article_analysis_result.status = ProcessingStatus.PARSING_ERROR
        article_analysis_result.title = f"Статья на {news_domain}"
        process_article_result_list.append(article_analysis_result)
        return

    try:
        content = await fetch(session, url)
    except asyncio.exceptions.TimeoutError:
        article_analysis_result.status = ProcessingStatus.TIMEOUT
        article_analysis_result.title = url
        process_article_result_list.append(article_analysis_result)
        return
    except aiohttp.ClientError as err:
        article_analysis_result.status = ProcessingStatus.FETCH_ERROR
        article_analysis_result.title = str(err)
        process_article_result_list.append(article_analysis_result)
        return

    article_analysis_result.title = title or get_title_from_response(content)

    try:
        clean_text = sanitize(content)
        article_words, process_article_duration = await split_by_words(morph=morph, text=clean_text)
        article_analysis_result.words_count = len(article_words)
        logging.info(f"Анализ закончен за {process_article_duration:.2f} сек. Статья: " + article_analysis_result.title)
    except asyncio.exceptions.TimeoutError:
        logging.info("Анализ не был проведен. Статья: " + title)
        article_analysis_result.status = ProcessingStatus.TIMEOUT

        process_article_result_list.append(article_analysis_result)
        return

    article_analysis_result.score = calculate_jaundice_rate(
        article_words=article_words,
        charged_words=charged_words,
    )
    article_analysis_result.status = ProcessingStatus.OK

    process_article_result_list.append(article_analysis_result)


async def process_articles_from_urls(
    urls: List[dict], charged_words: list = get_charged_words(), morph=pymorphy2.MorphAnalyzer()
):
    process_article_result_list = []
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(settings.FETCH_NEWS_TIMEOUT)) as session:
        async with create_task_group() as tg:
            for url in urls:
                tg.start_soon(process_article, session, morph, charged_words, url, process_article_result_list)

    return process_article_result_list


async def main():
    scoring_result = await process_articles_from_urls(
        urls=settings.TEST_ARTICLE_URLS,
    )
    for score in scoring_result:
        print(score, "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
