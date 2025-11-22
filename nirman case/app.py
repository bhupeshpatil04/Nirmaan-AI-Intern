from flask import Flask, render_template, request, jsonify
from scorer import score_transcript
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/score', methods=['POST'])
def score():
    data = request.json
    transcript = data.get('transcript','')
    rubric = None
    if data.get('rubric'):
        rubric = data.get('rubric')
    result = score_transcript(transcript, rubric=rubric)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')
