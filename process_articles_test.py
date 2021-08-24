import pytest
import process_articles


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://lenta.ru",
            process_articles.ArticleAnalysisResult(
                title="Статья на lenta.ru",
                status=process_articles.ProcessingStatus.PARSING_ERROR,
                url="https://lenta.ru",
                words_count=None,
                score=None,
            ),
        ),
        (
            "https://inosmi.ru/politic/20210625/xxx.html",
            process_articles.ArticleAnalysisResult(
                title="404, message='Not Found', url=URL('https://inosmi.ru/politic/20210625/xxx.html')",
                status=process_articles.ProcessingStatus.FETCH_ERROR,
                url="https://inosmi.ru/politic/20210625/xxx.html",
                words_count=None,
                score=None,
            ),
        ),
        (
            "https://inosmi.ru/politic/20210824/250366819.html",
            process_articles.ArticleAnalysisResult(
                title="Daily Express (Великобритания): Меркель обрушила на Европу «опасное оружие» соглашением с Путиным на 9 миллиардов фунтов стерлингов | Политика | ИноСМИ - Все, что достойно перевода",
                status=process_articles.ProcessingStatus.OK,
                url="https://inosmi.ru/politic/20210824/250366819.html",
                words_count=947,
                score=1.58,
            ),
        ),
    ],
)
async def test_process_article(url, expected, session, morph, charged_words):
    results = []
    await process_articles.process_article(
        session=session, morph=morph, charged_words=charged_words, url=url, process_article_result_list=results
    )

    assert results[0] == expected
