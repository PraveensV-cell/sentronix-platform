import { useState } from "react";
import { loginUser, registerUser, verifyOtp } from "../api/api";

export default function AuthPage({ onAuthenticated }) {
    const [mode, setMode] = useState("login"); // 'login' | 'register' | 'otp'
    const [usernameOrEmail, setUsernameOrEmail] = useState("");
    const [password, setPassword] = useState("");
    
    // Register fields
    const [regUsername, setRegUsername] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regFullName, setRegFullName] = useState("");
    const [regPhone, setRegPhone] = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [regRole, setRegRole] = useState("operator");

    // OTP verification fields
    const [otpEmail, setOtpEmail] = useState("");
    const [otpCode, setOtpCode] = useState("");
    const [mockOtpHint, setMockOtpHint] = useState("");

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

            if (res.success) {
                setOtpEmail(regEmail);
                setMockOtpHint(res.dev_mock_otp);
                setOtpCode(res.dev_mock_otp); // auto-fill in dev mode for ease!
                setMode("otp");
            } else {
                setError(res.detail || "Registration failed");
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    const handleVerifyOtp = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await verifyOtp({ email: otpEmail, otp: otpCode });
            if (res.success) {
                // Auto-login with the newly verified credentials
                await handleLogin(null, regUsername, regPassword);
            } else {
                setError(res.detail || "OTP verification failed");
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Invalid OTP code");
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

                {error && <div className="auth-alert error">{error}</div>}

                {mode === "login" && (
                    <form onSubmit={handleLogin} className="auth-form">
                        <div className="form-group">
                            <label>Username or Email</label>
                            <input
                                type="text"
                                placeholder="e.g. admin or operator"
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
                                    onClick={() => {
                                        setUsernameOrEmail("operator");
                                        setPassword("admin123");
                                    }}
                                >
                                    Security Operator
                                </button>
                            </div>
                        </div>

                        <div className="auth-footer-toggle">
                            Don't have an account?{" "}
                            <button type="button" onClick={() => setMode("register")}>
                                Register here
                            </button>
                        </div>
                    </form>
                )}

                {mode === "register" && (
                    <form onSubmit={handleRegister} className="auth-form">
                        <div className="form-row">
                            <div className="form-group">
                                <label>Username</label>
                                <input
                                    type="text"
                                    placeholder="johndoe"
                                    value={regUsername}
                                    onChange={(e) => setRegUsername(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Full Name</label>
                                <input
                                    type="text"
                                    placeholder="John Doe"
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
                                    placeholder="john@school.edu"
                                    value={regEmail}
                                    onChange={(e) => setRegEmail(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Phone</label>
                                <input
                                    type="text"
                                    placeholder="+1 555-0199"
                                    value={regPhone}
                                    onChange={(e) => setRegPhone(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Role</label>
                                <select
                                    value={regRole}
                                    onChange={(e) => setRegRole(e.target.value)}
                                >
                                    <option value="operator">Security Operator</option>
                                    <option value="admin">Administrator</option>
                                    <option value="analyst">Analyst</option>
                                    <option value="viewer">Viewer</option>
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
                            {loading ? "Registering..." : "Send Verification OTP"}
                        </button>

                        <div className="auth-footer-toggle">
                            Already registered?{" "}
                            <button type="button" onClick={() => setMode("login")}>
                                Sign in
                            </button>
                        </div>
                    </form>
                )}

                {mode === "otp" && (
                    <form onSubmit={handleVerifyOtp} className="auth-form">
                        <div className="auth-otp-badge">
                            <strong>[DEV OTP MODE ACTIVE]</strong>
                            <p>Verification OTP generated for {otpEmail}:</p>
                            <span className="otp-highlight">{mockOtpHint}</span>
                        </div>

                        <div className="form-group">
                            <label>Enter 6-Digit OTP</label>
                            <input
                                type="text"
                                placeholder="123456"
                                value={otpCode}
                                onChange={(e) => setOtpCode(e.target.value)}
                                maxLength={6}
                                required
                            />
                        </div>

                        <button type="submit" className="auth-submit-btn" disabled={loading}>
                            {loading ? "Verifying..." : "Verify & Launch System"}
                        </button>

                        <div className="auth-footer-toggle">
                            <button type="button" onClick={() => setMode("register")}>
                                Back to registration
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
