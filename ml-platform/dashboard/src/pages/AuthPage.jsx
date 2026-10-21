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

    // Register fields
    const [regUsername, setRegUsername] = useState("");
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

    // ── Register ───────────────────────────────────────────────────────────
    const handleRegister = async (e) => {
        e.preventDefault();
        setError("");
        if (!regUsername || !regPhone || !regEmail || !regPassword) {
            setError("All fields are required");
            return;
        }
        setLoading(true);
        try {
            const res = await registerUser({
                username: regUsername,
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
                "Registration failed. Username, email or phone may already be taken."
            );
        } finally {
            setLoading(false);
        }
    };

    // ── UI ─────────────────────────────────────────────────────────────────
    return (
        <div className="auth-container">
            <div className="auth-card">

                {/* Header */}
                <div className="auth-header">
                    <div className="brand-logo-icon large">
                        <div className="inner-radar"></div>
                    </div>
                    <h1>SENTRONIX AI</h1>
                    <p>Intelligent Surveillance &amp; Safety Operations Platform</p>
                </div>

                {/* Tabs */}
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
                        Create Account
                    </button>
                </div>

                {error && <div className="auth-alert error">{error}</div>}

                {/* ─── LOGIN FORM ─────────────────────────────────────────── */}
                {mode === "login" && (
                    <form onSubmit={handleLogin} className="auth-form">
                        <div className="form-group">
                            <label>User ID, Email, or Phone Number</label>
                            <input
                                type="text"
                                placeholder="admin  /  user@email.com  /  +91 98765 43210"
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
                            {loading ? "Authenticating..." : "Sign In →"}
                        </button>

                        {/* Demo quick-login buttons */}
                        <div className="demo-profiles-row">
                            <span className="demo-label">Quick Demo:</span>
                            {DEMO_PROFILES.map((p) => (
                                <button
                                    key={p.label}
                                    type="button"
                                    className="demo-btn"
                                    onClick={() => handleLogin(null, p.identifier, p.password)}
                                    disabled={loading}
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

                {/* ─── REGISTER FORM ──────────────────────────────────────── */}
                {mode === "register" && (
                    <form onSubmit={handleRegister} className="auth-form">
                        <div className="form-group">
                            <label>User ID (Username)</label>
                            <input
                                type="text"
                                placeholder="e.g. guard_01 or john_smith"
                                value={regUsername}
                                onChange={(e) => setRegUsername(e.target.value)}
                                required
                                autoFocus
                            />
                        </div>

                        <div className="form-group">
                            <label>Phone Number</label>
                            <input
                                type="tel"
                                placeholder="+91 98765 43210"
                                value={regPhone}
                                onChange={(e) => setRegPhone(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Email Address</label>
                            <input
                                type="email"
                                placeholder="officer@sentronix.ai"
                                value={regEmail}
                                onChange={(e) => setRegEmail(e.target.value)}
                                required
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

                        <div className="form-group">
                            <label>Password</label>
                            <input
                                type="password"
                                placeholder="••••••••"
                                value={regPassword}
                                onChange={(e) => setRegPassword(e.target.value)}
                                required
                                minLength={4}
                            />
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? "Creating Account..." : "Create Account & Enter →"}
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
