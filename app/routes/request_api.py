import uuid
from datetime import datetime, timedelta
from flask import jsonify, abort, request, Blueprint

from validate_email import validate_email
REQUEST_API = Blueprint('request_api', __name__)


def get_blueprint():
    """Return the blueprint for the main app module"""
    return REQUEST_API


BOOK_REQUESTS = {
    "8c36e86c-13b9-4102-a44f-646015dfd981": {
        'title': u'Good Book',
        'email': u'testuser1@test.com',
        'timestamp': (datetime.today() - timedelta(1)).timestamp()
    },
    "04cfc704-acb2-40af-a8d3-4611fab54ada": {
        'title': u'Bad Book',
        'email': u'testuser2@test.com',
        'timestamp': (datetime.today() - timedelta(2)).timestamp()
    }
}


@REQUEST_API.route('/request', methods=['GET'])
def get_records():
    """Return all book requests
    @return: 200: an array of all known BOOK_REQUESTS as a \
    flask/response object with application/json mimetype.
    """
    return jsonify(BOOK_REQUESTS)
