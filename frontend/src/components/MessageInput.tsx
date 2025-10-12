import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiX } from 'react-icons/fi';
import { MessageInputProps } from '../types';

const MessageInput: React.FC<MessageInputProps> = ({ onDetect, isLoading }) => {
  const [text, setText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const MAX_CHARS = 5000;

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [text]);

  useEffect(() => {
    // Keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter' && text.trim() && !isLoading) {
        handleSubmit();
      }
      if (e.key === 'Escape') {
        handleClear();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [text, isLoading]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    if (newText.length <= MAX_CHARS) {
      setText(newText);
      setCharCount(newText.length);
    }
  };

  const handleSubmit = () => {
    if (text.trim() && !isLoading) {
      onDetect(text);
    }
  };

  const handleClear = () => {
    setText('');
    setCharCount(0);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="message-input-container">
      <div className="input-header">
        <h3>Enter Message</h3>
        <span className="char-counter">
          {charCount} / {MAX_CHARS}
        </span>
      </div>
      
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          placeholder="Type or paste your message here..."
          className="message-textarea"
          disabled={isLoading}
          rows={4}
        />
        
        <div className="input-actions">
          <button
            onClick={handleClear}
            className="btn-clear"
            disabled={!text || isLoading}
            title="Clear (Esc)"
          >
            <FiX size={18} />
            Clear
          </button>
          
          <button
            onClick={handleSubmit}
            className="btn-detect"
            disabled={!text.trim() || isLoading}
            title="Detect (Ctrl+Enter)"
          >
            <FiSend size={18} />
            {isLoading ? 'Detecting...' : 'Detect'}
          </button>
        </div>
      </div>
      
      <div className="input-hint">
        <span>Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to detect • <kbd>Esc</kbd> to clear</span>
      </div>
    </div>
  );
};

export default MessageInput;
