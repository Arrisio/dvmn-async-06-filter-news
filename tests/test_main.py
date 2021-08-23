import aiohttp
import pytest
import pymorphy2
import main

# @pytest.fixture(scope="class")
from text_tools import get_charged_words


@pytest.fixture(scope="function")
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture(scope="module")
def morph():
    return pymorphy2.MorphAnalyzer()


@pytest.fixture(scope="module")
def charged_words():
    yield main.get_charged_words()


# @pytest.mark.parametrize('morph', indirect=True)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://lenta.ru",
            main.ArticleAnalysisResult(
                title="Статья на lenta.ru",
                status=main.ProcessingStatus.PARSING_ERROR,
                words_count=None,
                score=None,
            ),
        ),
        (
            "https://inosmi.ru/politic/20210625/xxx.html",
            main.ArticleAnalysisResult(
                title='404, message=\'Not Found\', url=URL(\'https://inosmi.ru/politic/20210625/xxx.html\')',
                status=main.ProcessingStatus.FETCH_ERROR,
                words_count=None,
                score=None,
            ),
        ),
        (
            "https://inosmi.ru/economic/20210625/249987698.html",
            main.ArticleAnalysisResult(
                title="Fox News (США): Россия заявляет, что готова нанести удар по вторгающимся военным кораблям | Политика | ИноСМИ - Все, что достойно перевода",
                status=main.ProcessingStatus.OK,
                words_count=343,
                score=1.13,
            ),
        ),

    ],
)
# def test_process_article(url, session,morph, charged_words):
async def test_process_article(url, expected, session, morph, charged_words):
    result = []
    await main.process_article(
        session=session, morph=morph, charged_words=charged_words, url=url, process_article_result_list=result
    )

    assert result[0] == expected
