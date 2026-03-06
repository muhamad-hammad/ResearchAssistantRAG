import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const API_BASE = "/api";

export default function AuthPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errorDelay, setErrorDelay] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrorDelay('');
        setLoading(true);

        try {
            if (!isLogin) {
                // Register flow
                const regRes = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (!regRes.ok) throw new Error(await regRes.text());
            }

            // Login flow (runs after register automatically, or standalone)
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const loginRes = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            });

            if (!loginRes.ok) throw new Error(await loginRes.text());

            const data = await loginRes.json();
            login(data.access_token);
            navigate('/');
        } catch (err) {
            // Clean up fastAPI error string
            let msg = err.message;
            try { msg = JSON.parse(msg).detail || msg; } catch { }
            setErrorDelay(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container" style={{
            display: 'flex', minHeight: '100vh', padding: '2rem', justifyContent: 'center', alignItems: 'center'
        }}>
            <div className="glass-panel animate-fade-in" style={{
                maxWidth: '480px', width: '100%', padding: '3rem', display: 'flex', flexDirection: 'column', gap: '2rem'
            }}>
                <div style={{ textAlign: 'center' }}>
                    <h1 style={{ background: 'linear-gradient(135deg, var(--accent-primary), #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        Aura Research
                    </h1>
                    <p>Access your intelligent document assistant</p>
                </div>

                {errorDelay && (
                    <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid var(--error-color)', borderRadius: '4px', color: '#ff8a8a' }}>
                        {errorDelay}
                    </div>
                )}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div className="input-group">
                        <label className="input-label">Email address</label>
                        <input
                            type="email"
                            className="input-field"
                            placeholder="you@university.edu"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="input-group">
                        <label className="input-label">Password</label>
                        <input
                            type="password"
                            className="input-field"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '1rem', marginTop: '0.5rem' }} disabled={loading}>
                        {loading ? "Processing..." : (isLogin ? "Sign In" : "Create Account")}
                    </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                    <p style={{ fontSize: '0.9rem' }}>
                        {isLogin ? "Don't have an account?" : "Already have an account?"}
                        <button
                            className="btn btn-secondary"
                            style={{ marginLeft: '1rem', padding: '0.5rem 1rem', background: 'transparent', border: 'none', color: 'var(--accent-primary)' }}
                            onClick={() => setIsLogin(!isLogin)}
                        >
                            {isLogin ? "Register here" : "Sign in here"}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}
