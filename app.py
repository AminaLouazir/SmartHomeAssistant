from flask import Flask, request, jsonify
import paho.mqtt.publish as publish
import json
import logging
import os
import random
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change if your broker is on a different host
MQTT_PORT = 1883
MQTT_TOPIC_LIGHT = "home/light"
MQTT_TOPIC_FAN = "home/fan"
MQTT_TOPIC_THERMOSTAT = "home/thermostat"
MQTT_TOPIC_DOOR = "home/door"
MQTT_TOPIC_OWNER = "home/owner"

@app.route('/')
def index():
    """Basic route to verify the server is running."""
    return "Smart Home Webhook is operational!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook requests from Dialogflow."""
    logger.debug(f"Received request headers: {dict(request.headers)}")
    try:
        request_text = request.get_data(as_text=True)
        logger.debug(f"Raw request body: {request_text}")
        req = json.loads(request_text) if request_text else {}
        logger.info(f"Parsed JSON: {json.dumps(req, indent=2)}")
        if 'queryResult' in req:
            query_result = req.get('queryResult', {})
            intent_info = query_result.get('intent', {})
            intent = intent_info.get('displayName', '')
            parameters = query_result.get('parameters', {})
            logger.info(f"Detected intent: {intent}")
            logger.info(f"Parameters: {parameters}")
            response_text = process_intent(intent, parameters)
            response = {'fulfillmentText': response_text}
            logger.info(f"Sending response: {response}")
            return jsonify(response)
        else:
            logger.warning("Request doesn't contain expected Dialogflow structure")
            return jsonify({
                'fulfillmentText': "I couldn't process that request correctly."
            })
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({
            'fulfillmentText': 'Sorry, there was an error processing your request.'
        })

def process_intent(intent, parameters):
    """Process the recognized intent and return appropriate response."""
    logger.info(f"Processing intent: {intent} with parameters: {parameters}")
    try:
        if intent == "TurnOnLight":
            try:
                publish.single(MQTT_TOPIC_LIGHT, payload="ON", hostname=MQTT_BROKER, port=MQTT_PORT)
                logger.info("Published 'ON' to home/light")
            except Exception as mqtt_err:
                logger.warning(f"MQTT publish failed (continuing anyway): {mqtt_err}")
            return "Turning on the light."
        elif intent == "TurnOffLight":
            try:
                publish.single(MQTT_TOPIC_LIGHT, payload="OFF", hostname=MQTT_BROKER, port=MQTT_PORT)
                logger.info("Published 'OFF' to home/light")
            except Exception as mqtt_err:
                logger.warning(f"MQTT publish failed (continuing anyway): {mqtt_err}")
            return "Turning off the light."
        elif intent == "SetTemperature":
            temp = parameters.get('number')
            if temp:
                try:
                    publish.single(MQTT_TOPIC_THERMOSTAT, payload=str(temp), hostname=MQTT_BROKER, port=MQTT_PORT)
                    logger.info(f"Published temperature {temp} to home/thermostat")
                except Exception as mqtt_err:
                    logger.warning(f"MQTT publish failed (continuing anyway): {mqtt_err}")
                return f"Setting temperature to {temp}°C."
            else:
                return "I didn't catch what temperature you wanted."
        elif intent == "ControlFan":
            action = parameters.get('fan_action', 'ON').upper()
            try:
                publish.single(MQTT_TOPIC_FAN, payload=action, hostname=MQTT_BROKER, port=MQTT_PORT)
                logger.info(f"Published '{action}' to home/fan")
            except Exception as mqtt_err:
                logger.warning(f"MQTT publish failed (continuing anyway): {mqtt_err}")
            return f"Turning {action.lower()} the fan."
        elif intent == "TurnOffFan":
            action = parameters.get('fan_action', 'OFF').upper()
            try:
                publish.single(MQTT_TOPIC_FAN, payload=action, hostname=MQTT_BROKER, port=MQTT_PORT)
                logger.info(f"Published '{action}' to home/fan")
            except Exception as mqtt_err:
                logger.warning(f"MQTT publish failed (continuing anyway): {mqtt_err}")
            return f"Turning {action.lower()} the fan."
        else:
            logger.warning(f"Unknown intent: {intent}")
            return "I'm not sure how to help with that request."
    except Exception as e:
        logger.error(f"Error processing intent: {e}", exc_info=True)
        return "Sorry, I encountered an error while processing your request."

@app.route('/test', methods=['GET', 'POST'])
def test():
    """Test endpoint to verify connectivity."""
    if request.method == 'POST':
        try:
            request_text = request.get_data(as_text=True)
            data = json.loads(request_text) if request_text else {}
            logger.info(f"Test endpoint received POST data: {data}")
            return jsonify({
                'status': 'success',
                'message': 'POST request received successfully',
                'received_data': data
            })
        except Exception as e:
            logger.error(f"Error in test endpoint: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': str(e)
            })
    logger.info("Test endpoint received GET request")
    return jsonify({
        'status': 'success',
        'message': 'Smart Home webhook is operational. Send a POST request to test JSON handling.'
    })

# @app.route('/simulate/door', methods=['POST'])
# def simulate_door():
#     """Simulate door/window sensor."""
#     try:
#         door_state = random.choice([True, False])  # Randomly open or close
#         payload = json.dumps({"open": door_state})
#         publish.single(MQTT_TOPIC_DOOR, payload=payload, hostname=MQTT_BROKER, port=MQTT_PORT)
#         logger.info(f"Published door state: {payload} to {MQTT_TOPIC_DOOR}")
#         return jsonify({"status": "success", "open": door_state})
#     except Exception as e:
#         logger.error(f"Error simulating door: {e}")
#         return jsonify({"status": "error", "message": str(e)})

def simulate_door_job():
    """Job to simulate door state periodically."""
    door_state = random.choice([True, False])
    # door_state = True
    payload = json.dumps({"open": door_state})
    try:
        publish.single(MQTT_TOPIC_DOOR, payload=payload, hostname=MQTT_BROKER, port=MQTT_PORT)
        logger.info(f"Scheduled: Published door state: {payload} to {MQTT_TOPIC_DOOR}")
    except Exception as e:
        logger.error(f"Scheduled: Error simulating door: {e}")

def simulate_owner_out():
    """Job to simulate owner state periodically."""
    owner_state = random.choice([True, False])
    # owner_state = True
    payload = json.dumps({"owner out": owner_state})
    try:
        publish.single(MQTT_TOPIC_OWNER, payload=payload, hostname=MQTT_BROKER, port=MQTT_PORT)
        logger.info(f"Scheduled: Published owner state: {payload} to {MQTT_TOPIC_OWNER}")
    except Exception as e:
        logger.error(f"Scheduled: Error simulating door: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(simulate_door_job, 'interval', minutes=5)  # Run every 5 minutes
scheduler.add_job(simulate_owner_out, 'interval', minutes=1)  # Run every 5 minutes

scheduler.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask webhook server on port {port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)  # Disable reloader to prevent scheduler duplication
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()