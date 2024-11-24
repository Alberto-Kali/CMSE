from flask import Flask, request, render_template, redirect, url_for
import requests

app = Flask(__name__)

BASE_URL = "http://backend:8000"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_pdf", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        file = request.files["file"]
        response = requests.post(f"{BASE_URL}/upload_pdf_db", files={"file": file})
        return render_template("upload_pdf.html", message=response.json().get("message"))
    return render_template("upload_pdf.html")

@app.route("/get_events", methods=["GET", "POST"])
def get_events():
    if request.method == "POST":
        keywords = request.form["keywords"]
        response = requests.get(f"{BASE_URL}/get_events", params={"keywords": keywords})
        events = response.json().get("events", [])
        return render_template("get_events.html", events=events)
    return render_template("get_events.html")

@app.route("/travel_info", methods=["GET", "POST"])
def travel_info():
    if request.method == "POST":
        departure_city = request.form["departure_city"]
        arrival_city = request.form["arrival_city"]
        check_in = request.form["check_in"]
        check_out = request.form["check_out"]
        adults = request.form["adults"]
        response = requests.get(f"{BASE_URL}/travel_info", params={
            "departure_city": departure_city,
            "arrival_city": arrival_city,
            "check_in": check_in,
            "check_out": check_out,
            "adults": adults
        })
        return render_template("travel_info.html", info=response.json())
    return render_template("travel_info.html")

@app.route("/register_user", methods=["GET", "POST"])
def register_user():
    if request.method == "POST":
        user_data = {
            "username": request.form["username"],
            "email": request.form["email"],
            "phone": request.form["phone"],
            "name": request.form["name"],
            "description": request.form["description"],
            "avatar": request.form["avatar"],
            "birth": request.form["birth"],
            "city": request.form["city"],
            "sports": request.form.getlist("sports"),
            "password": request.form["password"]
        }
        response = requests.post(f"{BASE_URL}/register_user", json=user_data)
        return render_template("register_user.html", message=response.json().get("message"))
    return render_template("register_user.html")

@app.route("/comment_event", methods=["GET", "POST"])
def comment_event():
    if request.method == "POST":
        event_id = request.form["event_id"]
        user_id = request.form["user_id"]
        rate = request.form["rate"]
        text = request.form["text"]
        images = request.form.getlist("images")
        response = requests.post(f"{BASE_URL}/comment_event/{event_id}/{user_id}", json={
            "rate": rate,
            "text": text,
            "images": images
        })
        return render_template("comment_event.html", message=response.json().get("message"))
    return render_template("comment_event.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
