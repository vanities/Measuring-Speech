# imports
import os
import uuid
import utils

import werkzeug
from utils import logger
from flask import Flask, request
from analyzer import voice_analyzer
from flask_restful import Resource, Api, reqparse


# Instance of application
class SoundCount(Resource):

    """
    An instance of the SoundCount app
    POST: receive a WAV file to process.
    file: the file field.
    """

    def post(self):
        logger.info("POST Request received.")


        # Create a temp file, assume bad result.
        payload = {'status': 'failure',
                   'count': 0,
                   'meta': {}}

        # Parse the request into a dict() which contains the raw wav data.
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()

        # Save the data as a temporary file
        filename = str(uuid.uuid4())
        audio_file = args['file']
        audio_file.save(filename)

        logger.info("Analyzing temp file.")
        # Extract the words and perform an analysis.
        try:
            words = utils.speech_rec(filename)
            analysis = voice_analyzer(filename)
        except:
            logger.error("File uploaded does not appear to be an wav file")
            os.remove(filename)
            logger.debug("temp file removed.  Was {0}".format(filename))
            return payload

        # Tag the words
        payload['meta']['text'] = utils.pos_tagger([words['meta']['text']])
        payload['meta']['gender'] = analysis['gender']
        payload['meta']['age'] = analysis['age']
        payload['meta']['dialect'] = analysis['dialect']

        # Count the words
        for word in payload['meta']['text']:
            payload['count'] += len(word)

        duration = utils.duration(filename)

        # Check for errors
        if 'error' not in payload:
            payload['status'] = 'success'
            payload['meta']['duration'] = duration

        logger.info("Analysis complete {count} WORDs, {gen} GENDER,{dur} seconds".format(
            count=payload['count'],
            gen="NYI",
            dur="%6.2f" % duration))

        # Remove temp file
        os.remove(filename)
        logger.debug("temp file removed.  Was {0}".format(filename))
        return payload


logger.debug('Starting flask app.')

# Create the app and resource (root)
app = Flask(__name__)
api = Api(app)

api.add_resource(SoundCount, '/')
if __name__ == '__main__':
    app.run(debug=True)
