# FitFindr

FitFindr is a multi-tool AI agent that helps users find secondhand clothing, get outfit ideas based on their wardrobe, and generate a short shareable fit card.
The agent uses three required tools:

1. `search_listings(description, size, max_price)`
2. `suggest_outfit(new_item, wardrobe)`
3. `create_fit_card(outfit, new_item)`

It also includes retry fallback logic when the first search returns no results.

---

## Setup
Install dependencies:

```bash
pip install -r requirements.txt
```
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_key_here
```
Run the Gradio app:
```bash
python app.py
```
Then open the local URL shown in the terminal. It is usually:

```text
http://127.0.0.1:7860
```

Run tests:

```bash
pytest tests/
```

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`
**Purpose:**
Searches the mock secondhand listings dataset for items that match the user's requested item, size, and budget.
**Inputs:**
* `description` (`str`): The item or style the user is searching for, such as `"vintage graphic tee"`.
* `size` (`str | None`): The preferred size, such as `"M"` or `"XL"`. If `None`, the tool searches all sizes.
* `max_price` (`float | None`): The highest price the user wants to pay. If `None`, the tool does not filter by price.
**Output:**
Returns a list of matching listing dictionaries. Each listing can include `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
**Failure handling:**
If no listings match, the tool returns an empty list `[]` instead of crashing.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`
**Purpose:**
Suggests one or two outfit ideas using the selected thrift item and the user's current wardrobe.
**Inputs:**
* `new_item` (`dict`): The selected listing returned by `search_listings`.
* `wardrobe` (`dict`): The user's wardrobe data, including an `items` list.
**Output:**
Returns a non-empty string with a practical outfit suggestion.
**Failure handling:**
If the wardrobe is empty, the tool still returns a general styling suggestion using the selected item. It does not crash or return an empty response.

---

### Tool 3: `create_fit_card(outfit, new_item)`
**Purpose:**
Creates a short shareable caption based on the outfit suggestion and selected item.
**Inputs:**
* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected listing returned by `search_listings`.
**Output:**
Returns a short caption that sounds like something someone could post with an outfit photo.
**Failure handling:**
If the outfit input is empty or missing, the tool returns a clear message explaining that a valid outfit suggestion is needed before creating a fit card.

---

## Planning Loop
The agent starts by reading the user's natural language query and extracting three values:

* item description
* size
* max price

The first tool called is always `search_listings`, because the agent needs a real item before it can style anything.
If listings are found, the agent selects the top result and saves it in the session as `session["selected_item"]`. That item is passed directly into `suggest_outfit`. The outfit suggestion returned from that tool is saved as `session["outfit_suggestion"]`.
After that, the agent calls `create_fit_card` using both the outfit suggestion and the selected item. The final caption is saved as `session["fit_card"]`.
The agent does not blindly call all tools every time. If `search_listings` returns no results, the agent retries once with looser filters. It removes the size filter and raises the max price slightly. If the retry still returns no results, the agent stops early and returns a helpful error message.

---

## State Management

The agent uses a session dictionary to keep track of what happens during one interaction.

Important session values:

* `session["query"]`: the original user query
* `session["parsed"]`: extracted description, size, and max price
* `session["search_results"]`: listings returned by `search_listings`
* `session["selected_item"]`: the listing chosen from the search results
* `session["outfit_suggestion"]`: the result from `suggest_outfit`
* `session["fit_card"]`: the result from `create_fit_card`
* `session["error"]`: error message if the workflow stops early
* `session["retry_used"]`: tracks whether fallback search was used
* `session["retry_message"]`: explains when the search was loosened

This makes the workflow clear because each tool's output becomes the next tool's input. The user does not have to re-enter the item or outfit manually.

---

## Error Handling

| Tool              | Failure mode                     | Agent response                                                                                                                                                |
| ----------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_listings` | No listings match the query      | The tool returns `[]`. The agent retries once with looser filters. If there are still no results, it saves a helpful message in `session["error"]` and stops. |
| `suggest_outfit`  | Wardrobe is empty                | The tool returns a general styling suggestion based on the selected item.                                                                                     |
| `create_fit_card` | Outfit input is empty or missing | The tool returns a clear message saying it needs a valid outfit suggestion before creating a fit card.                                                        |

---

## Retry Logic with Fallback
I added retry fallback as a stretch feature.
If the first search returns no matches, the agent automatically tries again with looser filters:
* `size` becomes `None`
* `max_price` increases by 20 if a max price exists
If the retry succeeds, the agent continues with the outfit and fit card tools. If the retry fails, the agent stops and tells the user to try a broader item description, different size, or higher budget.

---

## Demo Walkthrough

### Successful interaction

Example query:
```text
I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers.
```

Step 1:
The agent parses the query into:
```python
{
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0
}
```
Then it calls:
```python
search_listings(description="vintage graphic tee", size="M", max_price=30.0)
```
Step 2:
The agent saves the top listing as:
```python
session["selected_item"]
```
Then it calls:
```python
suggest_outfit(session["selected_item"], wardrobe)
```

Step 3:
The agent saves the outfit as:
```python
session["outfit_suggestion"]
```
Then it calls:
```python
create_fit_card(session["outfit_suggestion"], session["selected_item"])
```
Final result:
The app displays the selected listing, the outfit idea, and the fit card in three separate output panels.

---

### Failure interaction
Example query:

```text
designer ballgown size XXS under $5
```

The first call to `search_listings` returns no results. The agent retries once with looser filters.
If the retry still returns no results, the agent stops and returns:
```text
I couldn't find an exact match, even after loosening the filters. Try a broader item description, a different size, or a slightly higher budget.
```
The agent does not call `suggest_outfit` or `create_fit_card` when there is no item to style.

---

## Spec Reflection

Writing the spec first helped make the implementation easier because each tool had a clear job before I started coding. The planning document made it clear what each function should accept, what it should return, and what should happen when something fails.
One place where the implementation changed slightly from the original idea was query parsing. Instead of using another LLM call to parse the user query, I used a simple rule-based parser with regular expressions. This made the agent easier to test because the parsing behavior is more predictable.
The retry fallback also became part of the planning loop instead of a separate fourth tool. This kept the required three-tool structure clean while still adding the stretch behavior.

---

## AI Usage Transparency
I used ChatGPT as a planning and Claude as a debugging assistant while building this project.

First, I used it to turn the assignment requirements and rubric into a checklist. This helped me make sure `planning.md` included specific tool inputs, outputs, failure modes, planning logic, state management, and an architecture diagram. I reviewed and edited the wording so it matched my actual implementation.

Second, I used it to help debug the Python files after writing the tools and planning loop. I tested each function myself in the terminal and only kept code that matched my planning document. When errors came up, such as import or indentation issues, I used ChatGPT to help identify the problem and then verified the fix by rerunning the tests.

I did not treat AI output as automatically correct. I checked the code by running individual tool tests, running `python agent.py`, testing the Gradio app, and running `pytest tests/`.

---

## Testing

I tested the tools individually and through the full app.

Tests included:

* a successful listing search
* a no-results listing search
* outfit suggestion with an example wardrobe
* outfit suggestion with an empty wardrobe
* fit card creation with valid input
* fit card failure handling with an empty outfit

The test suite passed with:

```text
6 passed
```

---

## Files

Important project files:

```text
planning.md
tools.py
agent.py
app.py
tests/test_tools.py
data/listings.json
data/wardrobe_schema.json
utils/data_loader.py
```
