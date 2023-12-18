console.log("js loaded");

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('messageInput').focus();
    document.getElementById('questionForm').addEventListener('submit', function(event) {
        event.preventDefault();
        
        sendMessage();
    });
    
});

function displayMessage(msg, type) {
    var chatContainer = document.getElementById('chat-container');
    var newMessage = document.createElement("div");
    
    if (type == "request") {

    } else if (type == "response") {
        
    }
    newMessage.classList.add("message", type)
    newMessage.innerHTML = '<strong>' + msg.user + ':</strong> ' + msg.msg;
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
                displayMessage({'user': 'User', 'msg': message}, "response");
                messageInput.value = '';
            } else {
                console.error('Failed to send message:', data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}