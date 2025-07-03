from flask import Flask, request, jsonify, render_template, redirect
from firebase_admin import credentials, firestore, initialize_app
import os

app = Flask(__name__)

# Initialize Firebase
cred_path = "/etc/secrets/firebase/unlockimbot-bffb5-firebase-adminsdk-fbsvc-3939329081.json"
cred = credentials.Certificate(cred_path)
initialize_app(cred)

tools_ref = db.collection("tools")

# Admin Panel (basic password protection)
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "unlockadmin")

@app.route("/")
def home():
    print("Home route accessed")
    try:
        tools = [doc.to_dict() for doc in tools_ref.stream()]
        print(f"Loaded {len(tools)} tools")
        return render_template("dashboard.html", tools=tools)
    except Exception as e:
        print(f"Error loading tools or rendering dashboard: {e}")
        return "Error loading dashboard. Check logs.", 500

@app.route("/login", methods=["POST"])
def login():
    print("Login attempt")
    if request.form.get("password") == ADMIN_PASSWORD:
        print("Login success")
        return redirect("/")
    print("Login failed")
    return "Access Denied", 403

@app.route("/update_tool", methods=["POST"])
def update_tool():
    tool = request.form.get("tool")
    status = request.form.get("status")
    price = int(request.form.get("price"))
    duration = int(request.form.get("duration"))
    print(f"Updating tool {tool}: status={status}, price={price}, duration={duration}")
    try:
        tools_ref.document(tool).update({
            "status": status,
            "price": price,
            "duration": duration
        })
        print("Update successful")
    except Exception as e:
        print(f"Error updating tool: {e}")
        return "Error updating tool", 500
    return redirect("/")

# API Endpoints for WhatsApp bot
@app.route("/api/tool_rental")
def tool_rental():
    print("/api/tool_rental accessed")
    try:
        tools = [doc.to_dict() for doc in tools_ref.stream()]
        msg = "\ud83d\udee0\ufe0f Available Tools for Rent:\n"
        for tool in tools:
            msg += f"{tool['name']}: {'✅' if tool['status'] == 'available' else '❌ In Use'} - PGK {tool['price']} / {tool['duration']} mins\n"
        return jsonify({"response": msg})
    except Exception as e:
        print(f"Error in /api/tool_rental: {e}")
        return jsonify({"response": "Error retrieving tools."}), 500

@app.route("/api/<toolname>_status")
def tool_status(toolname):
    print(f"/api/{toolname}_status accessed")
    try:
        doc = tools_ref.document(toolname).get()
        if doc.exists:
            tool = doc.to_dict()
            msg = f"\ud83d\udd0d {tool['name']} Status:\nStatus: {'✅ Available' if tool['status']=='available' else '❌ In Use'}\nPrice: PGK {tool['price']}\nDuration: {tool['duration']} mins"
            return jsonify({"response": msg})
        else:
            return jsonify({"response": "Tool not found."})
    except Exception as e:
        print(f"Error in /api/{toolname}_status: {e}")
        return jsonify({"response": "Error retrieving tool status."}), 500

# Health check route for testing server responsiveness
@app.route("/ping")
def ping():
    print("/ping accessed")
    return "pong", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting app on port {port}")
    app.run(host="0.0.0.0", port=port)
