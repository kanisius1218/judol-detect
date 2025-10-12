import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
// Choose which version to use:
// import App from './App';  // Full featured version
import AppSimple from './AppSimple';  // Simple minimal version
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <AppSimple />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
