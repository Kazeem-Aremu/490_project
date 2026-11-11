import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { WebSocketProvider } from './contexts/ClientContextProvider'
import { AuthProvider } from './contexts/AuthContext'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WebSocketProvider url={import.meta.env.VITE_SERVER_WS_URL ?? "ws://127.0.0.1:8343"}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </WebSocketProvider>
  </StrictMode>
)
