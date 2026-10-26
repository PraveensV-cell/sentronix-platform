import { useState } from "react";
import { loginUser, registerUser } from "../api/api";

// ─── Demo Profiles for quick testing ────────────────────────────────────────
const DEMO_PROFILES = [
    { label: "Admin",    identifier: "admin",    password: "admin123" },
    { label: "Operator", identifier: "operator", password: "admin123" },
    { label: "Analyst",  identifier: "analyst",  password: "admin123" },
];

export default function AuthPage({ onAuthenticated }) {
    const [mode, setMode] = useState("login");   // 'login' | 'register'

    // Login fields
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword]     = useState("");

    // Register fields: ID, Name, Phone, Email, Password (NO OTP)
    const [regUsername, setRegUsername] = useState("");
    const [regName,     setRegName]     = useState("");
    const [regPhone,    setRegPhone]    = useState("");
    const [regEmail,    setRegEmail]    = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [regRole,     setRegRole]     = useState("operator");

    const [error,   setError]   = useState("");
    const [loading, setLoading] = useState(false);

    // ── Login ──────────────────────────────────────────────────────────────
    const handleLogin = async (e, customId, customPw) => {
        if (e) e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await loginUser({
                identifier: customId || identifier,
                password:   customPw  || password,
            });
            if (res.success && res.access_token) {
                localStorage.setItem("sentronix_token", res.access_token);
                localStorage.setItem("sentronix_user",  JSON.stringify(res.user));
                onAuthenticated(res.user);
            } else {
                setError(res.detail || "Authentication failed");
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                "Invalid credentials or backend unavailable"
            );
        } finally {
            setLoading(false);
        }
    };

    // ── Register (No OTP) ───────────────────────────────────────────────────
    const handleRegister = async (e) => {
        e.preventDefault();
        setError("");
        if (!regUsername || !regName || !regPhone || !regEmail || !regPassword) {
            setError("All fields (User ID, Full Name, Phone, Email, and Password) are required.");
            return;
        }
        setLoading(true);
        try {
            const res = await registerUser({
                username: regUsername,
                name:     regName,
                phone:    regPhone,
                email:    regEmail,
                password: regPassword,
                role:     regRole,
            });
            if (res.success && res.access_token) {
                localStorage.setItem("sentronix_token", res.access_token);
                localStorage.setItem("sentronix_user",  JSON.stringify(res.user));
                onAuthenticated(res.user);
            } else {
                setError(res.detail || "Registration failed");
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                "Registration failed. Username, email or phone may already be registered."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">

                {/* Header */}
                <div className="auth-header">
                    <div className="brand-logo-icon large">
                        <div className="inner-radar"></div>
                    </div>
                    <h1>SENTRONIX AI</h1>
                    <p>Intelligent 24/7 Surveillance &amp; Safety Platform</p>
                </div>

                {/* Tab Switcher */}
                <div className="auth-tabs-row">
                    <button
                        type="button"
                        className={`auth-tab-btn ${mode === "login" ? "active" : ""}`}
                        onClick={() => { setMode("login"); setError(""); }}
                    >
                        Sign In
                    </button>
                    <button
                        type="button"
                        className={`auth-tab-btn ${mode === "register" ? "active" : ""}`}
                        onClick={() => { setMode("register"); setError(""); }}
                    >
                        Register New User
                    </button>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="auth-alert error">
                        <span>⚠️</span>
                        <span>{error}</span>
                    </div>
                )}

                {/* ─── LOGIN FORM ─────────────────────────────────────────── */}
                {mode === "login" && (
                    <form onSubmit={handleLogin} className="auth-form">
                        <div className="form-group">
                            <label>User ID, Email, or Phone</label>
                            <input
                                type="text"
                                placeholder="e.g. admin or 9876543210"
                                value={identifier}
                                onChange={(e) => setIdentifier(e.target.value)}
                                required
                                autoFocus
                            />
                        </div>

                        <div className="form-group">
                            <label>Password</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? "Authenticating..." : "Sign In to Platform →"}
                        </button>

                        {/* Quick Demo Profiles */}
                        <div className="demo-profiles-row">
                            <span className="demo-label">Quick fill:</span>
                            {DEMO_PROFILES.map((p) => (
                                <button
                                    key={p.label}
                                    type="button"
                                    className="demo-btn"
                                    onClick={() => {
                                        setIdentifier(p.identifier);
                                        setPassword(p.password);
                                        handleLogin(null, p.identifier, p.password);
                                    }}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </div>

                        <div className="auth-footer-toggle">
                            Don&apos;t have an account?{" "}
                            <button type="button" onClick={() => { setMode("register"); setError(""); }}>
                                Register here
                            </button>
                        </div>
                    </form>
                )}

                {/* ─── REGISTER FORM (NO OTP REQUIRED) ──────────────────────── */}
                {mode === "register" && (
                    <form onSubmit={handleRegister} className="auth-form">
                        <div className="form-group">
                            <label>User ID (Username) *</label>
                            <input
                                type="text"
                                placeholder="e.g. officer_01 or pravin"
                                value={regUsername}
                                onChange={(e) => setRegUsername(e.target.value)}
                                required
                                autoFocus
                            />
                        </div>

                        <div className="form-group">
                            <label>Full Name *</label>
                            <input
                                type="text"
                                placeholder="e.g. Commander Pravin"
                                value={regName}
                                onChange={(e) => setRegName(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Phone Number *</label>
                            <input
                                type="tel"
                                placeholder="+91 98765 43210"
                                value={regPhone}
                                onChange={(e) => setRegPhone(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Email Address *</label>
                            <input
                                type="email"
                                placeholder="officer@sentronix.ai"
                                value={regEmail}
                                onChange={(e) => setRegEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Password *</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                value={regPassword}
                                onChange={(e) => setRegPassword(e.target.value)}
                                required
                                minLength={4}
                            />
                        </div>

                        <div className="form-group">
                            <label>Operational Role</label>
                            <select value={regRole} onChange={(e) => setRegRole(e.target.value)}>
                                <option value="operator">Security Operator</option>
                                <option value="admin">System Administrator</option>
                                <option value="analyst">Safety Analyst</option>
                                <option value="viewer">Command Room Viewer</option>
                            </select>
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? "Creating Account..." : "Create Account & Enter Platform →"}
                        </button>

                        <div className="auth-footer-toggle">
                            Already registered?{" "}
                            <button type="button" onClick={() => { setMode("login"); setError(""); }}>
                                Sign in
                            </button>
                        </div>
                    </form>
                )}

            </div>
        </div>
    );
}
