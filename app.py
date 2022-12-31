import datetime
import os
import glob
import pickle
import json
from flask import Flask, render_template, jsonify, request
from create_session import *
from create_session import get_order_json
from stat_handler import *

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template("index.html", utc_dt=datetime.datetime.now())


@app.route("/add_session")
def login_zomato():
    return render_template("add_session.html")


@app.route("/submit_phone", methods=["POST"])
def submit_phone():
    global driver_store
    data = request.data.decode("utf-8")
    data = json.loads(data)
    print(data)
    phone_num = data["phone"]
    session_id = data["sessionId"]

    if os.path.exists(f"sessions/{phone_num}_session.pkl"):
        response = {"status": 400, "message": "Session already exists"}
        print(response)
        return jsonify(response)
    else:
        driver = create_driver()
        driver = login(driver, phone_num)
        if driver is None:
            response = {"status": 400, "message": "Too many requests"}
            print(response)
            return jsonify(response)
        driver_store[phone_num] = (driver, session_id)
        response = {"status": 200, "message": "OTP sent"}
        print(response)
        return jsonify(response)


@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    global driver_store
    data = request.data.decode("utf-8")
    data = json.loads(data)
    print(data)
    phone_num = data["phone"]
    otp = data["otp"]
    session_id = data["sessionId"]
    driver, og_session_id = driver_store[phone_num]
    if session_id != og_session_id:
        response = {"status": 400, "message": "Invalid session"}
        print(response)
        return jsonify(response)
    is_valid, driver = fill_otp_submit(driver, otp)
    if not is_valid:
        response = {"status": 400, "message": "Invalid OTP"}
        print(response)
        return jsonify(response)
    else:
        req_session = create_req_session(driver)
        # create pickle
        with open(f"sessions/{phone_num}_session.pkl", "wb") as f:
            pickle.dump(req_session, f)
        response = {"status": 200, "message": "Session created"}
        print(response)
        return jsonify(response)


@app.route("/visualisations")
def visualisations():
    session_list = list_of_sessions()
    print(session_list)
    return render_template("visualisations.html", session_list=session_list)


@app.route("/fetch_data", methods=["POST"])
def fetch_data():
    """This function uses the session pickle to fetch data from Zomato"""
    data = request.data.decode("utf-8")
    data = json.loads(data)
    print(data)
    phone_num = data["phone_number"]
    orders = get_order_json(phone_num)
    response = {"status": 200, "message": "Data fetched"}
    print(response)
    return jsonify(response)


@app.route("/get_stats", methods=["POST"])
def get_stats():
    """This function computes the stats"""
    data = request.data.decode("utf-8")
    data = json.loads(data)
    print(data)
    phone_num = data["phone_number"]
    stats = get_stats(phone_num)
    response = {"status": 200, "message": "Stats computed", "stats": stats}
    print(response)
    return jsonify(response)


def get_stats(phone_num):
    user = User_data(phone_num)
    stats = user.generate_stat_str()
    return stats


def list_of_sessions():
    print("...")
    sessions = []
    for file in glob.glob("sessions/*.pkl"):
        phone_num = file.split("_")[0].split("\\")[-1]
        print(phone_num)
        has_data = False
        if os.path.exists(f"order_data/{phone_num}_orders.json"):
            has_data = True
        sessions.append({"phone_number": phone_num, "has_data": has_data})
    return sessions


if __name__ == "__main__":
    # if order_data and sessions folder doesn't exist, create them
    if not os.path.exists("order_data"):
        os.mkdir("order_data")
    if not os.path.exists("sessions"):
        os.mkdir("sessions")

    global driver_store
    driver_store = {}

    app.run(debug=True)
