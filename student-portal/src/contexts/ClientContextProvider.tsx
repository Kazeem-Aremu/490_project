import React, {Children, 
    createContext, 
    ReactNode, 
    useContext, 
    useEffect, 
    useRef, 
    useState}
     from 'react'

type Message = {
    id:string;
    text:string;
    timestamp:number;
};

type webSocketContextType = {
    messages:Message[];
    sendMessage:(msg:unknown) => void;
    isConnected:boolean;
};

const webSocketContext = createContext<webSocketContextType|null>(null);

export const useWebSocket = () => {
    const context = useContext(webSocketContext);
    if (!context){
        throw new Error("useWebSocket must be used with a WebSocketProvider")

    }
    return context
}

type ProviderProps = {
    url?:string;
    children:ReactNode;
}

//const [messages, setMessages] = useState<Message[]>([])

export  const WebSocketProvider = ({url = "ws://127.0.0.1:8343", children}:ProviderProps) =>{
    const socketRef = useRef<WebSocket| null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const socket = new WebSocket(url);
        socketRef.current = socket;

        socket.onopen = () => {
            console.log("WebSocket connected");
            setIsConnected(true);
        };

        socket.onclose = () => {
            console.log("Websocket is disconnected")
            setIsConnected(false);

        };

        socket.onmessage = (event) =>{
            try{
                const data:Message = JSON.parse(event.data);
                setMessages((prev) => [...prev, data]);

            } catch(err) {
                console.log("WebSocket disconnected");
                setIsConnected(false);

            }
        };

        return () => {socket.close();}
    }, [url]);

    const sendMessage = (msg:unknown) => {
        if (socketRef.current?.readyState === WebSocket.OPEN)
           {socketRef.current.send(JSON.stringify(msg));

        }else{
        console.warn("Websocket is not Open");
    }
}
    return (
        <webSocketContext.Provider value = {{messages, sendMessage, isConnected}}>
            {children}
        </webSocketContext.Provider>
    );
}