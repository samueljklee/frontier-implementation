from flask import Flask, request, jsonify
from urlFrontier import Frontier
import logging, sys

logging.basicConfig(level=logging.DEBUG, filename='frontier.log', filemode='w')
logger = logging.getLogger(__name__)
appFrontier = Frontier()
app = Flask(__name__)

@app.route('/api/v1/schedule', methods=['POST'])
def schedule():
    """ 
        Put message in frontier service through prioritizer
        
        Args: url, last_request_at, last_request_time, final_page, white_list

        Return: None
    """
    reqData = request.get_json()
    url = reqData['url']
    last_request_at = reqData['last_request_at']
    last_request_time = reqData['last_request_time']
    final_page = reqData['final_page']
    white_list = reqData['white_list']

    # Check for incorrect format
    if not isinstance(url, str) or not isinstance(last_request_at, int) \
            or not isinstance(last_request_time, int) or not isinstance(final_page, bool) or not isinstance(white_list, bool):
            payload = {
                'status': 'Incorrect format.'
            }
            logger.error(' Bad Request: Incorrect Format.')
            return jsonify(payload), 400
    
    try:
        response = appFrontier.prioritizer(url, last_request_at, last_request_time, final_page, white_list)
        if response:
            logger.info(' URL: {} successfully added into frontier.'.format(url))
            return jsonify(status='URL: {} successfully added into frontier.'.format(url)), 200
            
    except AssertionError as exception_message:
        logger.error(' {}'.format(exception_message))
        return jsonify(error='{}'.format(exception_message)), 400

@app.route('/api/v1/next', methods=['GET'])
def next():
    """ 
        Get the next message data
    
        Args: None

        Return: next message data with unique id
    """
    try:
        response = appFrontier.back_end_queue_selector()
        logger.info(' Next message data: {}'.format(response))
        return jsonify(response), 200

    except AssertionError as exception_message:
        return jsonify(error='{}'.format(exception_message)), 400

@app.route('/api/v1/commit', methods=['PUT'])
def commit():
    """ 
        Ack message resolved
        
        Args: id

        Return: message committed or not
    """
    reqData = request.get_json()
    
    try:
        response = appFrontier.commit_message(reqData['id'])
        return jsonify(response), 200

    except AssertionError as exception_message:
        return jsonify(status='Error {}'.format(exception_message)), 400

@app.route("/")
def welcome():
    return "Frontier"

@app.errorhandler(404)
def page_not_found(e):
    return "Page Not Found", 404

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')