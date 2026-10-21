import { useState } from "react";
import { loginUser, registerUser } from "../api/api";

export default function AuthPage({ onAuthenticated }) {
    const [mode, setMode] = useState("login"); // 'login' | 'register'
    const [usernameOrEmail, setUsernameOrEmail] = useState("");
    const [password, setPassword] = useState("");

    // Register fields
    const [regUsername, setRegUsername] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regFullName, setRegFullName] = useState("");
    const [regPhone, setRegPhone] = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [regRole, setRegRole] = useState("operator");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e, customUser, customPass) => {
        if (e) e.preventDefault();
        setError("");
        setLoading(true);

        const u = customUser || usernameOrEmail;
        const p = customPass || password;

        try {
            const res = await loginUser({ username_or_email: u, password: p });
            if (res.success && res.access_token) {
                localStorage.setItem("sentronix_token", res.access_token);
                localStorage.setItem("sentronix_user", JSON.stringify(res.user));
                onAuthenticated(res.user);
            } else {
                setError(res.detail || "Authentication failed");
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Invalid credentials or backend unavailable");
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await registerUser({
                username: regUsername,
                email: regEmail,
                full_name: regFullName,
                phone: regPhone,
                password: regPassword,
                role: regRole,
            });

            if (res.success && res.access_token) {
                localStorage.setItem("sentronix_token", res.access_token);
                localStorage.setItem("sentronix_user", JSON.stringify(res.user));
                onAuthenticated(res.user);
            } else if (res.success) {
                // If token wasn't returned, log in directly
                await handleLogin(null, regUsername, regPassword);
            } else {
                setError(res.detail || "Registration failed");
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Registration failed. Username or email may already be taken.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <div className="brand-logo-icon large">
                        <div className="inner-radar"></div>
                    </div>
                    <h1>SENTRONIX AI</h1>
                    <p>Intelligent Surveillance & Safety Operations Platform</p>
                </div>

                {/* Mode Selector Tabs */}
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

                {mode === "login" && (
                    <form onSubmit={handleLogin} className="auth-form">
                        <div className="form-group">
                            <label>User ID, Phone Number, or Email</label>
                            <input
                                type="text"
                                placeholder="e.g. admin, +1 555-0199, or operator@school.edu"
                                value={usernameOrEmail}
                                onChange={(e) => setUsernameOrEmail(e.target.value)}
                                required
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
                            {loading ? "Authenticating..." : "Sign In to Command Center"}
                        </button>

                        <div className="auth-demo-shortcuts">
                            <span>Quick Demo Profiles:</span>
                            <div className="demo-pills">
                                <button
                                    type="button"
                                    onClick={() => handleLogin(null, "admin", "admin123")}
                                >
                                    Admin (admin123)
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleLogin(null, "operator", "admin123")}
                                >
                                    Security Operator
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleLogin(null, "analyst", "admin123")}
                                >
                                    Safety Analyst
                                </button>
                            </div>
                        </div>

                        <div className="auth-footer-toggle">
                            Don't have an account?{" "}
                            <button type="button" onClick={() => { setMode("register"); setError(""); }}>
                                Register here
                            </button>
                        </div>
                    </form>
                )}

                {mode === "register" && (
                    <form onSubmit={handleRegister} className="auth-form">
                        <div className="form-row">
                            <div className="form-group">
                                <label>Username / User ID</label>
                                <input
                                    type="text"
                                    placeholder="e.g. guard_01"
                                    value={regUsername}
                                    onChange={(e) => setRegUsername(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Security Officer"
                                    value={regFullName}
                                    onChange={(e) => setRegFullName(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-row">
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
                                <label>Phone Number (Optional)</label>
                                <input
                                    type="text"
                                    placeholder="+91 98765 43210"
                                    value={regPhone}
                                    onChange={(e) => setRegPhone(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Operational Role</label>
                                <select
                                    value={regRole}
                                    onChange={(e) => setRegRole(e.target.value)}
                                >
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
                                />
                            </div>
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? "Registering & Signing In..." : "Complete Registration & Enter"}
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
