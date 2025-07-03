from flask import Flask, request, jsonify, render_template, redirect
from firebase_admin import credentials, firestore, initialize_app
import os

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("unlockimbot-firebase-adminsdk-fbsvc-5de8e43fe0.")
initialize_app(cred)
db = firestore.client()

tools_ref = db.collection("tools")

# Admin Panel (basic password protection)
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "unlockadmin")

@app.route("/")
def home():
    tools = [doc.to_dict() for doc in tools_ref.stream()]
    return render_template("dashboard.html", tools=tools)

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == ADMIN_PASSWORD:
        return redirect("/")
    return "Access Denied", 403

@app.route("/update_tool", methods=["POST"])
def update_tool():
    tool = request.form.get("tool")
    status = request.form.get("status")
    price = int(request.form.get("price"))
    duration = int(request.form.get("duration"))
    tools_ref.document(tool).update({
        "status": status,
        "price": price,
        "duration": duration
    })
    return redirect("/")

# API Endpoints for WhatsApp bot
@app.route("/api/tool_rental")
def tool_rental():
    tools = [doc.to_dict() for doc in tools_ref.stream()]
    msg = "\ud83d\udee0\ufe0f Available Tools for Rent:\n"
    for tool in tools:
        msg += f"{tool['name']}: {'✅' if tool['status'] == 'available' else '❌ In Use'} - PGK {tool['price']} / {tool['duration']} mins\n"
    return ify({"response": msg})

@app.route("/api/<toolname>_status")
def tool_status(toolname):
    doc = tools_ref.document(toolname).get()
    if doc.exists:
        tool = doc.to_dict()
        msg = f"\ud83d\udd0d {tool['name']} Status:\nStatus: {'✅ Available' if tool['status']=='available' else '❌ In Use'}\nPrice: PGK {tool['price']}\nDuration: {tool['duration']} mins"
        return ify({"response": msg})
    return ify({"response": "Tool not found."})

if __name__ == "__main__":
    app.run(debug=True)
