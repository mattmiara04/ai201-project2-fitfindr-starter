"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  -> list[dict]
    suggest_outfit(new_item, wardrobe)             -> str
    create_fit_card(outfit, new_item)              -> str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Returns a list of matching listing dictionaries.
    Returns [] if nothing matches.
    """
    listings = load_listings()

    if not description:
        description = ""

    search_terms = set(description.lower().replace(",", " ").split())
    scored_results = []

    for listing in listings:
        # Filter by price
        if max_price is not None:
            listing_price = float(listing.get("price", 0))
            if listing_price > float(max_price):
                continue

        # Filter by size
        if size:
            listing_size = str(listing.get("size", "")).lower()
            requested_size = str(size).lower()
            if requested_size not in listing_size:
                continue

        # Search across multiple listing fields
        searchable_parts = [
            str(listing.get("title", "")),
            str(listing.get("description", "")),
            str(listing.get("category", "")),
            str(listing.get("brand", "")),
            str(listing.get("platform", "")),
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]

        searchable_text = " ".join(searchable_parts).lower()

        # Score by keyword overlap
        score = 0
        for term in search_terms:
            if term and term in searchable_text:
                score += 1

        if score > 0:
            scored_results.append((score, listing))

    scored_results.sort(key=lambda pair: pair[0], reverse=True)

    return [listing for score, listing in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.

    If the wardrobe is empty, return general styling advice.
    """
    if not new_item:
        return "I need a selected item before I can suggest an outfit."

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    item_title = new_item.get("title", "the selected item")
    item_description = new_item.get("description", "")
    item_colors = ", ".join(new_item.get("colors", []))
    item_style_tags = ", ".join(new_item.get("style_tags", []))

    client = _get_groq_client()

    if not wardrobe_items:
        prompt = f"""
You are FitFindr, a casual styling assistant.

The user found this thrift item:
- Title: {item_title}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_style_tags}

The user's wardrobe is empty or unavailable.

Give a practical 2-4 sentence styling suggestion using general pieces that would pair well with this item.
Keep it casual, specific, and realistic.
"""
    else:
        wardrobe_text = ""
        for item in wardrobe_items:
            name = item.get("name", item.get("title", "wardrobe item"))
            category = item.get("category", "")
            color = item.get("color", item.get("colors", ""))
            style = item.get("style", item.get("style_tags", ""))

            wardrobe_text += f"- {name}: {category}, {color}, {style}\n"

        prompt = f"""
You are FitFindr, a casual styling assistant.

The user found this thrift item:
- Title: {item_title}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_style_tags}

The user's wardrobe includes:
{wardrobe_text}

Suggest 1-2 complete outfits using the thrift item and specific wardrobe pieces when possible.
Keep the response practical, casual, and under 6 sentences.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful fashion styling assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=250,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    If outfit is empty, return a clear error message instead of crashing.
    """
    if not outfit or not outfit.strip():
        return "I need a valid outfit suggestion before I can create a fit card."

    if not new_item:
        return "I need a selected item before I can create a fit card."

    item_title = new_item.get("title", "thrifted item")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "a secondhand platform")

    client = _get_groq_client()

    prompt = f"""
You are FitFindr, helping create a short outfit caption.

Selected thrift item:
- Item: {item_title}
- Price: ${item_price}
- Platform: {item_platform}

Outfit suggestion:
{outfit}

Write a 2-4 sentence caption that sounds like a real social media outfit post.

Requirements:
- Mention the item name naturally.
- Mention the price once.
- Mention the platform once.
- Capture the outfit vibe in specific terms.
- Keep it casual and authentic, not like an advertisement.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You write casual, authentic outfit captions.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.9,
        max_tokens=180,
    )

    return response.choices[0].message.content.strip()