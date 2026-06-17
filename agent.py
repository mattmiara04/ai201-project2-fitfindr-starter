"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
        "retry_used": False,
        "retry_message": None,
    }


# ── simple query parser ───────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max price from a natural language query.

    This parser is intentionally simple and rule-based so the agent can be
    tested consistently without needing another LLM call.
    """
    original_query = query
    query_lower = query.lower()

    # Extract max price from patterns like "$30", "under 30", or "under $30"
    max_price = None
    price_match = re.search(r"(?:under|below|less than)?\s*\$?(\d+(?:\.\d+)?)", query_lower)
    if "$" in query_lower or "under" in query_lower or "below" in query_lower or "less than" in query_lower:
        if price_match:
            max_price = float(price_match.group(1))

    # Extract size from patterns like "size M" or "size medium"
    size = None
    size_match = re.search(r"size\s+([a-z0-9/]+)", query_lower)
    if size_match:
        size = size_match.group(1).upper()

    # Build a cleaner description by removing common budget/size wording
    description = original_query

    description = re.sub(r"under\s+\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"below\s+\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"less than\s+\$?\d+(?:\.\d+)?", "", description, flags=re.IGNORECASE)
    description = re.sub(r"\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"size\s+[a-z0-9/]+", "", description, flags=re.IGNORECASE)

    # Remove extra styling context after common phrases
    description = re.split(
        r"i mostly wear|what'?s out there|how would i style|how do i style|with my wardrobe",
        description,
        flags=re.IGNORECASE,
    )[0]

    # Remove common filler words
    filler_phrases = [
        "i'm looking for",
        "im looking for",
        "looking for",
        "i want",
        "find me",
        "show me",
        "a ",
        "an ",
    ]

    cleaned = description.strip()
    for phrase in filler_phrases:
        if cleaned.lower().startswith(phrase):
            cleaned = cleaned[len(phrase):].strip()

    cleaned = cleaned.replace(",", " ").strip()

    if not cleaned:
        cleaned = original_query.strip()

    return {
        "description": cleaned,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    session = _new_session(query, wardrobe)

    # Step 1: Parse user query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Step 2: Search listings
    results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )

    session["search_results"] = results

    # Step 3: Retry once with looser filters if no results
    if not results:
        session["retry_used"] = True

        relaxed_size = None
        relaxed_max_price = max_price + 20 if max_price is not None else None

        retry_results = search_listings(
            description=description,
            size=relaxed_size,
            max_price=relaxed_max_price,
        )

        session["search_results"] = retry_results

        if retry_results:
            results = retry_results
            session["retry_message"] = (
                "I couldn't find an exact match, so I loosened the filters "
                "by removing the size requirement and raising the max price slightly."
            )
        else:
            session["error"] = (
                "I couldn't find an exact match, even after loosening the filters. "
                "Try a broader item description, a different size, or a slightly higher budget."
            )
            return session

    # Step 4: Save selected item
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Step 5: Suggest outfit using selected item and wardrobe
    outfit = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit

    if not outfit or not outfit.strip():
        session["error"] = "The outfit suggestion came back empty, so I could not create a fit card."
        return session

    # Step 6: Create fit card using outfit and selected item
    fit_card = create_fit_card(outfit, selected_item)
    session["fit_card"] = fit_card

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.",
        wardrobe=get_example_wardrobe(),
    )

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        if session["retry_message"]:
            print(session["retry_message"])

        print(f"Parsed: {session['parsed']}")
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    print(f"Parsed: {session2['parsed']}")
    print(f"Retry used: {session2['retry_used']}")
    print(f"Error message: {session2['error']}")