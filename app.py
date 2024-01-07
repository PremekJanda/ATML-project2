import os, librosa, audioread, uuid, wave
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from flask import Flask, render_template, jsonify, send_file, url_for
from flask import Flask, request, session
from flask_socketio import SocketIO, emit
from scipy.io.wavfile import read

audioread.ffdec.FFmpegAudioFile = audioread.ffdec.FFmpegAudioFile

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'static/audio'
# True == "speech", False == "text"
app.config['RESPONSE_TYPE'] = False
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

# @socketio.on('message')
# def handle_message(msg):
#     socketio.emit('message', msg)    

@app.route('/change_response', methods=['POST'])
def change_response():
    if request.data.decode() == "true":
        app.config['RESPONSE_TYPE'] = True
    else:
        app.config['RESPONSE_TYPE'] = False
        
    return jsonify({'success': True, 'message': app.config['RESPONSE_TYPE']})

    
@app.route('/send_response', methods=['POST'])
def send_response():
    content = request.json
    user = content.get('user', 'User')
    message: str = content.get('message', '')
    
    #### THIS IS WHERE MAGIC HAPPENS ###
    # TODO create answer
    message = message.upper()

    ### HERE MAGIC HAPPENS ###
    # answer in speech
    if app.config['RESPONSE_TYPE']:
        # TODO convert text to speech

        # Send the processed audio file back to the client
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "input-audio-id-1.webm"), as_attachment=True) # TODO change
    # answer in text
    else:        
        return jsonify({'success': True, 'message': message})

@app.route('/process_audio', methods=['POST'])
def process_audio():
     # Check if the POST request has a file part
    if 'audio' not in request.files:
        return 'No audio file provided', 400

    audio_file = request.files['audio']

    if audio_file:
        # Save the uploaded audio file
        audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"input-{request.form['name']}.webm")
        audio_file.save(audio_file_path)
        
        audio = AudioSegment.from_file(audio_file_path, format='webm')
        
        audio_array = np.array(audio.get_array_of_samples())
        
        ### TODO convert speech to text ###
        
        message = "response in text".upper() # TODO remove
        
        # answer in speech
        if app.config['RESPONSE_TYPE']:
            # TODO create audio fron the answer
            # Perform some processing (e.g., noise removal)
            processed_audio = normalize(audio)

            # Save the processed audio file
            processed_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"processed-{request.form['name']}.webm")
            # processed_audio.export(processed_audio_path, format='wav')
            processed_audio.export(processed_audio_path, format='webm')

            # Send the processed audio file back to the client
            return send_file(processed_audio_path, as_attachment=True)
        # answer in text
        else:
            return jsonify({'success': True, 'message': message})
            
            
            
        
    

# # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

# @app.route('/process_audio', methods=['POST'])
# def process_audio():
#     audio_file = request.files['audio']

#     if audio_file:
#         # audio = AudioSegment.from_file(audio_file, format='wav')
#         # audio = librosa.load(audio_file)
#         # audio = read(audio_file)
#         print(audio_file)
#         # with open("", "r") as f:
#         #     f.read()
#         # try:
#         audio = AudioSegment.from_file(audio_file.read(), format='webm')
#         audio.export("output.wav", format="wav")
#         print(audio)

#         # Perform noise removal (you can customize this step)
#         processed_audio = normalize(audio)

#         # Save the processed audio file
#         processed_audio_path = 'static/processed_audio.wav'
#         processed_audio.export(processed_audio_path, format='wav')
        
#         # Send the processed audio file back to the client
#         return send_file(processed_audio_path, as_attachment=True)
#         # except Exception as e:
#         #     print(f"Error: {e}")

#         # return send_file(audio_file, 
#         #                  as_attachment=True, 
#         #                  mimetype=audio_file.mimetype,
#         #                  download_name=audio_file.name)



if __name__ == '__main__':
    socketio.run(app, debug=True)
