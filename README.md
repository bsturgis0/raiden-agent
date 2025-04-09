# 🌟 Raiden+ Desktop Application

Raiden+ is an advanced AI-powered assistant designed to provide seamless interaction and assistance. With its futuristic interface and robust backend, Raiden+ bridges the gap between human-like conversational AI and powerful computational tools.

---

## 🚀 Features

### 🤖 AI-Powered Assistance
- **Dynamic Model Selection**: Choose from multiple AI models (Google Gemini, Groq Llama, Together Llama, DeepSeek Chat) to suit your needs.
- **Natural Conversations**: Engage in human-like dialogue with Raiden+.
- **Emotionally Intelligent Responses**: Raiden+ adapts its tone based on the context of the conversation.

### 🛠️ Integrated Tools
- **File Management**: Read and list files securely within the workspace.
- **GitHub Integration**: Access repositories, list contents, and fetch file data.
- **Image Analysis**: Leverage AWS Rekognition for object detection, text recognition, and more.
- **Email Drafting**: Compose professional emails effortlessly.
- **Mathematical Calculations**: Perform complex computations with ease.

### 🌐 Web Search
- **Brave Search**: Perform web searches using Brave's API.
- **Tavily Search**: Advanced search capabilities with detailed results.

### 🔒 Secure Operations
- **Confirmation Workflow**: Sensitive actions like file deletion or email sending require explicit user confirmation.

---

## 🖥️ User Interface

### Sidebar
- **Model Selector**: Easily switch between AI models.
- **Connection Status**: Real-time status indicator for backend connectivity.

### Chat Interface
- **Dynamic Conversations**: Engage with Raiden+ in a sleek, futuristic chat interface.
- **Typing Indicator**: Visual feedback when Raiden+ is processing your request.
- **File Upload**: Drag and drop images for analysis.

### Confirmation Modal
- **Action Verification**: Confirm or cancel sensitive actions with a clean, intuitive modal.

---

## 🛠️ Installation

### Prerequisites
- **Python 3.9+**
- **Node.js (Optional)**: For frontend development.
- **AWS Credentials**: Required for image analysis tools.

### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/raiden-agent.git
   cd raiden-agent
   ```
2. Install dependencies:
   ```bash
   pip install -r raiden+/requirements.txt
   ```
3. Configure environment variables:
   - Create a `.env` file in the `raiden+` directory.
   - Add your API keys and credentials (refer to the provided `.env` template).

4. Start the backend server:
   ```bash
   python raiden+/app.py
   ```

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd raiden+/frontend
   ```
2. Open `index.html` in your browser to launch the app.

---

## 🧩 Architecture

### Backend
- **Framework**: FastAPI
- **LLM Integration**: Supports multiple AI models via LangChain.
- **Tooling**: AWS Rekognition, GitHub API, Brave Search API, and more.

### Frontend
- **HTML/CSS/JavaScript**: A futuristic, responsive UI.
- **Dynamic Model Selection**: Switch AI models directly from the interface.

---

## 📖 Usage

1. Start the backend server.
2. Open the frontend in your browser.
3. Select an AI model from the sidebar.
4. Interact with Raiden+ by typing your queries or uploading files.
5. Confirm sensitive actions via the confirmation modal.

---

## 🛡️ Security

- **Environment Variables**: API keys and sensitive credentials are stored securely in a `.env` file.
- **Workspace Isolation**: File operations are restricted to the designated workspace directory.
- **Confirmation Workflow**: Sensitive actions require explicit user approval.

---

## 🛠️ Development

### Adding New Tools
1. Define the tool in `raiden+/app.py` using the `@tool` decorator.
2. Add the tool to `available_tools_list` and `executable_tools_map`.

### Extending the Frontend
1. Modify `index.html` for structural changes.
2. Update `style.css` for styling.
3. Add interactivity in `script.js`.

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 📧 Support

For questions or support, please contact us at [support@raidenplus.com](mailto:support@raidenplus.com).

---

## 🌟 Acknowledgments

Special thanks to the developers and contributors who made this project possible.