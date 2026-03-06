import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_BASE = "http://localhost:8000/api";

export default function PaperChat() {
    const { paperId } = useParams();
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        // Add empty assistant message that we will stream into
        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        try {
            const response = await fetch(`${API_BASE}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    paper_id: paperId,
                    message: userMsg
                })
            });

            if (response.status === 401) {
                logout();
                navigate('/');
                return;
            }

            if (!response.ok) throw new Error("Stream failed");

            // Read the SSE stream manually via Fetch API body reader
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value);

                // Parse the raw SSE raw event string "data: {"event": "token", "data": "word"}\n\n"
                const lines = chunkValue.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.replace('data: ', '');
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.event === 'token' && data.data) {
                                setMessages(prev => {
                                    const newMsgs = [...prev];
                                    const lastIndex = newMsgs.length - 1;
                                    if (newMsgs[lastIndex].role === 'assistant') {
                                        // Append the token progressively
                                        newMsgs[lastIndex] = {
                                            ...newMsgs[lastIndex],
                                            content: newMsgs[lastIndex].content + data.data
                                        };
                                    }
                                    return newMsgs;
                                });
                            } else if (data.event === 'end') {
                                // Stream completed
                                break;
                            }
                        } catch (err) {
                            // Ignore partial JSON parsing errors that happen mid-stream split
                        }
                    }
                }
            }
        } catch (e) {
            console.error(e);
            setMessages(prev => {
                const newMsgs = [...prev];
                const lastIndex = newMsgs.length - 1;
                newMsgs[lastIndex] = { role: 'assistant', content: "Sorry, an error occurred while connecting to the LLM." };
                return newMsgs;
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', height: '100vh', padding: '1rem' }}>
            <header style={{ padding: '1rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--panel-border)' }}>
                <button onClick={() => navigate('/')} className="btn btn-secondary">← Back to Dashboard</button>
                <h3 style={{ margin: 0 }}>Research Assistant Chat</h3>
                <button onClick={logout} className="btn btn-secondary">Sign Out</button>
            </header>

            <div
                ref={scrollRef}
                className="glass-panel"
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    margin: '1.5rem 0',
                    padding: '2rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1.5rem'
                }}
            >
                {messages.length === 0 ? (
                    <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '20vh' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
                        <h3>Ask anything about this document</h3>
                        <p>Example: "Can you summarize the main methodology used in this paper?"</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className="animate-fade-in"
                            style={{
                                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                backgroundColor: msg.role === 'user' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                                border: msg.role === 'user' ? '1px solid var(--accent-primary)' : '1px solid var(--panel-border)',
                                padding: '1rem 1.5rem',
                                borderRadius: '16px',
                                borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
                                borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '16px',
                                maxWidth: '80%',
                                lineHeight: 1.6,
                                letterSpacing: '0.01em',
                                whiteSpace: 'pre-wrap'
                            }}
                        >
                            {msg.content}
                        </div>
                    ))
                )}
            </div>

            <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', paddingBottom: '1rem' }}>
                <input
                    type="text"
                    className="input-field glass-panel"
                    placeholder="Ask a question..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                    style={{ flex: 1 }}
                />
                <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
                    {loading ? 'Thinking...' : 'Send Message'}
                </button>
            </form>
        </div>
    );
}
