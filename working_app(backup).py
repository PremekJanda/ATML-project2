import os, librosa, audioread, uuid, wave
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
from flask import Flask, render_template, jsonify, send_file, url_for
from flask import Flask, request, session
from scipy.io.wavfile import read
from scipy.io.wavfile import write
import torch
from pyngrok import ngrok, conf
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
from sentence_transformers import SentenceTransformer, CrossEncoder
import threading
import whisper
import json
import pickle
import hnswlib
from transformers import T5Tokenizer, T5ForConditionalGeneration

app = Flask(__name__, static_url_path='/static')

audioread.ffdec.FFmpegAudioFile = audioread.ffdec.FFmpegAudioFile

app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'static/audio'
# True == "speech", False == "text"
app.config['RESPONSE_TYPE'] = False

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
    question: str = content.get('message', '')
    
    #### THIS IS WHERE MAGIC HAPPENS ###
    # TODO create answer

    ### HERE MAGIC HAPPENS ###
    # answer in speech
    if app.config['RESPONSE_TYPE']:
        # TODO convert text to speech
        audio_numpy, rate = text2speech(question)

        write("./static/audio/audio.wav", rate, audio_numpy)

        # Send the processed audio file back to the client
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], "./audio.wav"), as_attachment=True) # TODO change
    # answer in text
    else:
        semb_model, index, xenc_model, model, tokenizer, device = load_qa_pipeline()
        pairs, unique_contexts = read_data()
        message = qa_pipeline(question, unique_contexts, semb_model, index, xenc_model, model,tokenizer, device)
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
      
      audio = AudioSegment.from_file(audio_file_path)
      
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
          message = speech2text(audio_file_path)
          return jsonify({'success': True, 'message': message})
            
def text2speech(input):
  rate = 22050
  # Transform the text to numeric sequence
  sequences, lengths = utils.prepare_input_sequence([input])

  # Use tacotron2 model to create a mel spectrogram from the numeric sequence
  
  with torch.no_grad():
      mel, _, _ = tacotron2.infer(sequences, lengths)
  
  # Use the waveglow model to produce audio signal from the mel spectrogram
  with torch.no_grad():
      audio = waveglow.infer(mel)
  
  # return the audio signal
  audio_numpy = audio[0].data.cpu().numpy()
  
  return audio_numpy, rate

def speech2text(audio_path):
  model = whisper.load_model("base")

  result = model.transcribe(audio_path)
  return result["text"]


def qa_pipeline(
    question, 
    unique_contexts,
    similarity_model,
    embeddings_index,
    re_ranking_model,
    generative_model,
    tokenizer,
    device
):
    if not question.endswith('?'):
        question = question + '?'
    # Embed question
    question_embedding = similarity_model.encode(question, convert_to_tensor=True)
    # Search documents similar to question in index
    corpus_ids, distances = embeddings_index.knn_query(question_embedding.cpu(), k=64)
    # Re-rank results
    xenc_model_inputs = [(question, unique_contexts[idx]) for idx in corpus_ids[0]]
    cross_scores = re_ranking_model.predict(xenc_model_inputs)
    # Get best matching passage
    passage_idx = np.argsort(-cross_scores)[0]
    passage = unique_contexts[corpus_ids[0][passage_idx]]
    # Encode input
    input_text = f"Given the following passage, answer the related question.\n\nPassage:\n\n{passage}\n\nQ: {question}"

    input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(device)
    # Generate output
    output_ids = generative_model.generate(input_ids, max_new_tokens=512)
    # Decode output
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # Return result
    return output_text


def read_data():
  file_path = './train-v2.0.json'
  with open(file_path, 'rb') as f:
      # Load the data
      data_dict = json.load(f)

  unique_contexts = []
  contexts = []
  pairs = []
  for category in data_dict["data"]:
      for passage in category["paragraphs"]:
          context = passage["context"]
          unique_contexts.append(context)
          for qa in passage["qas"]:
              question = qa["question"]
              for answer in qa["answers"]:
                  pairs.append([question, answer])
                  contexts.append(context)
  return pairs, contexts


def load_qa_pipeline():

  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')    
  semb_model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
  xenc_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

  pairs, unique_contexts = read_data()

  tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
  model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large", device_map="auto", torch_dtype=torch.float16)

  # Define hnswlib index path
  embeddings_cache_path = './qa_embeddings_cache.pkl'

  # Load cache if available
  if os.path.exists(embeddings_cache_path):
      print('Loading embeddings cache')
      with open(embeddings_cache_path, 'rb') as f:
          corpus_embeddings = pickle.load(f)
  # Else compute embeddings
  else:
      print('Computing embeddings')
      corpus_embeddings = semb_model.encode(unique_contexts, convert_to_tensor=True, show_progress_bar=True)
      # Save the index to a file for future loading
      print(f'Saving index to: \'{embeddings_cache_path}\'')
      with open(embeddings_cache_path, 'wb') as f:
          pickle.dump(corpus_embeddings, f)

  # Create empthy index
  index = hnswlib.Index(space='cosine', dim=corpus_embeddings.size(1))

  # Define hnswlib index path
  index_path = './qa_hnswlib_100.index'

  # Load index if available
  if os.path.exists(index_path):
      print('Loading index...')
      index.load_index(index_path)
  # Else index data collection
  else:
      # Initialise the index
      print('Start creating HNSWLIB index')
      index.init_index(max_elements=corpus_embeddings.size(0), ef_construction=100, M=64) # see https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md for parameter description
      # Compute the HNSWLIB index (it may take a while)
      index.add_items(corpus_embeddings.cpu(), list(range(len(corpus_embeddings))))
      # Save the index to a file for future loading
      print(f'Saving index to: {index_path}')
      index.save_index(index_path)

  return semb_model, index, xenc_model, model, tokenizer, device

        
if __name__ == '__main__':
    # Load tacotron
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')    
    if (str(device) != 'cpu'):
        tacotron2 = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_tacotron2', model_math='fp16')
        tacotron2 = tacotron2.to('cuda')
        tacotron2.eval()

        # Load waveglow
        waveglow = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_waveglow', model_math='fp16')
        waveglow = waveglow.remove_weightnorm(waveglow)
        waveglow = waveglow.to('cuda')
        waveglow.eval()

        # Load utils
        utils = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_tts_utils')
        
    # Set the ngrok API key (You can sign up at https://dashboard.ngrok.com/signup)
    ngrok.set_auth_token("2aqbGWfalvm3IkbsBxv0EPy5mXf_516D8P9TMEv4w6a12AW1g")

    # Open a ngrok tunnel to the Flask-SocketIO app
    public_url = ngrok.connect(5000, bind_tls=True)
    print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:5000\"".format(public_url))

    # Run the Flask-SocketIO app
    threading.Thread(target=app.run, kwargs={"use_reloader": False}).start()

