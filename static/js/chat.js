const API_KEY = 'AIzaSyCv9KO5acAkV2_T1p9PKVNJSrmeswE8_AA';  // Use your actual API key here
let chatHistory = [];  // Store the chat history

// Function to toggle the chat box
function toggleChatBox() {
    console.log("Toggling chat box...");
    const chatBoxExpanded = document.getElementById('chat-box-expanded');
    chatBoxExpanded.classList.toggle('active');

    // When expanding, send user data to the API and get a welcome message
    if (chatBoxExpanded.classList.contains('active')) {
        console.log("Chat box expanded, sending welcome message...");
        sendWelcomeMessage();
    } else {
        console.log("Chat box collapsed.");
    }
}

// Function to send the user's data to the API and receive a welcome message
function sendWelcomeMessage() {
    const userName = 'User'; // Replace with actual user data (e.g., from session or form)
    console.log(`Sending welcome message for user: ${userName}`);

    // Send a request to the API to get a welcome message
    fetch('https://api.gemini.com/v1/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({
            prompt: `Welcome, ${userName}.`,  // Customize the prompt as needed
            max_tokens: 150
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Received response:", data);
        appendMessage(`NitiSense: ${data.response.text}`);
    })
    .catch(error => {
        console.error('Error sending welcome message:', error);
    });
}

// Function to send the user's message to the API and get a response
function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    const chatBox = document.getElementById('chat-box');

    if (userInput.trim() !== '') {
        console.log(`Sending message: ${userInput}`);
        appendMessage(`You: ${userInput}`);
        document.getElementById('user-input').value = ''; // Clear input field

        // Add user message to history
        chatHistory.push(`You: ${userInput}`);
        console.log("Updated chat history:", chatHistory);

        // Send the chat history and current message to the API
        fetch('https://api.gemini.com/v1/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`,
            },
            body: JSON.stringify({
                prompt: buildChatHistory(),
                max_tokens: 150
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Received AI response:", data);
            appendMessage(`NitiSense: ${data.response.text}`);
            // Add AI's response to history
            chatHistory.push(`NitiSense: ${data.response.text}`);
        })
        .catch(error => {
            console.error('Error sending message:', error);
        });
    } else {
        console.log("User input is empty, not sending.");
    }
}

// Function to build the chat history into a string
function buildChatHistory() {
    console.log("Building chat history...");
    return chatHistory.join(" ");
}

// Function to append the message to the chat box
function appendMessage(message) {
    console.log(`Appending message: ${message}`);
    const chatBox = document.getElementById('chat-box');
    const newMessage = document.createElement('p');
    newMessage.textContent = message;
    chatBox.appendChild(newMessage);
    chatBox.scrollTop = chatBox.scrollHeight;
}