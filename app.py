from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'secret!'
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
    message = content.get('message', '')
    
    #### THIS IS WHERE MAGIC HAPPENS
    print(message)

    if message:
        socketio.emit('message', {'user': user, 'msg': message})
        return jsonify({'success': True, 'message': 'Message sent successfully'})
    else:
        return jsonify({'success': False, 'message': 'Message cannot be empty'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
