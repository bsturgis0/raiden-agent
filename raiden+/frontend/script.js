document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const chatDisplay = document.getElementById('chat-display');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const uploadButton = document.getElementById('upload-button');
    const fileInput = document.getElementById('file-input');
    const statusIndicator = document.getElementById('status-indicator');
    const statusDot = statusIndicator.querySelector('.status-dot'); // Target dot directly if needed
    const statusText = statusIndicator.querySelector('.status-text');
    const typingIndicator = document.getElementById('typing-indicator');
    const modelSelect = document.getElementById('model-select');

    const confirmationModal = document.getElementById('confirmation-modal');
    const confirmationText = document.getElementById('confirmation-text');
    const confirmYesButton = document.getElementById('confirm-yes');
    const confirmNoButton = document.getElementById('confirm-no');

    // --- Configuration ---
    const API_BASE_URL = 'http://localhost:5000'; // Ensure this matches your FastAPI backend
    const CHAT_ENDPOINT = `${API_BASE_URL}/chat`;
    const CONFIRM_ENDPOINT = `${API_BASE_URL}/confirm`;
    const UPLOAD_ENDPOINT = `${API_BASE_URL}/upload`;
    const PING_ENDPOINT = `${API_BASE_URL}/ping`;

    // --- State ---
    let messageHistory = []; // Store message objects { role: 'user'/'assistant'/'tool'/'system', content: '...' }
    let isWaitingForResponse = false;
    let isWaitingForConfirmation = false;
    let currentActionData = null; // Store data for confirmation { prompt: ..., tool_name: ..., tool_args: ... }
    let selectedModel = modelSelect.value; // Default to the first option

    // Set default model to Groq
    modelSelect.value = 'groq-llama';
    selectedModel = 'groq-llama';

    // --- Function: Add Message to History & Display ---
    function addMessage(text, role, details = {}) {
        const messageData = { role, content: text, ...details };

        // Avoid adding duplicate system/error messages rapidly
        if (messageHistory.length > 0) {
            const lastMsg = messageHistory[messageHistory.length - 1];
            if (lastMsg.role === role && lastMsg.content === text && (role === 'system' || role === 'error')) {
                console.log("Skipping duplicate system/error message.");
                return; // Don't add or display duplicates
            }
        }

        messageHistory.push(messageData);
        displayMessage(messageData);
    }

    // --- Function: Display Message from Data ---
    function displayMessage(messageData) {
        const { role, content } = messageData;
        const messageDiv = document.createElement('div');
        const roleClassMap = { 'user': 'user', 'assistant': 'agent', 'ai': 'agent', 'tool': 'tool', 'system': 'system', 'error': 'error' };
        messageDiv.classList.add('message', `${roleClassMap[role] || 'agent'}-message`);

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');

        // Handle Python REPL output specially
        if (role === 'tool' && content.includes('Python REPL')) {
            // Parse and format Python output
            const output = content.replace('Python REPL Output:\n', '').trim();
            
            // Check if the output contains a plot file path
            const plotMatch = output.match(/Plot has been generated and saved as '(.+?)'/);
            if (plotMatch) {
                // Create plot image element
                const plotPath = plotMatch[1];
                const plotImg = document.createElement('img');
                plotImg.src = `/workspace/${plotPath}`; // Adjust path as needed
                plotImg.alt = 'Python Plot';
                plotImg.classList.add('python-plot');
                
                // Create output div for any text output
                const outputDiv = document.createElement('div');
                outputDiv.classList.add('python-repl-output');
                outputDiv.textContent = output.replace(plotMatch[0], '').trim();
                
                contentDiv.appendChild(outputDiv);
                contentDiv.appendChild(plotImg);
            } else {
                // Regular output without plot
                const outputDiv = document.createElement('div');
                outputDiv.classList.add('python-repl-output');
                // Check for error messages
                if (output.toLowerCase().includes('error')) {
                    outputDiv.classList.add('python-repl-error');
                }
                outputDiv.textContent = output;
                contentDiv.appendChild(outputDiv);
            }
        }
        // Handle other message types
        else {
            let processedContent = content
                .replace(/&/g, "&") // Escape HTML first
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");

            // Code blocks (```lang\n...\n``` or ```\n...\n```)
            processedContent = processedContent.replace(/```(\w*\n)?([\s\S]*?)```/g, (match, lang, code) => {
                const languageClass = lang ? `language-${lang.trim()}` : '';
                const escapedCode = code.replace(/</g, "<").replace(/>/g, ">").replace(/&/g, "&");
                return `<pre><code class="${languageClass}">${escapedCode}</code></pre>`;
            });
            // Inline code (`...`)
            processedContent = processedContent.replace(/`([^`]+)`/g, '<code>$1</code>');
            // Bold (**...**)
            processedContent = processedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            // Italic (*...*)
            processedContent = processedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
            // Links (simple URL detection)
            const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
            processedContent = processedContent.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
            // Newlines
            processedContent = processedContent.replace(/\n/g, '<br>');

            contentDiv.innerHTML = processedContent;
        }

        messageDiv.appendChild(contentDiv);
        chatDisplay.appendChild(messageDiv);

        // Scroll to bottom smoothly
        chatDisplay.scrollTo({ top: chatDisplay.scrollHeight, behavior: 'smooth' });
    }

    // --- Function: Set Status ---
    function setStatus(status, text) { // status: 'connected', 'error', 'pending', 'disconnected', 'connecting'
        statusIndicator.className = `status ${status}`; // Set class on parent
        statusText.textContent = text || status.charAt(0).toUpperCase() + status.slice(1);
    }

    // --- Function: Set Loading State ---
    function setLoadingState(isLoading) {
        isWaitingForResponse = isLoading;
        userInput.disabled = isLoading || isWaitingForConfirmation;
        sendButton.disabled = isLoading || isWaitingForConfirmation;
        uploadButton.disabled = isLoading || isWaitingForConfirmation; // Also disable upload during processing

        if (isLoading) {
            setStatus('pending', 'Raiden is thinking...');
            typingIndicator.classList.remove('hidden');
             userInput.placeholder = ""; // Clear placeholder when loading
        } else {
             // Status will be updated by health check or connection success/error
             // Set back to default placeholder only if not waiting for confirmation
            if (!isWaitingForConfirmation) {
                 userInput.placeholder = "Ask Raiden...";
                 checkBackendStatus(); // Update status indicator after loading stops
            }
            typingIndicator.classList.add('hidden');
            adjustTextareaHeight();
        }
    }

    // --- Function: Adjust Textarea Height ---
    function adjustTextareaHeight() {
        userInput.style.height = 'auto';
        let scrollHeight = userInput.scrollHeight;
        // Account for padding/border if needed, but box-sizing should handle it
        userInput.style.height = `${Math.min(scrollHeight, 140)}px`; // Use max-height from CSS
    }

    // --- Function: Send Chat Message ---
    async function sendChatMessage() {
        const messageText = userInput.value.trim();
        if (!messageText || isWaitingForResponse || isWaitingForConfirmation) {
            return;
        }

        addMessage(messageText, 'user'); // Add to history and display
        userInput.value = '';
        adjustTextareaHeight();
        setLoadingState(true);

        try {
            const response = await fetch(CHAT_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', },
                // Send the *entire* message history and selected model
                body: JSON.stringify({ messages: messageHistory, model: selectedModel }),
            });

            const data = await response.json(); // Always try to parse JSON

            if (!response.ok) {
                 // Use error detail from API response if available
                throw new Error(data.error || data.detail || `Server error: ${response.status}`);
            }

            handleApiResponse(data);

        } catch (error) {
            console.error('Chat Error:', error);
            addMessage(`Error: ${error.message}`, 'error');
            setStatus('error', 'Connection Issue');
        } finally {
             // Only stop loading if NOT waiting for confirmation
             if (!isWaitingForConfirmation) {
                 setLoadingState(false);
             }
        }
    }

    // --- Function: Handle API Response (Chat & Confirm) ---
    function handleApiResponse(data) {
         if (data.error) {
             console.error("API Error:", data.error);
             addMessage(`API Error: ${data.error}`, 'error');
             setStatus('error', 'API Error');
             return;
         }

         // Add any messages received from the backend
         if (data.messages && Array.isArray(data.messages)) {
             data.messages.forEach(msg => {
                 // Convert role back if needed (e.g., 'ai' -> 'assistant')
                 const role = msg.role === 'ai' ? 'assistant' : msg.role;
                 // Pass tool call info if present
                 const details = msg.tool_calls ? { tool_calls: msg.tool_calls } : {};
                  // Add name if it's a tool message result
                 if(role === 'tool' && msg.name) { details.name = msg.name; }
                 addMessage(msg.content, role, details);
             });
         }

         // Check if confirmation is required
         if (data.requires_confirmation) {
             showConfirmationModal(
                 data.requires_confirmation.prompt,
                 data.requires_confirmation // Pass the whole object as actionDetails
             );
             // Keep loading state true because we are waiting for user interaction
             setLoadingState(true); // Explicitly keep loading appearance
             setStatus('pending', 'Confirmation Required'); // Update status text
         } else {
              // If no confirmation needed, ensure loading state is off
              setLoadingState(false);
         }
    }


    // --- Function: Send Confirmation ---
    async function sendConfirmation(confirmed) {
        if (!currentActionData) return;

        hideConfirmationModal();
        setLoadingState(true); // Show loading while processing confirmation

        // Display user's choice immediately
        addMessage(`User ${confirmed ? 'CONFIRMED' : 'CANCELED'} action: '${currentActionData.prompt}'`, 'system');


        try {
            const response = await fetch(CONFIRM_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    confirmed: confirmed,
                    action_details: currentActionData
                }),
            });

            const data = await response.json();

             if (!response.ok) {
                throw new Error(data.error || data.detail || `Server error: ${response.status}`);
            }

            handleApiResponse(data); // Process messages/errors from confirmation

        } catch (error) {
            console.error('Confirmation Error:', error);
            addMessage(`Error processing confirmation: ${error.message}`, 'error');
            setStatus('error', 'Confirmation Error');
             setLoadingState(false); // Ensure loading stops on error here
        } finally {
             currentActionData = null;
             // Loading state is turned off by handleApiResponse if successful,
             // or by the catch block if there's an error.
        }
    }

    // --- Function: Upload Image ---
    async function uploadImage(file) {
        if (!file) return;

        setLoadingState(true);
        addMessage(`Uploading ${file.name}...`, 'system');

        const formData = new FormData();
        formData.append('file', file);

        try {
             const response = await fetch(UPLOAD_ENDPOINT, {
                 method: 'POST',
                 body: formData,
                 // 'Content-Type' header is set automatically by browser for FormData
             });

             const data = await response.json(); // Expecting ApiResponse format

              if (!response.ok) {
                 throw new Error(data.error || data.detail || `Server error: ${response.status}`);
             }

             handleApiResponse(data); // Display message from backend (e.g., "File uploaded as...")

        } catch (error) {
             console.error('Upload Error:', error);
             addMessage(`Upload failed: ${error.message}`, 'error');
             setStatus('error', 'Upload Failed');
        } finally {
            setLoadingState(false);
            fileInput.value = ''; // Reset file input
        }
    }


    // --- Function: Show Confirmation Modal ---
    function showConfirmationModal(prompt, actionDetails) {
        confirmationText.textContent = prompt || "Do you want to proceed?";
        currentActionData = actionDetails;
        isWaitingForConfirmation = true; // Set confirmation flag
        confirmationModal.classList.remove('hidden');
        confirmYesButton.focus();
        // setLoadingState(true) should already be active or set by caller
        setStatus('pending', 'Confirmation Required');
    }

    // --- Function: Hide Confirmation Modal ---
    function hideConfirmationModal() {
        isWaitingForConfirmation = false; // Clear flag
        confirmationModal.classList.add('hidden');
        // Don't clear currentActionData here, sendConfirmation needs it
    }

    // --- Function: Health Check ---
    let isConnected = false; // Track connection state
    async function checkBackendStatus() {
         // Don't ping if waiting for response or confirmation
        if (isWaitingForResponse || isWaitingForConfirmation) return;

        try {
            const response = await fetch(PING_ENDPOINT, { method: 'GET', signal: AbortSignal.timeout(5000) }); // 5s timeout
            if (response.ok) {
                 if (!isConnected) { // First successful connection or reconnection
                     addMessage("Connected to Raiden backend.", "system");
                     isConnected = true;
                 }
                 setStatus('connected', 'Ready');
            } else {
                 if (isConnected) { // Lost connection
                     addMessage("Connection to backend lost.", "error");
                     isConnected = false;
                 }
                 setStatus('error', 'Server Issue');
            }
        } catch (error) {
            if (isConnected) { // Lost connection
                 addMessage("Connection error.", "error");
                 isConnected = false;
             }
             setStatus('disconnected', 'Offline');
             console.warn("Ping failed:", error.name === 'AbortError' ? 'Timeout' : error);
        }
    }

    // --- Event Listeners ---
    sendButton.addEventListener('click', sendChatMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    userInput.addEventListener('input', adjustTextareaHeight);

    uploadButton.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
             uploadImage(e.target.files[0]);
         }
    });

    modelSelect.addEventListener('change', () => {
        selectedModel = modelSelect.value;
        addMessage(`Model switched to: ${selectedModel.replace('-', ' ')}`, 'system');
    });

    confirmYesButton.addEventListener('click', () => sendConfirmation(true));
    confirmNoButton.addEventListener('click', () => sendConfirmation(false));

    // Optional: Close modal on overlay click (acts as cancel)
    confirmationModal.addEventListener('click', (e) => {
         if (e.target === confirmationModal && !isWaitingForResponse) { // Prevent closing if processing confirm response
             sendConfirmation(false);
         }
     });


    // --- Initial Setup ---
    setStatus('connecting', 'Connecting...');
    adjustTextareaHeight();
    setLoadingState(false); // Start interactive

    // Initial health check slightly delayed
    setTimeout(checkBackendStatus, 1000);
    // Periodic health check
    setInterval(checkBackendStatus, 20000); // Check every 20 seconds

    // Add initial system message to history
    addMessage("Initializing Raiden Interface... Awaiting backend connection.", "system");

});