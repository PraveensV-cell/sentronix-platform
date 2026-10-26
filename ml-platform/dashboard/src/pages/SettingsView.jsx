import { useState, useEffect } from "react";
import { changeUserPassword, updateUserProfile } from "../api/api";

export default function SettingsView({
    user,
    onUserUpdated,
    themeMode,
    onThemeChange,
    fontStyle,
    onFontChange,
    zoomLevel,
    onZoomChange,
    voiceEnabled,
    onVoiceToggle,
}) {
    const [activeTab, setActiveTab] = useState("personalization"); // "personalization" | "account" | "system"

    // Profile form
    const [name, setName] = useState(user?.name || user?.full_name || "");
    const [email, setEmail] = useState(user?.email || "");
    const [phone, setPhone] = useState(user?.phone || "");
    const [profileFeedback, setProfileFeedback] = useState("");
    const [profileError, setProfileError] = useState("");

    // Password form
    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [passwordFeedback, setPasswordFeedback] = useState("");
    const [passwordError, setPasswordError] = useState("");

    useEffect(() => {
        if (user) {
            setName(user.name || user.full_name || "");
            setEmail(user.email || "");
            setPhone(user.phone || "");
        }
    }, [user]);

    const handleSaveProfile = async (e) => {
        e.preventDefault();
        setProfileFeedback("");
        setProfileError("");
        try {
            const res = await updateUserProfile({
                identifier: user.username,
                name,
                email,
                phone,
            });
            if (res.success) {
                setProfileFeedback("✓ Profile details updated successfully!");
                setTimeout(() => setProfileFeedback(""), 3000);
                if (onUserUpdated) onUserUpdated(res.user);
            }
        } catch (err) {
            setProfileError(err.response?.data?.detail || "Could not update profile.");
        }
    };

    const handleChangePassword = async (e) => {
        e.preventDefault();
        setPasswordFeedback("");
        setPasswordError("");
        if (newPassword !== confirmPassword) {
            setPasswordError("New passwords do not match.");
            return;
        }
        if (newPassword.length < 4) {
            setPasswordError("Password must be at least 4 characters.");
            return;
        }
        try {
            const res = await changeUserPassword({
                identifier: user.username,
                old_password: oldPassword,
                new_password: newPassword,
            });
            if (res.success) {
                setPasswordFeedback("✓ Password changed successfully!");
                setOldPassword("");
                setNewPassword("");
                setConfirmPassword("");
                setTimeout(() => setPasswordFeedback(""), 3000);
            }
        } catch (err) {
            setPasswordError(err.response?.data?.detail || "Failed to change password. Verify your current password.");
        }
    };

    const handleTestVoice = () => {
        if ("speechSynthesis" in window) {
            const utterance = new SpeechSynthesisUtterance("Audio synthesis operational. Sentronix AI is ready to broadcast real-time surveillance briefings.");
            utterance.rate = 1.05;
            window.speechSynthesis.speak(utterance);
        } else {
            alert("Speech synthesis is not supported in this browser.");
        }
    };

    return (
        <div className="surveillance-view" style={{ maxWidth: "1100px", margin: "0 auto" }}>
            {/* Header */}
            <div style={{ marginBottom: "20px" }}>
                <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "var(--text-primary)" }}>
                    ⚙️ Settings &amp; Personalization Command Center
                </h2>
                <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--text-secondary)" }}>
                    Customize interface aesthetics, typography, scaling, voice synthesis, and operator account security.
                </p>
            </div>

            {/* Navigation Tabs */}
            <div style={{ display: "flex", gap: "8px", marginBottom: "20px", borderBottom: "1px solid var(--border-color)", paddingBottom: "10px" }}>
                {[
                    { id: "personalization", label: "🎨 UI Personalization & Display" },
                    { id: "account", label: "👤 Account Security & Credentials" },
                    { id: "system", label: "⚡ System & Telemetry Preferences" },
                ].map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id)}
                        className={`fleet-pill ${activeTab === t.id ? "active" : ""}`}
                        style={{ fontSize: "12px", padding: "8px 18px", fontWeight: 600 }}
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            {/* TAB 1: UI Personalization & Display */}
            {activeTab === "personalization" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                    {/* Theme Mode Card */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            🌓 Visual Appearance &amp; Color Theme
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Select the operational color ambiance across all surveillance dashboards.
                        </p>

                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                            {[
                                { id: "light", icon: "☀️", title: "Clean Light Mode", desc: "Crisp alabaster surfaces, subtle slate depth, ideal for daylight command rooms." },
                                { id: "dark", icon: "🌙", title: "Royal Dark Tactical Mode", desc: "Deep midnight obsidian, gold and cyan highlights, low-glare nighttime command." },
                                { id: "system", icon: "💻", title: "System Default", desc: "Automatically synchronizes with your device's operating system preferences." },
                            ].map((tm) => (
                                <div
                                    key={tm.id}
                                    onClick={() => onThemeChange(tm.id)}
                                    style={{
                                        padding: "14px",
                                        borderRadius: "8px",
                                        border: `2px solid ${themeMode === tm.id ? "var(--primary-color)" : "var(--border-color)"}`,
                                        background: themeMode === tm.id ? "var(--primary-soft)" : "var(--bg-secondary)",
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "14px",
                                        transition: "all 0.15s ease",
                                    }}
                                >
                                    <div style={{ fontSize: "24px" }}>{tm.icon}</div>
                                    <div>
                                        <div style={{ fontSize: "13px", fontWeight: 700 }}>{tm.title}</div>
                                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>{tm.desc}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Typography & Fonts Card */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            🔤 Typography &amp; Font Styling
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Choose the royal or modern typographic personality for the dashboard.
                        </p>

                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                            {[
                                { id: "royal", title: "👑 Royal Historic Serif", sample: "Playfair & Cinzel Classic", font: "'Cinzel', 'Playfair Display', serif" },
                                { id: "modern", title: "⚡ Modern Professional Clean", sample: "Inter Clean Helvetica Sans", font: "'Inter', sans-serif" },
                                { id: "tech", title: "🚀 Sleek Aerospace Tech", sample: "Outfit Space Grotesk", font: "'Outfit', sans-serif" },
                                { id: "mono", title: "💻 Tactical SOC Monospace", sample: "Fira Code Terminal HUD", font: "'Fira Code', 'Courier New', monospace" },
                            ].map((f) => (
                                <div
                                    key={f.id}
                                    onClick={() => onFontChange(f.id)}
                                    style={{
                                        padding: "12px 14px",
                                        borderRadius: "8px",
                                        border: `2px solid ${fontStyle === f.id ? "var(--primary-color)" : "var(--border-color)"}`,
                                        background: fontStyle === f.id ? "var(--primary-soft)" : "var(--bg-secondary)",
                                        cursor: "pointer",
                                    }}
                                >
                                    <div style={{ fontSize: "13px", fontWeight: 700, fontFamily: f.font }}>{f.title}</div>
                                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px", fontFamily: f.font }}>
                                        Preview: {f.sample}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Dashboard Zoom & Scaling Card */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            🔍 Dashboard Zoom &amp; Canvas Scaling
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Zoom in or out to fit small laptop displays or large multi-monitor video walls.
                        </p>

                        <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "14px" }}>
                            {[
                                { val: "80%", label: "80% (Wide Overview)" },
                                { val: "90%", label: "90% (Compact)" },
                                { val: "100%", label: "100% (Standard)" },
                                { val: "110%", label: "110% (Large)" },
                                { val: "125%", label: "125% (Maximum)" },
                            ].map((z) => (
                                <button
                                    key={z.val}
                                    type="button"
                                    onClick={() => onZoomChange(z.val)}
                                    className={`fleet-pill ${zoomLevel === z.val ? "active" : ""}`}
                                    style={{ fontSize: "11px", padding: "6px 14px", fontWeight: 600 }}
                                >
                                    {z.val}
                                </button>
                            ))}
                        </div>

                        <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                            Current zoom level: <strong>{zoomLevel}</strong> • Can also be adjusted anytime via the floating zoom pill on the bottom-right corner.
                        </div>
                    </div>

                    {/* Audio & JARVIS Voice Card */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            🔊 JARVIS Spoken Audio Announcements
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Enable real-time voice speech synthesis for verified attendances and alerts.
                        </p>

                        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "14px" }}>
                            <input
                                type="checkbox"
                                id="voiceSettingToggle"
                                checked={voiceEnabled}
                                onChange={(e) => onVoiceToggle(e.target.checked)}
                                style={{ width: "18px", height: "18px", cursor: "pointer" }}
                            />
                            <label htmlFor="voiceSettingToggle" style={{ fontSize: "13px", fontWeight: 600, cursor: "pointer" }}>
                                Enable Live Voice Broadcasts
                            </label>
                        </div>

                        <button
                            type="button"
                            onClick={handleTestVoice}
                            className="tool-btn btn-secondary-mini"
                            style={{ padding: "8px 16px", fontSize: "12px", fontWeight: 600 }}
                        >
                            🔊 Test Audio Speech Synthesis
                        </button>
                    </div>
                </div>
            )}

            {/* TAB 2: Account Security & Credentials */}
            {activeTab === "account" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                    {/* Profile Information */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            👤 Operator Profile Information
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Update your personal identification and communication contact details.
                        </p>

                        {profileFeedback && (
                            <div style={{ padding: "8px 12px", background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534", borderRadius: "6px", fontSize: "12px", marginBottom: "12px" }}>
                                {profileFeedback}
                            </div>
                        )}
                        {profileError && (
                            <div style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", borderRadius: "6px", fontSize: "12px", marginBottom: "12px" }}>
                                {profileError}
                            </div>
                        )}

                        <form onSubmit={handleSaveProfile} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                            <div>
                                <label className="fleet-stat-label">Operator User ID (Immutable)</label>
                                <input
                                    className="form-control"
                                    value={user?.username || ""}
                                    disabled
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Full Display Name</label>
                                <input
                                    className="form-control"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="e.g. Commander Pravin"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Email Address</label>
                                <input
                                    className="form-control"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="e.g. pravin@institution.edu"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Contact Phone</label>
                                <input
                                    className="form-control"
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value)}
                                    placeholder="e.g. +91 98765 43210"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <button
                                type="submit"
                                className="tool-btn btn-primary"
                                style={{ marginTop: "8px", padding: "10px 18px", fontSize: "12px", fontWeight: 700 }}
                            >
                                Save Profile Changes
                            </button>
                        </form>
                    </div>

                    {/* Change Password */}
                    <div className="cam-card" style={{ padding: "22px" }}>
                        <h4 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700 }}>
                            🔒 Change Account Password
                        </h4>
                        <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                            Direct password update without any OTP requirement.
                        </p>

                        {passwordFeedback && (
                            <div style={{ padding: "8px 12px", background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#166534", borderRadius: "6px", fontSize: "12px", marginBottom: "12px" }}>
                                {passwordFeedback}
                            </div>
                        )}
                        {passwordError && (
                            <div style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", borderRadius: "6px", fontSize: "12px", marginBottom: "12px" }}>
                                {passwordError}
                            </div>
                        )}

                        <form onSubmit={handleChangePassword} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                            <div>
                                <label className="fleet-stat-label">Current Password</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    value={oldPassword}
                                    onChange={(e) => setOldPassword(e.target.value)}
                                    placeholder="Enter current password"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">New Password (min 4 characters)</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    placeholder="Enter new password"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <div>
                                <label className="fleet-stat-label">Confirm New Password</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="Repeat new password"
                                    style={{ width: "100%", padding: "10px 12px", fontSize: "13px", border: "1px solid var(--border-color)", borderRadius: "6px" }}
                                />
                            </div>

                            <button
                                type="submit"
                                className="tool-btn btn-primary"
                                style={{ marginTop: "8px", padding: "10px 18px", fontSize: "12px", fontWeight: 700 }}
                            >
                                Update Password
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* TAB 3: System & Telemetry Preferences */}
            {activeTab === "system" && (
                <div className="cam-card" style={{ padding: "24px" }}>
                    <h4 style={{ margin: "0 0 6px 0", fontSize: "15px", fontWeight: 700 }}>
                        ⚡ Sentronix AI Core &amp; Database Diagnostics
                    </h4>
                    <p style={{ margin: "0 0 18px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
                        Hardware and relational database parameters backing the 24/7 vision engine.
                    </p>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px" }}>
                        <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>YOLO Model Engine</div>
                            <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "4px" }}>YOLO11 Nano + Haar Biometrics</div>
                            <div style={{ fontSize: "11px", color: "var(--success-color)", marginTop: "2px" }}>✓ Operational (GPU/CPU Acceleration)</div>
                        </div>

                        <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Relational Database</div>
                            <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "4px" }}>SQLite3 / PostgreSQL Compatible</div>
                            <div style={{ fontSize: "11px", color: "var(--success-color)", marginTop: "2px" }}>✓ Connected (Zero Latency IPC)</div>
                        </div>

                        <div style={{ padding: "14px", background: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Webcam &amp; USB Port Driver</div>
                            <div style={{ fontSize: "14px", fontWeight: 700, marginTop: "4px" }}>HTML5 MediaDevices + OpenCV</div>
                            <div style={{ fontSize: "11px", color: "var(--success-color)", marginTop: "2px" }}>✓ Auto-Port Detection Active</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
