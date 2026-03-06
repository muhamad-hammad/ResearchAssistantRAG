import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_BASE = "/api";

export default function Dashboard() {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [papers, setPapers] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef(null);

    const fetchPapers = async () => {
        try {
            const res = await fetch(`${API_BASE}/papers`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setPapers(data);
            } else if (res.status === 401) {
                logout();
            }
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchPapers();
        // Poll for status updates on pending/processing papers
        const interval = setInterval(() => {
            setPapers(current => {
                const needsPolling = current.some(p => p.status !== 'ready' && p.status !== 'failed');
                if (needsPolling) fetchPapers();
                return current;
            });
        }, 3000);
        return () => clearInterval(interval);
    }, [token]);

    const handleUpload = async (file) => {
        if (!file || file.type !== "application/pdf") {
            alert("Please upload a valid PDF file.");
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch(`${API_BASE}/papers/upload`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData
            });
            if (res.ok) {
                await fetchPapers();
            } else {
                alert("Upload failed.");
            }
        } catch (e) {
            console.error(e);
            alert("Upload failed.");
        } finally {
            setUploading(false);
        }
    };

    const onDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
        else if (e.type === "dragleave") setDragActive(false);
    };

    const onDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleUpload(e.dataTransfer.files[0]);
        }
    };

    return (
        <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}>
                <h2>My Research Papers</h2>
                <button onClick={logout} className="btn btn-secondary">Sign Out</button>
            </div>

            <div
                className={`glass-panel animate-fade-in ${dragActive ? 'drag-active' : ''}`}
                style={{
                    padding: '4rem 2rem',
                    textAlign: 'center',
                    borderStyle: dragActive ? 'solid' : 'dashed',
                    borderColor: dragActive ? 'var(--accent-primary)' : 'var(--panel-border)',
                    cursor: 'pointer',
                    marginBottom: '3rem',
                    transition: 'all 0.2s ease'
                }}
                onDragEnter={onDrag} onDragLeave={onDrag} onDragOver={onDrag} onDrop={onDrop}
                onClick={() => fileInputRef.current.click()}
            >
                <input
                    type="file"
                    accept="application/pdf"
                    style={{ display: 'none' }}
                    ref={fileInputRef}
                    onChange={(e) => handleUpload(e.target.files[0])}
                />
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
                <h3>Upload a new Research Paper</h3>
                <p style={{ marginTop: '0.5rem' }}>Drag and drop a PDF file here, or click to browse</p>
                {uploading && <p style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>Uploading...</p>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {papers.map((paper) => (
                    <div
                        key={paper.id}
                        className="glass-panel"
                        style={{
                            padding: '1.5rem',
                            cursor: paper.status === 'ready' ? 'pointer' : 'default',
                            transition: 'transform 0.2s',
                            opacity: paper.status === 'failed' ? 0.5 : 1
                        }}
                        onClick={() => {
                            if (paper.status === 'ready') navigate(`/chat/${paper.id}`, { state: { title: paper.title } });
                        }}
                        onMouseOver={(e) => { if (paper.status === 'ready') e.currentTarget.style.transform = 'translateY(-4px)' }}
                        onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)' }}
                    >
                        <h4 style={{ wordBreak: 'break-word', marginBottom: '1rem' }}>{paper.title}</h4>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                {new Date(paper.created_at || Date.now()).toLocaleDateString()}
                            </span>

                            <span style={{
                                padding: '0.25rem 0.75rem',
                                borderRadius: '99px',
                                fontSize: '0.8rem',
                                fontWeight: 'bold',
                                backgroundColor: paper.status === 'ready' ? 'var(--success-color)' :
                                    paper.status === 'failed' ? 'var(--error-color)' :
                                        'var(--accent-primary)',
                                color: 'white'
                            }}>
                                {paper.status.toUpperCase()}
                            </span>
                        </div>

                        {paper.status === 'processing' && (
                            <div style={{ width: '100%', height: '4px', background: 'var(--panel-border)', marginTop: '1rem', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{ width: '50%', height: '100%', background: 'var(--accent-primary)', animation: 'slide 1.5s infinite linear' }} />
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <style>{`
        @keyframes slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
      `}</style>
        </div>
    );
}
