import asyncio
import time
import pymorphy2
import requests
from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate, get_charged_words

from async_timeout import timeout

def main():
    d = dict(a=1)
    print(d)


async def test_sanitize():
    resp = requests.get('https://dvmn.org/media/filer_public/51/83/51830f54-7ec7-4702-847b-c5790ed3724c/gogol_nikolay_taras_bulba_-_bookscafenet.txt')
    resp.raise_for_status()
    sanitize = SANITIZERS['inosmi.ru']
    # clean_text =  sanitize(resp.text)
    morph = pymorphy2.MorphAnalyzer()

    async with timeout(timeout=1) :
        t_start = time.monotonic()
        article_words = await split_by_words(morph=morph, text=resp.text)
        print('длительность', time.monotonic() - t_start)

    print(len(article_words))
    print(calculate_jaundice_rate(
        article_words=article_words,
        charged_words=get_charged_words()
    ),

    )



if __name__ == '__main__':
    asyncio.run(test_sanitize())

