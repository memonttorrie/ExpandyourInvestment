import json, re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
BASE = Path(__file__).resolve().parents[1]
FACTS = json.loads((BASE / "dataset/property_facts.json").read_text(encoding="utf-8"))
MODEL_FILE = BASE / "model/sentiment_best.joblib"

@lru_cache(maxsize=1)
def load_model():
    if MODEL_FILE.exists():
        import joblib
        return joblib.load(MODEL_FILE)
    return None

def sentiment(text):
    model = load_model()
    if model is None:
        return {"label":"not trained","confidence":None,"review":True}
    label = str(model.predict([text])[0])
    if hasattr(model,"predict_proba"):
        confidence = float(max(model.predict_proba([text])[0]))
    else:
        confidence = None  # Linear SVM decision margins are not probabilities
    return {"label":label,"confidence":confidence,"review":confidence is None or confidence < .65}

def locate_property(q):
    q=q.lower()
    aliases={"ut5":["university tower","ut5","ust tower","españa","espana"],
             "playa":["playa calatagan","playa"],
             "casobe":["casobe","ca so be","casobe calatagan"],
             "nautilus":["nautilus"],
             "trat":["trat","punta fuego"]}
    for prop in FACTS:
        if any(alias in q for alias in aliases[prop["id"]]):
            return prop
    return None

def amount(text):
    q=text.lower().replace(",","")
    patterns=[r"(?:₱|php|budget(?:\s+of)?|under|below|less than|up to|hanggang|around|maximum|max)\s*(\d+(?:\.\d+)?)\s*(million|milyon|m|k|thousand|libo)?",
              r"(\d+(?:\.\d+)?)\s*(million|milyon|m|k|thousand|libo)\b"]
    for pattern in patterns:
        match=re.search(pattern,q)
        if match:
            number=float(match.group(1))
            unit=(match.group(2) or "").lower()
            if unit in ("million","milyon","m"): number*=1_000_000
            if unit in ("k","thousand","libo"): number*=1_000
            if number>=100_000: return round(number)
    return None

def public_property(p):
    result={k:v for k,v in p.items() if k not in ("source",)}
    result["directions_url"]="https://www.google.com/maps/search/?api=1&query="+quote(p["map_query"])
    return result

def recommendations(budget=None, kind=None, location=None):
    rows=[]
    for p in FACTS:
        if kind and kind!="all" and p["type"]!=kind: continue
        if location and location!="all" and location.lower() not in p["location"].lower(): continue
        priced=[u for u in p["units"] if budget is None or u["tcp_php"]<=budget]
        rows.append({**public_property(p),"matching_units":priced,"budget_verified":bool(priced),
                     "pricing_status":"Historical price list (2025); confirm with agent" if p["units"] else "Price not documented"})
    if budget is not None:
        rows.sort(key=lambda x:(not x["budget_verified"], min([u["tcp_php"] for u in x["matching_units"]],default=10**15)))
    return rows

def response_language(text):
    """Simple language heuristic; it is not a trained language detector."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    filipino = {"po", "opo", "ba", "yung", "ung", "meron", "may", "magkano", "paano", "saan", "pwede", "gusto", "ako", "kami", "ko", "namin", "kaya", "naman", "lang", "nga", "pa", "ito", "yan", "mura", "mahal", "kumuha", "magpa", "salamat", "kayo", "sa", "ng", "ang", "para", "hindi", "ano", "malapit", "hanap"}
    return "taglish" if len(words & filipino) >= 1 else "english"


def localized_message(action, text, prop, budget, english_message):
    if response_language(text) == "english":
        return english_message.replace(" po?", "?").replace(" po!", "!")
    name = prop["name"] if prop else "property"
    if action == "budget":
        if budget:
            options = recommendations(budget)
            matches = sum(len(p["matching_units"]) for p in options if p["budget_verified"])
            return (f"Sa budget na ₱{budget:,.0f}, may {matches} unit option(s) na pasok sa historical listed prices. "
                    "Check po yung options sa chat. Historical 2025 price list ito, at kailangan i-confirm ang current availability.")
        return "Magkano po ang maximum total budget ninyo? Halimbawa, ₱6M. Ipapakita ko yung available na documented options for comparison."
    if action == "viewing":
        return f"Sure po! Piliin ninyo yung property, preferred date at time sa form dito sa chat. Request draft lang ito at hindi pa confirmed booking."
    if action == "location":
        return "Pwede po nating tingnan yung location at Google Maps link ng property. Para malaman ang nearest, pakisabi muna ang starting location ninyo."
    if action == "contact":
        return ("May historical contact number po sa UT5 price list, pero kailangan munang i-verify kung active pa. " if prop and prop["id"] == "ut5" else
                "Wala pa po tayong verified current agent contact para sa property na ito. ") + "Tingnan po ang property details sa chat."
    if action == "payment":
        return (f"Sa {name}, may historical options na spot cash, deferred 20–80, at bank financing 10–10–80. Need pa pong i-confirm ang current terms." if prop and prop["id"] == "ut5" else
                "Hindi pa po verified ang current payment terms. Kailangan ng updated computation at financing details mula sa agent.")
    if action == "availability":
        return "Wala pa po tayong live inventory, kaya hindi ko ma-confirm kung available ngayon. Pwede po kayong mag-request ng viewing at updated inventory."
    if action == "pricing":
        if prop and prop["units"]:
            return f"Sa {name}, may {len(prop['units'])} documented listings sa 2025 price list, mula ₱{min(u['tcp_php'] for u in prop['units']):,.0f} hanggang ₱{max(u['tcp_php'] for u in prop['units']):,.0f}. Sample: " + "; ".join(f"{u['size']} — ₱{u['tcp_php']:,.0f}" for u in prop["units"][:3]) + ". Historical prices lang po ito, hindi live availability."
        return "Pwede po ninyong tingnan ang property options sa chat. Historical 2025 price list ang basis; hindi ito live price o inventory."
    return "Welcome po sa ExpandyourInvestment! Sabihin ninyo ang budget, preferred property, o itanong ang prices, viewing, payment, at location."


def reply(text, budget=None, property_id=None):
    q=text.lower()
    budget=budget or amount(text)
    prop=locate_property(text) or next((p for p in FACTS if p["id"]==property_id),None)
    s=sentiment(text)
    want_budget=bool(budget) or any(w in q for w in ["budget","afford","recommend","suggest","best property","better property","investment","worth it","mas mura","cheaper"])
    want_view=any(w in q for w in ["viewing","schedule","visit","ocular","tour","tingin","puntahan"])
    want_route=any(w in q for w in ["direction","paano pumunta","how to go","commute","route","nearest","malapit","near me"])
    want_payment=any(w in q for w in ["payment","financing","installment","downpayment","down payment","monthly","hulog","terms"])
    want_price=any(w in q for w in ["price","prices","how much","magkano","presyo","tcp","cost","sqm","size","unit","details","tell me about"])
    want_contact=any(w in q for w in ["contact","agent","number","tawagan","viber"])
    want_avail=any(w in q for w in ["available","availability","rfo","open pa","vacant"])
    if want_budget:
        options=recommendations(budget)
        matched=[p for p in options if p["budget_verified"]]
        if budget:
            message=(f"With a budget of ₱{budget:,.0f}, I found {sum(len(p['matching_units']) for p in matched)} historically priced unit option(s) within budget. " if matched else
                     f"For a ₱{budget:,.0f} budget, I can't verify a matching priced unit from the available documents. ")
        else:
            message="What's your maximum total budget in pesos po? You can enter e.g. ₱6M or ₱10,000,000. "
        message+="Matches are based on the historical 2025 price lists. Availability and suitability require agent confirmation."
        action="budget"
    elif want_view:
        message=f"Sure! Choose a property, preferred date, and time in the viewing form. This sends a request summary only; no appointment is booked until an agent confirms."
        action="viewing"
    elif want_route:
        message="I can show each property's general location and a Google Maps directions link. For the nearest option, please share your starting city or address; I don't know your location."
        action="location"
    elif want_contact:
        message=("The historical UT5 price list includes an agent contact. Please verify it is still active before contacting. "
                 if prop and prop["id"]=="ut5" else "I don't have a verified current agent contact for that property. ")
        message+="Open the property card to see available contact details."
        action="contact"
    elif want_payment:
        message=(f"For {prop['name']}, the supplied historical price list mentions spot cash, deferred 20–80 and bank financing 10–10–80. These terms must be reconfirmed." if prop and prop["id"]=="ut5" else
                 "Payment terms for this property are not verified. Ask the agent for an updated computation, fees and financing requirements.")
        action="payment"
    elif want_avail:
        message="I don't have live inventory access, so I can't confirm whether a unit or lot is available. You can submit a viewing inquiry and request an updated inventory list."
        action="availability"
    elif want_price and prop and prop["units"]:
        message=f"The 2025 price list contains {len(prop['units'])} listings for {prop['name']}, ranging from ₱{min(u['tcp_php'] for u in prop['units']):,.0f} to ₱{max(u['tcp_php'] for u in prop['units']):,.0f}. Examples: "+", ".join(f"{u['size']} — ₱{u['tcp_php']:,.0f}" for u in prop["units"][:3])+". These are historical figures, not live offers."
        action="pricing"
    elif want_price:
        message="You can compare documented 2025 prices and sizes for UT5, CaSoBe, Playa Calatagan, The Nautilus and TRAT in the chat. Current prices require confirmation."
        action="pricing"
    else:
        message=(f"Here are the documented details for {prop['name']}. Select the property below to view its historical listed prices, sizes and map." if prop else "Welcome to ExpandyourInvestment! Tell me your budget, preferred property type or location, or ask about prices, viewing, financing and directions.")
        action="discover"
    message = localized_message(action, text, prop, budget, message)
    return {"reply":message,"sentiment":s,"action":action,"selected_property":prop["id"] if prop else None,
            "budget":budget,"properties":recommendations(budget) if want_budget else ([public_property(prop)] if prop else [public_property(p) for p in FACTS])}
