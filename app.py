from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from backend.chatbot import FACTS, public_property, recommendations, reply
ROOT=Path(__file__).resolve().parents[1]
app=Flask(__name__,static_folder=str(ROOT/"frontend"),static_url_path="")
@app.get("/")
def home():
    return send_from_directory(app.static_folder,"index.html")
@app.get("/api/properties")
def properties():
    try:
        budget=int(request.args["budget"]) if request.args.get("budget") else None
    except ValueError:
        return jsonify({"error":"Invalid budget"}),400
    return jsonify(recommendations(budget,request.args.get("type"),request.args.get("location")))
@app.post("/api/chat")
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get("message","")).strip()
    if not message or len(message)>2000:
        return jsonify({"error":"Enter a message up to 2000 characters"}),400
    budget=data.get("budget")
    try: budget=int(budget) if budget else None
    except (ValueError,TypeError): budget=None
    return jsonify(reply(message,budget,data.get("property_id")))
@app.post("/api/viewing")
def viewing():
    data=request.get_json(silent=True) or {}
    required=("property_id","date","time","name","contact")
    if any(not str(data.get(k,"")).strip() for k in required):
        return jsonify({"error":"Complete all viewing request fields"}),400
    prop=next((p for p in FACTS if p["id"]==data["property_id"]),None)
    if prop is None:return jsonify({"error":"Unknown property"}),400
    # Demo only: do not store personal data or imply a confirmed booking.
    return jsonify({"status":"draft_only","message":"Viewing request prepared but NOT sent or booked. Contact an agent to confirm.","property":prop["name"]})
@app.get("/api/health")
def health():return jsonify({"status":"ok"})
if __name__=="__main__":app.run(debug=True,port=5000)
