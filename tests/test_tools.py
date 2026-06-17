import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


def test_search_returns_list():
    results = search_listings("vintage graphic tee", size="M", max_price=30)
    assert isinstance(results, list)


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_suggest_outfit_with_example_wardrobe():
    results = search_listings("vintage graphic tee", size="M", max_price=30)
    item = results[0]
    outfit = suggest_outfit(item, get_example_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_suggest_outfit_empty_wardrobe():
    results = search_listings("vintage graphic tee", size="M", max_price=30)
    item = results[0]
    outfit = suggest_outfit(item, get_empty_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_create_fit_card_valid_input():
    results = search_listings("vintage graphic tee", size="M", max_price=30)
    item = results[0]
    outfit = "Pair this tee with baggy jeans and chunky sneakers."
    fit_card = create_fit_card(outfit, item)

    assert isinstance(fit_card, str)
    assert len(fit_card.strip()) > 0


def test_create_fit_card_empty_outfit():
    results = search_listings("vintage graphic tee", size="M", max_price=30)
    item = results[0]
    fit_card = create_fit_card("", item)

    assert isinstance(fit_card, str)
    assert "valid outfit suggestion" in fit_card