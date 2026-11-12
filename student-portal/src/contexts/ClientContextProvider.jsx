import {useEffect, useRef, useState} from 'react';
import {WebSocketContext as Context} from './webSocketContext';
export function WebSocketProvider({url = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8343', children}) {
  const socketRef = useRef(null);
  const pending = useRef(null);
  const [isConnected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  useEffect(() => {
    const socket = new WebSocket(url);
    socketRef.current = socket;
    socket.onopen = () => setConnected(true);
    socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        setMessages(old => [...old.slice(-99), data]);
        if (pending.current) {
          const {resolve, reject, timer} = pending.current;
          pending.current = null;
          clearTimeout(timer);
          const body = data.MESSAGE;
          if (data['Response Code'] !== '200' || body?.ERROR || body?.error || body?.Error) reject(new Error(body?.ERROR || body?.error || body?.Error || 'Server request failed'));
          else resolve(body);
        }
      } catch { socket.close(); }
    };
    socket.onclose = () => {
      setConnected(false);
      if (pending.current) {
        clearTimeout(pending.current.timer);
        pending.current.reject(new Error('Disconnected from server. Reload to reconnect.'));
        pending.current = null;
      }
    };
    socket.onerror = () => socket.close();
    return () => {
      socket.onclose = null;
      socket.close();
      if (pending.current) {
        clearTimeout(pending.current.timer);
        pending.current.reject(new Error('Connection closed'));
        pending.current = null;
      }
    };
  }, [url]);
  function request(message) {
    return new Promise((resolve, reject) => {
      const socket = socketRef.current;
      if (socket?.readyState !== WebSocket.OPEN) return reject(new Error('Server is disconnected. Start both Python servers and reload.'));
      if (pending.current) return reject(new Error('Please wait for the current request.'));
      const timer = setTimeout(() => {
        pending.current = null;
        reject(new Error('Server timed out. Reload to reconnect.'));
        socket.close();
      }, 90000);
      pending.current = {resolve, reject, timer};
      socket.send(JSON.stringify(message));
    });
  }
  return <Context.Provider value={{messages, request, sendMessage: request, isConnected}}>{children}</Context.Provider>;
}
