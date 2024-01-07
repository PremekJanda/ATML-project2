document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('messageInput').focus();
    document.getElementById('questionForm').addEventListener('submit', function(event) {
        event.preventDefault();
        
        sendMessage();
    });
    
});

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

function sendMessage() {
    var messageInput = document.getElementById('messageInput');
    var message = messageInput.value.trim();

    displayMessage({'user': 'User', 'msg': message}, "request");

    if (message !== '') {
        fetch('/send_response', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({'user': 'User', 'message': message}),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayMessage({'user': 'ChatBot', 'msg': data.message}, "response");
                messageInput.value = '';
            } else {
                console.error('Failed to send message:', data.message);
            }
        })
        .catch(error => console.error('Error:', error));
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
    .then(response => response.blob())
    .then(blob => {
        // processedAudio.src = URL.createObjectURL(blob);
        createAudio(blob, "ChatBot", "response")
    })
    .catch(error => console.error('Error:', error));
}


let preview = document.getElementById("preview");
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
    const audioBlob = new Blob(recordedChunks, { type: "audio/webm" })
    audioElement.src = URL.createObjectURL(audioBlob);
    audioElement.controls = true;
    audioElement.id = getNewId();
    audioElement.download = audioElement.id + ".webm";
    msg = {'user': user, 'msg': audioElement};
    displayMessage(msg, type, is_audio=true);
    return audioBlob;
}

// function createAudio(recordedChunks, user="User", type="request") {
//     const audioElement = document.createElement('audio');
//     const audioBlob = recordedChunks
//     audioElement.src = URL.createObjectURL(recordedChunks);
//     audioElement.controls = true;
//     audioElement.id = getNewId();
//     audioElement.download = audioElement.id + ".webm";
//     msg = {'user': user, 'msg': audioElement};
//     displayMessage(msg, type, is_audio=true);
//     return audioBlob;
// }

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
          stop(preview.srcObject);
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
            preview.srcObject = stream;
            downloadButton.href = stream;
            preview.captureStream = preview.captureStream || preview.mozCaptureStream;
            return new Promise((resolve) => (preview.onplaying = resolve));
        })
        .then(() => startRecording(preview.captureStream()))
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

// startButton.addEventListener("click", () => {
//     navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
//         // Collection for recorded data.
//         let data = [];
      
//         // Recorder instance using the stream.
//         // Also set the stream as the src for the audio element.
//         const recorder = new MediaRecorder(stream);
//         preview.srcObject = stream;
//         recording.srcObject = stream;
      
//         recorder.addEventListener('start', e => {
//           // Empty the collection when starting recording.
//           data.length = 0;
//         });
      
//         recorder.addEventListener('dataavailable', event => {
//           // Push recorded data to collection.
//           data.push(event.data);
//         });
      
//         // Create a Blob when recording has stopped.
//         recorder.addEventListener('stop', () => {
//           const blob = new Blob(data, {
//             'type': 'audio/mp3'
//           });
//           sendAudio(blob);
//         });
      
//         // Start the recording.
//         // recorder.start();
//       });
// })

// stopButton.addEventListener("click", () => {
//         stop(preview.srcObject);
//         toggleButtons();
//     }, false,
// );






// ! 2
// let mediaRecorder;
// let audioChunks = [];
// let audioBlob;

// const startRecordButton = document.getElementById('startRecord');
// const stopRecordButton = document.getElementById('stopRecord');
// const sendToServerButton = document.getElementById('sendToServer');
// const audioPlayer = document.getElementById('audioPlayer');

// navigator.mediaDevices.getUserMedia({ audio: true })
//     .then(stream => {
//         mediaRecorder = new MediaRecorder(stream);

//         mediaRecorder.ondataavailable = event => {
//             if (event.data.size > 0) {
//                 audioChunks.push(event.data);
//             }
//         };

//         mediaRecorder.onstop = () => {
//             audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
//             const audioUrl = URL.createObjectURL(audioBlob);

//             audioPlayer.src = audioUrl;
//             audioPlayer.controls = true;

//             sendToServerButton.disabled = false;
//         };

//         startRecordButton.addEventListener('click', () => {
//             mediaRecorder.start();
//             startRecordButton.disabled = true;
//             stopRecordButton.disabled = false;
//         });

//         stopRecordButton.addEventListener('click', () => {
//             mediaRecorder.stop();
//             startRecordButton.disabled = false;
//             stopRecordButton.disabled = true;
//         });

//         sendToServerButton.addEventListener('click', () => {
//             const formData = new FormData();
//             // formData.append('audio', new File(audioChunks, 'recorded_audio.wav'));
//             formData.append('audio', audioBlob);

//             fetch('/process_audio', {
//                 method: 'POST',
//                 body: formData
//             })
//             .then(response => response.blob())
//             .then(blob => {
//                 const processedAudioUrl = URL.createObjectURL(blob);
//                 audioPlayer.src = processedAudioUrl;
//                 audioPlayer.controls = true;
//             })
//             .catch(error => console.error('Error:', error));
//         });
//     })
//     .catch(error => console.error('Error accessing microphone:', error));




// ! 3
// let mediaRecorder;
// let audioChunks = [];
// let audioBlob;

// const startRecordButton = document.getElementById('startRecord');
// const stopRecordButton = document.getElementById('stopRecord');
// const sendToServerButton = document.getElementById('sendToServer');
// const audioPlayer = document.getElementById('audioPlayer');
// var base64data = 0;
// var reader;
// var recorder, gumStream;
// var recordButton = my_btn;
// reader = new FileReader();
// reader.readAsDataURL(e.data); 
// reader.onloadend = function() {
//     base64data = reader.result;
//     //console.log("Inside FileReader:" + base64data);
// }

// navigator.mediaDevices.getUserMedia({ audio: true })
//     .then(stream => {
//         mediaRecorder = new MediaRecorder(stream);

//         mediaRecorder.ondataavailable = event => {
//             if (event.data.size > 0) {
//                 audioChunks.push(event.data);
//             }
//         };

//         mediaRecorder.onstop = () => {
//             audioBlob = new Blob(audioChunks, { type: 'audio/mp3' });
//             const audioUrl = URL.createObjectURL(audioBlob);

//             audioPlayer.src = audioUrl;
//             audioPlayer.controls = true;

//             sendToServerButton.disabled = false;
//         };

//         startRecordButton.addEventListener('click', () => {
//             mediaRecorder.start();
//             startRecordButton.disabled = true;
//             stopRecordButton.disabled = false;
//         });

//         stopRecordButton.addEventListener('click', () => {
//             mediaRecorder.stop();
//             startRecordButton.disabled = false;
//             stopRecordButton.disabled = true;
//         });

//         sendToServerButton.addEventListener('click', () => {
//             const formData = new FormData();
//             // formData.append('audio', new File(audioChunks, 'recorded_audio.wav'));
//             formData.append('audio', audioBlob);

//             fetch('/process_audio', {
//                 method: 'POST',
//                 body: formData
//             })
//             .then(response => response.blob())
//             .then(blob => {
//                 const processedAudioUrl = URL.createObjectURL(blob);
//                 audioPlayer.src = processedAudioUrl;
//                 audioPlayer.controls = true;
//             })
//             .catch(error => console.error('Error:', error));
//         });
//     })
//     .catch(error => console.error('Error accessing microphone:', error));