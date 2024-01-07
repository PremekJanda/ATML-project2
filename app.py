import os, librosa, audioread, uuid, wave
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
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(msg):
    socketio.emit('message', msg)
    
@app.route('/send_response', methods=['POST'])
def send_response():
    content = request.json
    user = content.get('user', 'User')
    message: str = content.get('message', '')
    
    #### THIS IS WHERE MAGIC HAPPENS ###
    print(message)

    if message:
        socketio.emit('message', {'user': user, 'msg': message})
        return jsonify({'success': True, 'message': message.upper()})
    else:
        return jsonify({'success': False, 'message': message.upper()})

@app.route('/process_audio', methods=['POST'])
def process_audio():
     # Check if the POST request has a file part
    if 'audio' not in request.files:
        return 'No audio file provided', 400

    audio_file = request.files['audio']
    print(request.form['name'])

    if audio_file:
        # Save the uploaded audio file
        audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"input-{request.form['name']}.webm")
        audio_file.save(audio_file_path)

        # Load the audio file using pydub
        # audio = librosa.load(audio_file_path, sr=48000)
        # audio = librosa.load(audio_file_path)
        audio = read(audio_file_path)
        # audio = AudioSegment.from_wav(audio_file_path)

        # Perform some processing (e.g., noise removal)
        processed_audio = normalize(audio)

        # Save the processed audio file
        processed_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"processed-{request.form['name']}.webm")
        processed_audio.export(processed_audio_path, format='wav')

        # Send the processed audio file back to the client
        return send_file(processed_audio_path, as_attachment=True)

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
