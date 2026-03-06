import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ForceGraph2D from 'react-force-graph-2d';

const API_BASE = "/api";

export default function PaperChat() {
    const { paperId } = useParams();
    const { token, logout } = useAuth();
    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState('chat'); // 'chat', 'explain', 'visualize'

    // Chat state
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loadingChat, setLoadingChat] = useState(false);
    const scrollRef = useRef(null);

    // Explain state
    const [explainData, setExplainData] = useState(null);
    const [loadingExplain, setLoadingExplain] = useState(false);

    // Visualize state
    const [visualizeData, setVisualizeData] = useState(null);
    const [loadingVisualize, setLoadingVisualize] = useState(false);
    const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 });
    const graphContainerRef = useRef(null);

    // Auto-scroll chat
    useEffect(() => {
        if (activeTab === 'chat' && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, activeTab]);

    // Handle active tab change to load data lazily
    useEffect(() => {
        if (activeTab === 'explain' && !explainData && !loadingExplain) {
            fetchExplain();
        } else if (activeTab === 'visualize' && !visualizeData && !loadingVisualize) {
            fetchVisualize();
        }

        if (activeTab === 'visualize' && graphContainerRef.current) {
            setGraphDimensions({
                width: graphContainerRef.current.clientWidth,
                height: graphContainerRef.current.clientHeight || 600
            });

            const handleResize = () => {
                if (graphContainerRef.current) {
                    setGraphDimensions({
                        width: graphContainerRef.current.clientWidth,
                        height: graphContainerRef.current.clientHeight || 600
                    });
                }
            };

            window.addEventListener('resize', handleResize);
            return () => window.removeEventListener('resize', handleResize);
        }
    }, [activeTab]);

    const fetchExplain = async () => {
        setLoadingExplain(true);
        try {
            const response = await fetch(`${API_BASE}/chat/explain`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ paper_id: paperId })
            });
            if (response.status === 401) return logout();
            const data = await response.json();
            setExplainData(data.explain);
        } catch (e) {
            console.error(e);
            setExplainData({ error: 'Failed to load explanation.' });
        } finally {
            setLoadingExplain(false);
        }
    };

    const fetchVisualize = async () => {
        setLoadingVisualize(true);
        try {
            const response = await fetch(`${API_BASE}/chat/visualize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ paper_id: paperId })
            });
            if (response.status === 401) return logout();
            const data = await response.json();
            setVisualizeData(data.visualize || { nodes: [], edges: [] });
        } catch (e) {
            console.error(e);
            setVisualizeData({ nodes: [], edges: [] });
        } finally {
            setLoadingVisualize(false);
        }
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || loadingChat) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoadingChat(true);

        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        try {
            const response = await fetch(`${API_BASE}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ paper_id: paperId, message: userMsg })
            });

            if (response.status === 401) {
                logout();
                navigate('/');
                return;
            }

            if (!response.ok) throw new Error("Stream failed");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value);

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
                                        newMsgs[lastIndex] = {
                                            ...newMsgs[lastIndex],
                                            content: newMsgs[lastIndex].content + data.data
                                        };
                                    }
                                    return newMsgs;
                                });
                            } else if (data.event === 'end') {
                                break;
                            }
                        } catch (err) { }
                    }
                }
            }
        } catch (e) {
            setMessages(prev => {
                const newMsgs = [...prev];
                const lastIndex = newMsgs.length - 1;
                newMsgs[lastIndex] = { role: 'assistant', content: "Sorry, an error occurred while connecting to the LLM." };
                return newMsgs;
            });
        } finally {
            setLoadingChat(false);
        }
    };

    const renderExplainCards = () => {
        if (loadingExplain) {
            return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>Extracting structured paper data... (This may take a minute)</div>;
        }
        if (!explainData) return null;
        if (explainData.error) return <div style={{ color: 'var(--error-color)' }}>{explainData.error}</div>;

        const sections = [
            { id: 'problem_statement', title: 'Problem Statement' },
            { id: 'key_contributions', title: 'Key Contributions' },
            { id: 'methodology', title: 'Methodology' },
            { id: 'results', title: 'Results' },
            { id: 'limitations', title: 'Limitations' },
            { id: 'eli5_summary', title: 'ELI5 Summary' }
        ];

        return (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', paddingBottom: '2rem' }}>
                {sections.map(sec => {
                    let content = explainData[sec.id];
                    if (!content) return null;

                    return (
                        <div key={sec.id} className="glass-panel animate-fade-in" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
                            <h4 style={{ color: 'var(--accent-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0.5rem' }}>
                                {sec.title}
                            </h4>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                                {Array.isArray(content) ? (
                                    <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                                        {content.map((item, i) => <li key={i} style={{ marginBottom: '0.5rem' }}>{item}</li>)}
                                    </ul>
                                ) : (
                                    <p style={{ margin: 0 }}>{content}</p>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    const renderVisualizeGraph = () => {
        if (loadingVisualize) {
            return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>Generating Knowledge Graph... (This may take a minute)</div>;
        }
        if (!visualizeData || visualizeData.nodes.length === 0) {
            if (!loadingVisualize && visualizeData) {
                return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>No graph data available.</div>;
            }
            return null;
        }

        return (
            <div className="glass-panel animate-fade-in" style={{ flex: 1, borderRadius: '16px', overflow: 'hidden', minHeight: '600px', display: 'flex' }} ref={graphContainerRef}>
                <ForceGraph2D
                    width={graphDimensions.width}
                    height={graphDimensions.height}
                    graphData={visualizeData}
                    nodeAutoColorBy="group"
                    nodeLabel="id"
                    nodeRelSize={8}
                    linkDirectionalArrowLength={3.5}
                    linkDirectionalArrowRelPos={1}
                    linkLabel={(link) => link.label || link.relationship || ''}
                    linkColor={() => 'rgba(255,255,255,0.2)'}
                    backgroundColor="var(--bg-color)"
                />
            </div>
        );
    };

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', height: '100vh', padding: '1rem' }}>
            <header style={{ padding: '1rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--panel-border)', marginBottom: '1.5rem' }}>
                <button onClick={() => navigate('/')} className="btn btn-secondary">← Back to Dashboard</button>

                <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.3rem', borderRadius: '12px' }}>
                    <button
                        className={`btn ${activeTab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.5rem 1.5rem', border: 'none', background: activeTab === 'chat' ? '' : 'transparent' }}
                        onClick={() => setActiveTab('chat')}
                    >
                        Chat
                    </button>
                    <button
                        className={`btn ${activeTab === 'explain' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.5rem 1.5rem', border: 'none', background: activeTab === 'explain' ? '' : 'transparent' }}
                        onClick={() => setActiveTab('explain')}
                    >
                        Explain
                    </button>
                    <button
                        className={`btn ${activeTab === 'visualize' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.5rem 1.5rem', border: 'none', background: activeTab === 'visualize' ? '' : 'transparent' }}
                        onClick={() => setActiveTab('visualize')}
                    >
                        Visualize
                    </button>
                </div>

                <button onClick={logout} className="btn btn-secondary">Sign Out</button>
            </header>

            {/* CHAT TAB */}
            {activeTab === 'chat' && (
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                    <div
                        ref={scrollRef}
                        className="glass-panel"
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            marginBottom: '1.5rem',
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

                    <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '1rem', paddingBottom: '1rem' }}>
                        <input
                            type="text"
                            className="input-field glass-panel"
                            placeholder="Ask a question..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loadingChat}
                            style={{ flex: 1 }}
                        />
                        <button type="submit" className="btn btn-primary" disabled={loadingChat || !input.trim()}>
                            {loadingChat ? 'Thinking...' : 'Send Message'}
                        </button>
                    </form>
                </div>
            )}

            {/* EXPLAIN TAB */}
            {activeTab === 'explain' && (
                <div style={{ flex: 1, overflowY: 'auto' }}>
                    {renderExplainCards()}
                </div>
            )}

            {/* VISUALIZE TAB */}
            {activeTab === 'visualize' && (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    {renderVisualizeGraph()}
                </div>
            )}
        </div>
    );
}
