import {
    createContext,
    type ReactNode,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState}
     from 'react'

// Every server reply has this envelope (Docs/Server_API_Documentation.md, section 4.3)
export type ServerResponse<T = unknown> = {
    "Response Code": string;
    MESSAGE: T;
    REQUESTID?: number;
};

type Message = ServerResponse & {
    id:string;
    timestamp:number;
};

export class ServerError extends Error {
    code:string;
    constructor(code:string, text:string){
        super(text);
        this.code = code;
    }
}

type webSocketContextType = {
    messages:Message[];
    sendMessage:(msg:unknown) => void;
    // Sends one request and resolves with its MESSAGE when the "200" reply comes back.
    request:<T = unknown>(msg:{MESSAGE:Record<string, unknown>}, timeoutMs?:number) => Promise<T>;
    isConnected:boolean;
};

const webSocketContext = createContext<webSocketContextType|null>(null);

// eslint-disable-next-line react-refresh/only-export-components
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

type Pending = {resolve:(v:unknown) => void; reject:(e:Error) => void; timer:ReturnType<typeof setTimeout>};

const RECONNECT_MS = 2000;

export  const WebSocketProvider = ({url = "ws://127.0.0.1:8343", children}:ProviderProps) =>{
    const socketRef = useRef<WebSocket| null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const pending = useRef(new Map<number, Pending>());
    const nextId = useRef(1);

    useEffect(() => {
        let stopped = false;
        let retry: ReturnType<typeof setTimeout> | undefined;
        const waiting = pending.current;

        function failAll(reason:string){
            waiting.forEach((p) => { clearTimeout(p.timer); p.reject(new ServerError("503", reason)); });
            waiting.clear();
        }

        function open(){
            const socket = new WebSocket(url);
            socketRef.current = socket;

            socket.onopen = () => {
                console.log("WebSocket connected");
                setIsConnected(true);
            };

            socket.onclose = () => {
                console.log("Websocket is disconnected")
                setIsConnected(false);
                failAll("Lost the connection to the server");
                // The Python server may start after the page does, so keep trying
                if (!stopped) retry = setTimeout(open, RECONNECT_MS);
            };

            socket.onmessage = (event) =>{
                try{
                    const data:ServerResponse = JSON.parse(event.data);
                    const waiter = data.REQUESTID != null ? waiting.get(data.REQUESTID) : undefined;
                    if (waiter && data.REQUESTID != null){
                        waiting.delete(data.REQUESTID);
                        clearTimeout(waiter.timer);
                        const body = data.MESSAGE as {ERROR?:string} | null;
                        if (data["Response Code"] === "200") waiter.resolve(data.MESSAGE);
                        else waiter.reject(new ServerError(data["Response Code"], body?.ERROR ?? "Request failed"));
                        return;
                    }
                    setMessages((prev) => [...prev, {...data, id:crypto.randomUUID(), timestamp:Date.now()}]);

                } catch(err) {
                    console.warn("WebSocket sent something that isn't JSON", err);
                }
            };
        }

        open();
        return () => {
            stopped = true;
            clearTimeout(retry);
            failAll("The page closed the connection");
            socketRef.current?.close();
        };
    }, [url]);

    const sendMessage = useCallback((msg:unknown) => {
        if (socketRef.current?.readyState === WebSocket.OPEN)
           {socketRef.current.send(JSON.stringify(msg));

        }else{
        console.warn("Websocket is not Open");
    }
    }, []);

    const request = useCallback(<T,>(msg:{MESSAGE:Record<string, unknown>}, timeoutMs = 90_000) => {
        return new Promise<T>((resolve, reject) => {
            const socket = socketRef.current;
            if (socket?.readyState !== WebSocket.OPEN){
                reject(new ServerError("503", "The server isn't connected. Is SocketServer.py running?"));
                return;
            }
            const id = nextId.current++;
            const timer = setTimeout(() => {
                pending.current.delete(id);
                reject(new ServerError("504", "The server took too long to answer"));
            }, timeoutMs);
            pending.current.set(id, {resolve:resolve as (v:unknown) => void, reject, timer});
            socket.send(JSON.stringify({...msg, REQUESTID:id}));
        });
    }, []);

    return (
        <webSocketContext.Provider value = {{messages, sendMessage, request, isConnected}}>
            {children}
        </webSocketContext.Provider>
    );
}
