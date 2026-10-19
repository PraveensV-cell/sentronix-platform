import { useState, useRef, useEffect } from "react";
import { askAIAssistant } from "../api/api";

export default function AIAssistantWidget({ isOpen, onClose }) {
    const [messages, setMessages] = useState([
        {
            sender: "assistant",
            text: "Hello, I am the Sentronix AI Surveillance Operations Assistant. How can I assist you with cameras, attendance, or alerts today?",
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    if (!isOpen) return null;

    const handleSend = async (queryText) => {
        const text = queryText || input;
        if (!text.trim() || loading) return;

        const userMsg = {
            sender: "user",
            text,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res = await askAIAssistant(text);
            const assistantMsg = {
                sender: "assistant",
                text: res.reply || "Operation completed.",
                tool: res.tool_called,
                data: res.data,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    sender: "assistant",
                    text: "Error communicating with Sentronix backend services. Please ensure the API is running.",
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const quickQueries = [
        "How many students are present today?",
        "Which cameras are offline?",
        "Show active critical alerts",
        "System health status",
        "Explain alert #1"
    ];

    return (
        <div className="assistant-drawer-overlay" onClick={onClose}>
            <div className="assistant-drawer" onClick={(e) => e.stopPropagation()}>
                <div className="assistant-header">
                    <div className="assistant-title">
                        <div className="assistant-ai-pulse"></div>
                        <div>
                            <h3>Sentronix AI Operator</h3>
                            <span>Autonomous Surveillance Assistant</span>
                        </div>
                    </div>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="assistant-quick-prompts">
                    {quickQueries.map((q, idx) => (
                        <button
                            key={idx}
                            className="quick-chip"
                            onClick={() => handleSend(q)}
                            disabled={loading}
                        >
                            {q}
                        </button>
                    ))}
                </div>

                <div className="assistant-messages">
                    {messages.map((m, idx) => (
                        <div key={idx} className={`message-row ${m.sender}`}>
                            <div className="message-bubble">
                                <div className="message-text">{m.text}</div>
                                {m.tool && (
                                    <div className="tool-badge">
                                        Verified via Tool: <code>{m.tool}()</code>
                                    </div>
                                )}
                                <div className="message-time">{m.time}</div>
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="message-row assistant">
                            <div className="message-bubble typing">
                                <span>Analyzing surveillance telemetry...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <form
                    className="assistant-input-bar"
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSend();
                    }}
                >
                    <input
                        type="text"
                        placeholder="Ask about cameras, alerts, attendance, or safety events..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button type="submit" disabled={loading || !input.trim()}>
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
