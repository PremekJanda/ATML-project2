document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('messageInput').focus();
    document.getElementById('questionForm').addEventListener('submit', function(event) {
        event.preventDefault(); 
        sendMessage();
    });
    changeResponseType();
});

document.getElementById('toggle').addEventListener("change", () => changeResponseType());

function changeResponseType() {
    fetch('/change_response', {
        method: 'POST',
        body: document.getElementById('toggle').checked,
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            log('Failed to toggle button');
        }
    })
    .catch(error => log('Error:', error));
}

function displayMessage(msg, type, is_audio=false) {
    var chatContainer = document.getElementById('chat-container');
    var newMessage = document.createElement("div");
    newMessage.classList.add("message", type)
    
    if (is_audio) {
        let strong = document.createElement("strong")
        strong.innerHTML = msg.user
        newMessage.appendChild(strong);
        newMessage.appendChild(msg.msg);
    } else {
        newMessage.innerHTML = '<strong>' + msg.user + '</strong> ' + `${msg.msg}`;
    }

    chatContainer.appendChild(newMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function createResponse(data) {
    document.getElementById('messageInput').value = "";

    if (document.getElementById('toggle').checked) {
        createAudio(data, "ChatBot", "response")
    } else {
        if (data.success) {
            displayMessage({'user': 'ChatBot', 'msg': data.message}, "response");
        } else {
            log('Failed to send message:', data.message);
        }
    }
}

function sendMessage() {
    var message = document.getElementById('messageInput').value.trim();

    if (message != "") {
        displayMessage({'user': 'User', 'msg': message}, "request");

        fetch('/send_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({'user': 'User', 'message': message}),
        })
        .then(response => document.getElementById('toggle').checked ? response.blob() : response.json())
        .then(data => createResponse(data))
        .catch(error => log('Error:', error));
    }
}

function sendAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);    
    formData.append('name', getNewId());

    fetch('/process_audio', {
        method: 'POST',
        body: formData
    })
    .then(response => document.getElementById('toggle').checked ? response.blob() : response.json())
    .then(data => createResponse(data))
    .catch(error => log('Error:', error));
}


let recording = document.getElementById("recording");
let startButton = document.getElementById("startButton");
let stopButton = document.getElementById("stopButton");
let downloadButton = document.getElementById("downloadButton");

function log(msg) {
    document.getElementById("log").innerHTML += `${msg}\n`;
}

function toggleButtons() {
  if (startButton.style.display == "none") {
    startButton.style.display = "inline-block"
    stopButton.style.display = "none"
  } else {
    stopButton.style.display = "inline-block"
    startButton.style.display = "none"
  }
}

function getNewId(start="audio-id-") {
    const elements = document.querySelectorAll('[id^="'+start+'"]');
    return start+elements.length;
}

function createAudio(recordedChunks, user="User", type="request") {
    const audioElement = document.createElement('audio');
    const audioBlob = (type == "request") ? new Blob(recordedChunks, { type: "audio/webm" }) : recordedChunks;
    audioElement.src = URL.createObjectURL(audioBlob);
    audioElement.controls = true;
    audioElement.id = getNewId();
    audioElement.download = audioElement.id + ".webm";
    msg = {'user': user, 'msg': audioElement};
    displayMessage(msg, type, is_audio=true);
    return audioBlob;
}

async function startRecording(stream) {
    let recorder = new MediaRecorder(stream);
    let data = [];

    recorder.ondataavailable = (event) => data.push(event.data);
    recorder.start();
    toggleButtons();

    let stopped = new Promise((resolve, reject) => {
        recorder.onstop = resolve;
        recorder.onerror = (event) => reject(event.name);
    });

    let recorded = new Promise(resolve => {
        stopButton.addEventListener("click", resolve, { once: true });
    })
    .then(() => {
        if (recorder.state === "recording") {
          recorder.stop();
          stop(recording.srcObject);
          toggleButtons();
        }
    });  

    await Promise.all([stopped, recorded]);
    return data;
}

function stop(stream) {
  stream.getTracks().forEach((track) => track.stop());
}

startButton.addEventListener("click", () => {
    navigator.mediaDevices
        .getUserMedia({
            video: false,
            audio: true,
        })
        .then((stream) => {
            recording.srcObject = stream;
            downloadButton.href = stream;
            recording.captureStream = recording.captureStream || recording.mozCaptureStream;
            return new Promise((resolve) => (recording.onplaying = resolve));
        })
        .then(() => startRecording(recording.captureStream()))
        .then((recordedChunks) => {
            const audioBlob = createAudio(recordedChunks);
            sendAudio(audioBlob);
        })
        .catch((error) => {
            if (error.name === "NotFoundError") {
                log("Microphone not found. Can't record.");
            } else {
                log(error);
            }
        });
  }, false,
);
