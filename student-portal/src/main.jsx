import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { WebSocketProvider } from './contexts/ClientContextProvider.js'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <WebSocketProvider url ="ws://127.0.0.1:8343">
      <App />
    </WebSocketProvider>
  </StrictMode>
)
