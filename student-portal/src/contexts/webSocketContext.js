import {createContext, useContext} from 'react';
export const WebSocketContext = createContext(null);
export function useWebSocket() {
 const value = useContext(WebSocketContext);
 if (!value) throw new Error('useWebSocket requires WebSocketProvider');
 return value;
}
