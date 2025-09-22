import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Point d'entrée principal de l'application React
// Initialise React et monte l'application sur l'élément #root
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);