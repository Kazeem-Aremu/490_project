import {useRef, useState} from 'react';
import {useWebSocket} from './contexts/webSocketContext';
import './chatbox.css';
const positiveID = value => /^\d+$/.test(value) && Number.isSafeInteger(Number(value)) && Number(value) > 0;
export default function Chatbox() {
  const {request, isConnected} = useWebSocket();
  const query = new URLSearchParams(window.location.search);
  const [userID, setUserID] = useState(query.get('userId') || '');
  const [submissionID, setSubmissionID] = useState(query.get('submissionId') || '');
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lock = useRef(false);
  async function start(event) {
    event.preventDefault();
    if (lock.current || !positiveID(userID) || !positiveID(submissionID)) return;
    lock.current = true; setBusy(true); setError(''); setConversation(null); setMessages([]);
    try {
      const data = await request({MESSAGE:{METHOD:'POST', INFO:'startAIConversation', PARAMS:{USERID:Number(userID), SUBMISSIONID:Number(submissionID)}}});
      if (!Number.isSafeInteger(data?.CONVOID) || !Array.isArray(data.MESSAGES)) throw new Error('Unexpected conversation response');
      setConversation({id:data.CONVOID, userID:Number(userID), submissionID:Number(submissionID)});
      setMessages(data.MESSAGES.filter(m => ['user','assistant'].includes(m.role) && typeof m.content === 'string'));
    } catch (err) { setError(err.message); }
    finally { lock.current = false; setBusy(false); }
  }
  async function send(event) {
    event.preventDefault();
    const content = text.trim();
    if (lock.current || !conversation || !content || content.length > 4000) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const data = await request({MESSAGE:{METHOD:'POST', INFO:'sendAIMessage', PARAMS:{USERID:conversation.userID, CONVOID:conversation.id, TEXT:content}}});
      if (typeof data?.REPLY !== 'string') throw new Error('Unexpected reply response');
      setMessages(old => [...old, {role:'user',content}, {role:'assistant',content:data.REPLY}]);
      setText('');
    } catch (err) { setError(err.message); }
    finally { lock.current = false; setBusy(false); }
  }
  return <main className="chatbox-page"><div className="app">
    <header><a href="#">Back to portal</a><h1 className="title">Assignment chat</h1><p className="subtitle">Questions and hints about your submitted work, provided by the server.</p></header>
    <div className="work"><div className="card"><h2>Open your submission</h2>
      <p>Local integration preview: enter existing database IDs. The server loads the submitted file. These fields do not sign you in.</p>
      <form className="submission-form" onSubmit={start}>
        <label>Student ID<input required inputMode="numeric" value={userID} disabled={busy} onChange={e => {setUserID(e.target.value);setConversation(null);setMessages([]);}} /></label>
        <label>Submission ID<input required inputMode="numeric" value={submissionID} disabled={busy} onChange={e => {setSubmissionID(e.target.value);setConversation(null);setMessages([]);}} /></label>
        <button className="btn" disabled={busy || !isConnected || !positiveID(userID) || !positiveID(submissionID)}>Open / resume conversation</button>
      </form>
      <p role="status">{isConnected ? 'Connected to local bridge' : 'Disconnected — start the backend and bridge, then reload.'}</p>
      {conversation && <p>Submission {conversation.submissionID} · Conversation {conversation.id}</p>}
    </div></div>
    <section className="chat"><div className="chat-head"><strong>AI tutor</strong><span className="pill">{conversation ? 'Conversation ready' : 'Open a submission first'}</span></div>
      <div className="messages" role="log" aria-live="polite">{messages.map((m,i) => <div key={i} className={`msg ${m.role === 'user' ? 'me' : 'bot'}`}>{m.role === 'assistant' && <span className="avatar">AI</span>}<div className="bubble">{m.content}</div></div>)}{busy && <p role="status">Waiting for server…</p>}</div>
      {error && <p className="chat-error" role="alert">{error}</p>}
      <form className="composer" onSubmit={send}><textarea aria-label="Message to AI" placeholder="Ask about your submission…" value={text} maxLength={4000} disabled={!conversation || busy} onChange={e=>setText(e.target.value)} /><button className="btn" disabled={!conversation || !isConnected || busy || !text.trim()}>Send</button></form>
    </section>
  </div></main>;
}
