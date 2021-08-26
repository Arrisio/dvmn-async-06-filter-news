import asyncio

import pytest
import requests

import settings
from text_tools import split_by_words, calculate_jaundice_rate
from conftest import morph


@pytest.mark.asyncio
async def test_split_by_words(morph):
    words = await split_by_words(morph, "Во-первых, он хочет, чтобы")
    assert words == ["во-первых", "хотеть", "чтобы"]

    words = await split_by_words(
        morph, "«Удивительно, но это стало началом!»"
    )
    assert words == ["удивительно", "это", "стать", "начало"]

    large_text = requests.get(settings.SOME_LARGE_TEXT_URL).text
    with pytest.raises(asyncio.exceptions.TimeoutError):
        await split_by_words(morph, large_text)


def test_calculate_jaundice_rate():
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert (
        33.0
        < calculate_jaundice_rate(
            ["все", "аутсайдер", "побег"], ["аутсайдер", "банкротство"]
        )
        < 34.0
    )
