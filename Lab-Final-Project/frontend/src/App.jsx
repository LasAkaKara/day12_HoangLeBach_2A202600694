import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  const messagesEndRef = useRef(null);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const API_KEY = import.meta.env.VITE_AGENT_API_KEY || "my-local-secret-key";

  // Load session from local storage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem('chat_session_id');
    if (savedSession) {
      setSessionId(savedSession);
      // Optional: Add a welcome back message
      setMessages([{ role: 'assistant', content: 'Welcome back! Your previous session is restored.' }]);
    } else {
      setMessages([{ role: 'assistant', content: 'Hello! I am your AI agent. How can I help you today?' }]);
    }
  }, []);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          question: userMessage,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      
      // Save session id if it's new
      if (data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem('chat_session_id', data.session_id);
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (error) {
      console.error("Error calling API:", error);
      setMessages((prev) => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please check your connection or backend." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearSession = () => {
    localStorage.removeItem('chat_session_id');
    setSessionId(null);
    setMessages([{ role: 'assistant', content: 'Session cleared. Starting fresh!' }]);
  };

  return (
    <div className="app-container">
      <div className="glass-panel">
        <header className="chat-header">
          <div className="header-info">
            <h1>AI Assistant</h1>
            <span className="status-indicator"></span>
            <span className="status-text">Online</span>
          </div>
          <button className="clear-btn" onClick={handleClearSession} title="Clear Session">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </header>

        <div className="messages-container">
          {messages.map((msg, index) => (
            <div key={index} className={`message-wrapper ${msg.role === 'user' ? 'user' : 'assistant'}`}>
              <div className="message-bubble">
                <div className="message-content">{msg.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant">
              <div className="message-bubble typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={loading}
          />
          <button type="submit" disabled={!input.trim() || loading} className="send-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
