from flask import Flask, jsonify, request
import requests

app = Flask(__name__)


@app.route("/ga4_proxy", methods=["POST"])
def ga4_proxy():
    """
    API endpoint that receives three parameters via POST request
    and sends data to GA4 backend via Measurement Protocol.
    """

    parameters = ["show_title", "show_subtitle", "event_type"]

    for param in parameters:
        if param not in request.json:
            return jsonify({"error": f"Missing '{param}' parameter"}), 400

    show_title = request.json.get("show_title")
    show_subtitle = request.json.get("show_subtitle")
    event_type = request.json.get("event_type")

    measurement_id = "MEASUREMENT_ID"
    api_secret = "API_SECRET"

    endpoint = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"

    data = {
        "client_id": "MY_CLIENT_ID",
        "events": [
            {
                "name": "play",
                "params": {
                    "event_category": show_title,
                    "event_label": show_subtitle,
                    "event_type": event_type,  # Radio play or Arci play ?
                },
            }
        ],
    }

    headers = {
        "content-type": "application/json",
    }

    try:
        response = requests.post(endpoint, json=data, headers=headers)
        print(response)
        return jsonify({"message": "Data sent to GA4 API."}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
