import asyncio
import os
import string
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

from async_timeout import timeout
from bs4 import BeautifulSoup

import settings


def _clean_word(word):
    word = word.replace("«", "").replace("»", "").replace("…", "")
    # FIXME какие еще знаки пунктуации часто встречаются ?
    word = word.strip(string.punctuation)
    return word


async def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги."""
    words = []
    async with timeout(timeout=settings.PROCESS_NEWS_TIMEOUT) as cm:
        for word in text.split():
            cleaned_word = _clean_word(word)
            normalized_word = morph.parse(cleaned_word)[0].normal_form
            if len(normalized_word) > 2 or normalized_word == "не":
                words.append(normalized_word)
            await asyncio.sleep(0)
    process_article_duration = settings.PROCESS_NEWS_TIMEOUT - cm.remaining
    return words, process_article_duration


def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста, принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = [word for word in article_words if word in set(charged_words)]

    score = len(found_charged_words) / len(article_words) * 100

    return round(score, 2)


def get_charged_words() -> list[str]:
    charged_words = []
    with ZipFile(settings.CHARGED_WORDS_FILE_PATH) as zipfile:
        for file in zipfile.namelist():
            if os.path.isdir(file):
                continue
            with zipfile.open(file) as f:
                charged_words.extend(f.read().decode().splitlines())

    return charged_words


def get_title_from_response(content: str) -> str:
    soup = BeautifulSoup(content, "html.parser")

    if title := soup.find("title"):
        return str(title.string)

    return content.split("\n")[0].strip()


