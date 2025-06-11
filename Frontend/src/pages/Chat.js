import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import config from '../config';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import { Send as SendIcon, Upload as UploadIcon } from '@mui/icons-material';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef(null);
  const { user } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${config.API_URL}/api/chat/query`,
        { text: input },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      const botMessage = {
        type: 'bot',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    try {
      const response = await axios.post(
        `${config.API_URL}/api/documents/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      const successMessage = {
        type: 'bot',
        content: `Document "${file.name}" uploaded successfully.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, successMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: `Failed to upload document: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <Paper
        elevation={3}
        sx={{
          flexGrow: 1,
          mb: 2,
          p: 2,
          overflow: 'auto',
          bgcolor: 'background.default'
        }}
      >
        <List>
          {messages.map((message, index) => (
            <React.Fragment key={index}>
              <ListItem
                sx={{
                  justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                  mb: 1
                }}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    bgcolor: message.type === 'user' ? 'primary.main' : 'background.paper',
                    color: message.type === 'user' ? 'primary.contrastText' : 'text.primary'
                  }}
                >
                  <ListItemText
                    primary={message.content}
                    secondary={
                      message.type === 'bot' && message.sources?.length > 0
                        ? `Sources: ${message.sources.join(', ')}`
                        : new Date(message.timestamp).toLocaleTimeString()
                    }
                  />
                </Paper>
              </ListItem>
              {index < messages.length - 1 && <Divider />}
            </React.Fragment>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Paper>

      <Box
  component="form"
  onSubmit={handleSubmit}
  sx={{
    display: 'flex',
    gap: 1.5,
    alignItems: 'center',
    p: 2,
    bgcolor: 'background.paper',
    borderRadius: 1
  }}
>
  <TextField
    fullWidth
    value={input}
    onChange={(e) => setInput(e.target.value)}
    placeholder="Ask a question about the documentation..."
    disabled={loading}
    size="small"
  />
  {/* Wrap both buttons inside a flex Box */}
  <Box sx={{ display: 'flex', gap: 1 }}>
    <Button
      type="submit"
      variant="contained"
      disabled={loading || !input.trim()}
      sx={{
        minWidth: '40px',
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        padding: 0
      }}
    >
      {loading ? <CircularProgress size={20} /> : <SendIcon />}
    </Button>
    <Button
      variant="contained"
      component="label"
      disabled={uploading}
      sx={{
        minWidth: '40px',
        width: '40px',
        height: '40px',
        borderRadius: '50%',
        padding: 0,
        backgroundColor: '#7B61FF',
        boxShadow: '0 0 10px rgba(123, 97, 255, 0.6)',
        '&:hover': {
          backgroundColor: '#6A50E0'
        }
      }}
    >
      <UploadIcon />
      <input
        type="file"
        hidden
        accept=".pdf,.txt"
        onChange={handleFileUpload}
      />
    </Button>
  </Box>
</Box>
  );
}

export default Chat;
