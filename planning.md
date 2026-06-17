# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
search_listings searches the mock secondhand clothing listings dataset for items that match the user's requested item description, size, and budget. It is the first tool the agent uses because the rest of the workflow depends on finding a real listing to style.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The clothing item or style the user is looking for, such as "vintage graphic tee", "denim jacket", or "chunky sneakers".
- `size` (str): The user's preferred size, such as "S", "M", "L", or "XL". If this is None, the tool should search across all sizes.
- `max_price` (float): The highest price the user wants to pay. If this is None, the tool should not filter by price.

**What it returns:**
id
title
description
category
style_tags
size
price
colors
brand
platform
condition

**What happens if it fails or returns nothing:**
If no listings match, the tool returns an empty list [] instead of crashing. The planning loop should not continue directly to suggest_outfit or create_fit_card with missing data.

For the retry fallback stretch feature, the agent will retry once with looser filters by removing the size filter and slightly increasing the max price. If the retry still returns no results, the agent saves an error in session["error"] and tells the user to try a broader description, a different size, or a higher max price.

---

### Tool 2: suggest_outfit

**What it does:**
suggest_outfit takes the selected thrift listing and the user's wardrobe, then suggests how to wear the item with clothing the user already owns. This tool helps turn a found item into a realistic outfit instead of only showing a product result.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected item returned by search_listings. This should be the exact listing saved in session["selected_item"]
- `wardrobe` (dict): The user's wardrobe data. It may include owned clothing items, shoes, colors, styles, or categories depending on the provided schema.

**What it returns:**
The tool returns a string describing one or more outfit ideas. The suggestion should include the selected new item and at least one wardrobe piece when possible. It should sound like practical styling advice, not just a product description.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, missing, or has no useful items, the tool should still return a general styling suggestion using the selected item. It should not crash, return an empty string, or require the user to re-enter wardrobe information.

---

### Tool 3: create_fit_card

**What it does:**
create_fit_card turns the outfit suggestion and selected item into a short, shareable caption. This is the final step of the workflow and should sound like something someone could post with an outfit picture.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion returned by suggest_outfit.
- `new_item` (dict): The selected listing returned by search_listings.
**What it returns:**
The tool returns a short string that describes the full outfit in a fun, shareable way. It should mention the thrifted item and make the outfit sound intentional.

**What happens if it fails or returns nothing:**
If the outfit input is missing, empty, or incomplete, the tool returns a clear message such as:

"I need a valid outfit suggestion before I can create a fit card."

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent starts by reading what the user is asking for and pulling out the main search details: what item they want, what size they want, and how much they want to spend. Since the rest of the project depends on finding an actual secondhand item first, the first tool the agent uses is always search_listings.If the search finds matching items, the agent picks the best result and saves it. From there, it uses that saved item to ask suggest_outfit how the user could wear it with their current wardrobe. Once an outfit idea is created, the agent sends that outfit idea into create_fit_card to make the final shareable caption.The agent does not just call every tool no matter what. If the search does not find anything, there is no real item to style, so the agent should not move on to the outfit or fit card tools. Instead, it retries one time with looser filters, like removing the size requirement and raising the max price a little. If that still does not find anything, the agent stops and gives the user a helpful message asking them to broaden the search.The loop is finished when the agent has either created a complete result with a selected item, outfit suggestion, and fit card, or when it reaches a clear stopping point because no useful listing could be found.

---

## State Management

**How does information from one tool get passed to the next?**

The agent keeps track of the important pieces of information in a session dictionary while it is working through one user request. This matters because the user should not have to repeat the same item or outfit details after each step. When `search_listings` finds results, the agent saves the best listing as `session["selected_item"]`. That saved item is then passed directly into `suggest_outfit`, so the outfit tool is styling the exact item that was found in the search. After `suggest_outfit` creates an outfit idea, the agent saves it as `session["outfit_suggestion"]`. Then that saved outfit idea is passed into `create_fit_card` along with the selected item. The final caption is saved as `session["fit_card"]`. The session also stores `session["error"]` if something goes wrong and `session["retry_used"]` to track whether the agent already tried a looser search. This keeps the workflow organized and makes it clear what happened at each step.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The tool returns [] and the agent retries with looser filters. If there are still no results the session is saved as  and error and the user is asked to broaden the description |
| suggest_outfit | Wardrobe is empty | The tools returns a standard outifit based on the selected item instead of crashing. This forces the agent to continue to create_fit_card as long as there is a not empty string|
| create_fit_card | Outfit input is missing or incomplete | The tool returns a clear message explaining that a fit card cannot be created without a valid outfit suggestion |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

User Query
   |
   v
Planning Loop
   |
   v
Extract item description, size, and max price
   |
   v
search_listings(description, size, max_price)
   |
   |-- No results -----------------------------|
   |                                           |
   v                                           v
Results found?                         Retry once with looser filters
   |                                    - remove size filter
   |                                    - raise max price slightly
   |                                           |
   |                                           v
   |                                    Results found?
   |                                           |
   |                    No --------------------|-------------------- Yes
   |                    |                                           |
   v                    v                                           v
Save selected item     Save error message                    Save selected item
in session             Return helpful message                 in session
   |                    and stop                                  |
   |                                                               |
   v                                                               |
suggest_outfit(selected_item, wardrobe) <--------------------------|
   |
   |-- Empty wardrobe --> Create general styling suggestion
   |
   v
Save outfit suggestion in session
   |
   v
create_fit_card(outfit_suggestion, selected_item)
   |
   |-- Missing outfit --> Save error message
   |                       Return helpful message
   |
   v
Save fit card in session
   |
   v
Return final response:
- selected item
- outfit idea
- fit card


---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
For the individual tool implementations, I plan to use Claude as a planning and debugging assistant. I will give it the specific tool descriptions from this `planning.md`, including each tool's purpose, inputs, expected return value, and failure mode. I will also give it the starter code from `tools.py` so the generated code fits the project structure instead of being random standalone code. For `search_listings`, I will ask Claude to help implement the search logic using the mock listings dataset. I will verify it by testing at least one query that should return results and one query that should return an empty list. I will make sure the function returns `[]` instead of crashing when no listings match. For `suggest_outfit`, I will ask Claude to help implement an outfit suggestion function that uses the selected listing and the user's wardrobe. I will verify that it returns a useful outfit string when wardrobe data exists and still returns a general styling suggestion if the wardrobe is empty. For `create_fit_card`, I will ask Claude to help create a short shareable caption based on the outfit suggestion and selected item. I will verify that it returns a non-empty caption for valid inputs and a helpful message when the outfit input is missing.
**Milestone 4 — Planning loop and state management:**
For the planning loop, I plan to use ChatGPT to help check the order of tool calls and the state passing between them. I will give it the Planning Loop, State Management, Error Handling, and Architecture sections from this document. I expect the planning loop to call `search_listings` first. If no results are found, the agent should retry once with looser filters. If the retry still fails, the agent should stop and return a helpful message. If results are found, the agent should save the selected listing in `session["selected_item"]`, pass that item into `suggest_outfit`, save the outfit as `session["outfit_suggestion"]`, and then pass both the outfit and selected item into `create_fit_card`. I will verify the final agent by testing a successful query and a failure query. The successful query should show all three tool results. The failure query should prove that the agent does not blindly call the outfit or fit card tools when there is no listing to style.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent reads the user query and extracts the main search details:

- `description = "vintage graphic tee"`
- `size = "M"`
- `max_price = 30.0`

The agent calls:

`search_listings(description="vintage graphic tee", size="M", max_price=30.0)`
If matching listings are found, the tool returns a list of listing dictionaries. The agent picks the best result and saves it as:
`session["selected_item"]`
If no listings are found, the agent retries once with looser filters by removing the size filter and slightly raising the max price. If the retry still finds nothing, the agent stops and gives the user a helpful message.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
After a listing is selected, the agent passes the saved item into the outfit suggestion tool:
`suggest_outfit(new_item=session["selected_item"], wardrobe=wardrobe)`
The tool uses the selected thrift item and the user's wardrobe to create an outfit idea.
Example:
`"Pair the vintage graphic tee with baggy jeans and chunky sneakers for a relaxed streetwear look. Add a hoodie or flannel layer if you want the outfit to feel more complete."`
The agent saves this result as:
`session["outfit_suggestion"]`

**Step 3:**
<!-- Continue until the full interaction is complete -->
After the outfit suggestion is saved, the agent passes the outfit and selected item into the fit card tool:
`create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`
The tool creates a short shareable caption.
Example fit card:
`"Thrifted a vintage graphic tee under $30 and built the fit around baggy jeans, chunky sneakers, and easy streetwear energy."`
The agent saves this result as:
`session["fit_card"]`

**Final output to user:**
<!-- What does the user actually see at the end? -->
I found this for you:
Selected item:
Vintage Graphic Tee — under $30
Size: M
How to style it:
Pair the vintage graphic tee with baggy jeans and chunky sneakers for a relaxed streetwear look. Add a hoodie or flannel layer if you want the outfit to feel more complete.
Fit card:
Thrifted a vintage graphic tee under $30 and built the fit around baggy jeans, chunky sneakers, and easy streetwear energy.

If fails:
I couldn't find an exact match, even after loosening the filters. Try a broader item description, a different size, or a slightly higher budget.