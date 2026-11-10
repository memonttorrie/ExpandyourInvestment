# ExpandyourInvestment — Taglish Real Estate Website Chatbot

A clean, text-only real estate chatbot with all property options, budget matching, and viewing forms **inside the chat panel**, using a Python Flask backend.

## Start locally

1. Open this folder in VS Code.
2. Run `python -m venv .venv` and activate your virtual environment.
3. Run `pip install -r requirements.txt`.
4. Run `python -m backend.app`.
5. Open `http://127.0.0.1:5000`.

The frontend is served by Flask, so the API and website work together locally. No API URL change is needed.

## Folder guide

- `frontend/index.html`: readable website layout, dialogs, and forms
- `frontend/style.css`: design and responsive layout
- `frontend/script.js`: UI interactions and calls to Flask
- No icons or favicon are used in the chatbot UI.
- `backend/app.py`: Flask API (`/api/chat`, `/api/properties`, `/api/viewing`)
- `backend/chatbot.py`: property matching, budget parsing, recommendations, and sentiment prediction
- `dataset/property_facts.json`: editable property information; only UT5 prices are supported by the verified historical PDF
- `dataset/task_b_sentiment.csv`: combined synthetic UT5 + LPC statements (2,224 rows; inferred labels need auditing)
- `notebooks/02_task_b_baselines.ipynb`: train baseline sentiment models; writes `model/sentiment_best.joblib`
- `notebooks/03_xlmr_finetuning.ipynb`: optional research transformer comparison
- `notebooks/01_task_a_baselines.ipynb`: Task A needs labeled listing data; not included
- `model/`: trained artifacts (none included by default)

## What the app does

- Shows 5 property groups, locations, and available historical unit sizes and prices.
- Recommends documented UT5 units that fit a stated maximum **total contract price** budget.
- Shows other properties as **unverified**, rather than assuming they fit the budget.
- Handles Taglish questions about price, sqm, viewing, financing, directions, contact, availability.
- Opens a date-picker viewing request modal. **Requests are NOT sent, saved, or confirmed.**
- Links to Google Maps **search**, not measured distance or route from the user's position.
- Displays the historical UT5 agent phone from the provided PDF. Confirm that it is current before contacting.
- Loads the trained sentiment model if present. The NLP sentiment classifier does **not** generate property facts or recommendations; those use explicit rules and the property facts file.

## Important limits

- UT5 prices originate from a **March 15, 2025 historical price list**, and multiple pricelists may vary.
- Current availability, prices, financing approvals, contact details and appointments are **not verified**.
- There is no live inventory, booking service, CRM integration, distance calculator or authenticated contact form.
- A budget is treated as a maximum **total property price**, not down payment or monthly payment.
- The synthetic sentiment labels were inferred from known generation order; audit and independently annotate them for research.
- No model accuracy has been measured in this package. Train and evaluate the notebook before reporting results.
- Training a sentiment model does not make the chatbot a generative language model.
- Property-type Task A still needs 2,000 labeled listings and additional experimental requirements from the paper.

## Hosting

For a simple working demo, deploy the Flask app on a Python host with `gunicorn backend.app:app` (install `gunicorn`).
Netlify can host the static `frontend/`, but then frontend requests must be updated to use the separately deployed Flask API and Flask must allow that origin. Never expose a Flask development server publicly.

## Security

Do not submit sensitive information to this demo. The viewing form intentionally does not store or transmit an appointment to an agent. Do not treat a prepared request as a booking.

## Latest chatbot UI behavior
- No icons, emojis, or property cards outside the chatbot.
- Property suggestions appear **as soon as the visitor starts typing**. Selecting one sends a property-specific question.
- A property details panel appears inside the chat after selecting a property or asking about it.
- Budget questions show a budget input inside the chat; matching properties are shown there.
- Viewing requests show a date, time, property and contact form inside the chat; submissions are **drafts only**.
- Responses use a simple Filipino-word heuristic to choose Taglish or English. This is not a trained language-identification model, and mixed-language edge cases may be misclassified.
- Existing sentiment training notebooks and dataset remain unchanged.
