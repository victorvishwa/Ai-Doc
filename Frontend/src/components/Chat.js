import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const { user, logout } = useAuth();

  // Debug info
  useEffect(() => {
    console.log('Current user:', user);
  }, [user]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark-mode');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      content: input,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await axios.post('/api/chat/query', {
        text: input
      }, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });

      // Simulate typing effect
      setTimeout(() => {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          content: response.data.answer,
          sender: 'ai',
          timestamp: new Date().toISOString()
        }]);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        content: 'Sorry, there was an error processing your request.',
        sender: 'error',
        timestamp: new Date().toISOString()
      }]);
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/documents/upload', formData, {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        }
      });

      // Add success message to chat
      setMessages(prev => [...prev, {
        content: `Document "${file.name}" uploaded successfully.`,
        sender: 'ai',
        timestamp: new Date().toISOString()
      }]);

      // Reset after successful upload
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
      }, 1000);
    } catch (error) {
      console.error('Error uploading file:', error);
      // Add error message to chat
      setMessages(prev => [...prev, {
        content: `Failed to upload document: ${error.response?.data?.detail || error.message}`,
        sender: 'error',
        timestamp: new Date().toISOString()
      }]);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="container">
      {/* Debug info - remove in production */}
      {process.env.NODE_ENV === 'development' && (
        <div style={{ 
          position: 'fixed', 
          top: '1rem', 
          left: '1rem', 
          background: 'var(--card-bg)', 
          padding: '0.5rem', 
          borderRadius: '0.5rem',
          fontSize: '0.8rem',
          zIndex: 1000
        }}>
          Admin Status: {user?.is_admin ? 'Yes' : 'No'}
        </div>
      )}

      <div className="chat-container">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
            style={{
              animation: `fadeIn 0.3s ease ${index * 0.1}s both`
            }}
          >
            <div className="message-content">
              {message.content}
            </div>
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message ai-message" style={{ animation: 'fadeIn 0.3s ease' }}>
            <div className="typewriter">AI is analyzing your request...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-controls">
        <form onSubmit={handleSubmit} className="chat-input-container">
          <div className="chat-input-wrapper">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
              accept=".pdf,.doc,.docx,.txt"
            />
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
              className="chat-input"
            />
            
            <button
              type="button"
              className="upload-btn"
              onClick={handleUploadClick}
              disabled={isUploading}
              style={{
                opacity: isUploading ? 0.7 : 1,
                transform: isUploading ? 'scale(0.95)' : 'scale(1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '0.5rem'
              }}
            >
              {isUploading ? (
                <div className="spinner" style={{ width: '24px', height: '24px' }} />
              ) : (
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              )}
            </button>

            <button
              type="submit"
              className="send-button"
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? (
                <div className="spinner" />
              ) : (
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
        </form>

        <button
          className="user-account-btn"
          onClick={logout}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.5rem',
            borderRadius: '50%',
            background: 'var(--primary-color)',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            position: 'fixed',
            top: '1rem',
            right: '1rem'
          }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </button>
      </div>

      {isUploading && (
        <div
          className="card"
          style={{
            position: 'fixed',
            bottom: '6rem',
            right: '2rem',
            padding: '1rem',
            animation: 'slideUp 0.3s ease'
          }}
        >
          <div className="flex items-center gap-2">
            <div className="spinner" style={{ width: '20px', height: '20px' }} />
            <span>Uploading document... {uploadProgress}%</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat; 