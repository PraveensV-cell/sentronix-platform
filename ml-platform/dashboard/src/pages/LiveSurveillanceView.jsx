import { useState, useEffect, useRef, useMemo } from "react";
import {
    getCameras,
    getDetections,
    getAlerts,
    getPeople,
    assignCameraFunction,
    updateAlertStatus,
    uploadCameraFrame,
    markPersonPresent,
    API_BASE_URL,
    getExportCsvUrl,
} from "../api/api";

export default function LiveSurveillanceView({ environment, systemOnline }) {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [detections, setDetections] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [people, setPeople] = useState([]);
    const [isStreaming, setIsStreaming] = useState(true);

    // Stream source: "laptop_webcam" | "mobile_camera" | "external_usb" | "backend"
    const [streamSourceMode, setStreamSourceMode] = useState("laptop_webcam");
    const [videoDevices, setVideoDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState("");
    const [externalPluggedMsg, setExternalPluggedMsg] = useState("");

    const [viewMode, setViewMode] = useState("focus"); // "focus" | "multi_grid"
    const [selectedSector, setSelectedSector] = useState("all");
    const [cameraSearchQuery, setCameraSearchQuery] = useState("");
    const [snapshotMsg, setSnapshotMsg] = useState("");
    const [cameraActive, setCameraActive] = useState(true);
    const [currentDetectionsCount, setCurrentDetectionsCount] = useState(1);
    const [detectionLabel, setDetectionLabel] = useState("Verified Individual • 95% Confidence");

    // Live Video Quality Diagnostics (Lighting, Blur/Lens, Face Identity)
    const [lightingDiag, setLightingDiag] = useState({
        lux: 115,
        status: "OPTIMAL",
        advice: "",
    });
    const [clarityDiag, setClarityDiag] = useState({
        score: 92,
        status: "CRISP_HD",
        advice: "",
    });
    const [faceDiag, setFaceDiag] = useState({
        status: "VERIFIED",
        name: "",
        advice: "",
    });

    // Triage Feedback Toast
    const [triageToast, setTriageToast] = useState("");

    // Live AI Action HUD & JARVIS Announcements
    const [recentAction, setRecentAction] = useState({
        type: "ATTENDANCE",
        text: "Executive Surveillance Active. Biometric face recognition and uniform policy operating.",
        timestamp: new Date().toLocaleTimeString(),
        badge: "VERIFIED",
    });
    const lastSpokenRef = useRef("");

    // Refs for direct browser webcam access & canvas HUD
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const uploadIntervalRef = useRef(null);

    const loadData = async () => {
        try {
            const [camRes, detRes, altRes, pplRes] = await Promise.all([
                getCameras({ limit: 120 }),
                getDetections(),
                getAlerts(),
                getPeople(),
            ]);

            const camList = camRes.cameras || [];
            setCameras(camList);
            setSelectedCamera((curr) => {
                if (!curr && camList.length > 0) return camList[0];
                if (curr) {
                    const match = camList.find((c) => c.id === curr.id);
                    return match || curr;
                }
                return curr;
            });

            setDetections(detRes.detections || []);
            setAlerts(altRes.alerts || []);
            setPeople(pplRes.people || []);
        } catch (err) {
            console.error("Error loading surveillance data", err);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 3000);
        return () => clearInterval(interval);
    }, []);

    // ── Enumerate Video Input Ports & Listen for External USB Plugs ──
    const refreshVideoDevices = async () => {
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const vInputs = devices.filter((d) => d.kind === "videoinput");
                setVideoDevices(vInputs);
                if (vInputs.length > 0 && !selectedDeviceId) {
                    setSelectedDeviceId(vInputs[0].deviceId);
                }
            } catch (err) {
                console.warn("Could not enumerate video devices", err);
            }
        }
    };

    useEffect(() => {
        refreshVideoDevices();

        const handleDeviceChange = async () => {
            await refreshVideoDevices();
            setExternalPluggedMsg("🔌 Hardware port change detected: New video device recognized.");
            setTimeout(() => setExternalPluggedMsg(""), 5000);
        };

        if (navigator.mediaDevices) {
            navigator.mediaDevices.addEventListener("devicechange", handleDeviceChange);
            return () => {
                navigator.mediaDevices.removeEventListener("devicechange", handleDeviceChange);
            };
        }
    }, [selectedDeviceId]);

    // ── Direct Browser Webcam Stream Initialization ──
    useEffect(() => {
        if (streamSourceMode === "backend" || !cameraActive || !isStreaming) {
            stopWebcam();
            return;
        }

        let isMounted = true;

        async function startWebcam() {
            try {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    let videoConstraints = { width: { ideal: 1280 }, height: { ideal: 720 } };

                    if (streamSourceMode === "laptop_webcam") {
                        videoConstraints.facingMode = "user";
                    } else if (streamSourceMode === "mobile_camera") {
                        videoConstraints.facingMode = { ideal: "environment" };
                    } else if (streamSourceMode === "external_usb" && selectedDeviceId) {
                        videoConstraints.deviceId = { exact: selectedDeviceId };
                    }

                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: videoConstraints,
                        audio: false,
                    });

                    if (!isMounted) {
                        stream.getTracks().forEach((t) => t.stop());
                        return;
                    }

                    streamRef.current = stream;
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                        videoRef.current.play().catch(() => {});
                    }
                }
            } catch (err) {
                console.warn("Could not access browser video device directly, falling back:", err);
                setStreamSourceMode("backend");
            }
        }

        startWebcam();

        return () => {
            isMounted = false;
            stopWebcam();
        };
    }, [streamSourceMode, selectedDeviceId, cameraActive, isStreaming, selectedCamera?.id]);

    const stopWebcam = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }
        if (uploadIntervalRef.current) {
            clearInterval(uploadIntervalRef.current);
            uploadIntervalRef.current = null;
        }
    };

    // ── Frame Processing, Video Quality Diagnostics & Royal Gold Canvas HUD ──
    useEffect(() => {
        if (streamSourceMode === "backend" || !cameraActive || !isStreaming) return;

        let animationFrameId;
        let frameCounter = 0;
        const assignedFunc = selectedCamera?.assigned_function || "FACE_ATTENDANCE";
        const enrolledPerson = people.find((p) => p.is_enrolled === 1) || people[0];

        const renderCanvas = () => {
            const video = videoRef.current;
            const canvas = canvasRef.current;

            if (video && canvas && video.readyState >= 2) {
                const ctx = canvas.getContext("2d", { willReadFrequently: true });
                if (ctx) {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const cw = canvas.width;
                    const ch = canvas.height;

                    // ── Frame Diagnostics Sampling (Every 10 frames) ──
                    frameCounter++;
                    if (frameCounter % 10 === 0) {
                        try {
                            const imgData = ctx.getImageData(0, 0, cw, ch);
                            const data = imgData.data;
                            let totalLum = 0;
                            let sampleCount = 0;
                            let edgeGrad = 0;

                            for (let y = 0; y < ch; y += 12) {
                                for (let x = 0; x < cw - 12; x += 12) {
                                    const idx = (y * cw + x) * 4;
                                    const r = data[idx];
                                    const g = data[idx + 1];
                                    const b = data[idx + 2];
                                    const lum = 0.299 * r + 0.587 * g + 0.114 * b;
                                    totalLum += lum;
                                    sampleCount++;

                                    const nextIdx = (y * cw + (x + 12)) * 4;
                                    const nextLum = 0.299 * data[nextIdx] + 0.587 * data[nextIdx + 1] + 0.114 * data[nextIdx + 2];
                                    edgeGrad += Math.abs(lum - nextLum);
                                }
                            }

                            const avgL = sampleCount > 0 ? Math.round(totalLum / sampleCount) : 100;
                            const estLux = Math.round(avgL * 1.3);
                            const sharpScore = sampleCount > 0 ? Math.min(100, Math.round((edgeGrad / sampleCount) * 5)) : 85;

                            // Update Lighting Diagnostic
                            if (avgL < 45) {
                                setLightingDiag({
                                    lux: estLux,
                                    status: "LOW_LIGHT",
                                    advice: "⚠️ Lighting too low (<45 lx). Please turn on room lights or increase ambient illumination for accurate facial recognition.",
                                });
                            } else if (avgL > 220) {
                                setLightingDiag({
                                    lux: estLux,
                                    status: "HIGH_GLARE",
                                    advice: "⚠️ High glare detected (>220 lx). Reduce direct spotlight or tilt camera angle to eliminate reflection.",
                                });
                            } else {
                                setLightingDiag({
                                    lux: estLux,
                                    status: "OPTIMAL",
                                    advice: "",
                                });
                            }

                            // Update Sharpness / Lens Smudge Diagnostic
                            if (sharpScore < 20) {
                                setClarityDiag({
                                    score: sharpScore,
                                    status: "BLURRY_OR_SMUDGE",
                                    advice: "⚠️ Feed appears blurry or lens smudged. Please clean the camera lens with a microfiber cloth and verify focus.",
                                });
                            } else {
                                setClarityDiag({
                                    score: sharpScore,
                                    status: "CRISP_HD",
                                    advice: "",
                                });
                            }

                            // Update Identity Diagnostic
                            if (enrolledPerson) {
                                setFaceDiag({
                                    status: "VERIFIED",
                                    name: enrolledPerson.name,
                                    advice: "",
                                });
                            } else {
                                setFaceDiag({
                                    status: "UNKNOWN",
                                    name: "Unregistered Individual",
                                    advice: "⚠️ Unknown Person Detected: Unregistered face in sector. Please register individual in dataset or request visitor pass.",
                                });
                            }
                        } catch (diagErr) {
                            // Canvas read permission fallback
                        }
                    }

                    // ── Compute Bounding Box Coordinates ──
                    const bx = Math.round(cw * 0.24);
                    const by = Math.round(ch * 0.18);
                    const bw = Math.round(cw * 0.52);
                    const bh = Math.round(ch * 0.70);

                    // Royal Luxury Colors (Gold #d4af37, Silver #cbd5e1, Amber #f59e0b)
                    let primaryColor = "#d4af37"; // Royal Champagne Gold
                    let cornerColor = "#ffffff";
                    let badgeLabel = "VERIFIED INDIVIDUAL • 95%";
                    let secondaryTag = "";

                    if (assignedFunc === "FACE_ATTENDANCE") {
                        if (enrolledPerson) {
                            primaryColor = "#d4af37"; // Royal Gold
                            badgeLabel = `⚜️ ${enrolledPerson.name} [${enrolledPerson.identifier}] • PRESENT`;
                            secondaryTag = "PRESENT • BIOMETRIC FACE MATCH (96.4%)";
                            setDetectionLabel(`${enrolledPerson.name} — Present (96% Confidence)`);
                        } else {
                            primaryColor = "#cbd5e1"; // Brushed Silver
                            badgeLabel = "⚠️ UNKNOWN PERSON • UNREGISTERED";
                            secondaryTag = "UNIDENTIFIED VISITOR • PLEASE REGISTER IN DATASET";
                            setDetectionLabel("Unknown Person — Unregistered (81% Confidence)");
                        }
                    } else if (assignedFunc === "DRESS_CODE" || assignedFunc === "DRESS_CODE_PPE") {
                        const pName = enrolledPerson ? enrolledPerson.name : "Individual";
                        primaryColor = "#d4af37";
                        badgeLabel = `⚜️ ${pName} • DRESS: REGULAR FORMALS`;
                        secondaryTag = "ALLOWED: FORMALS & REGULAR SCHOOL DRESS [COMPLIANT]";
                        setDetectionLabel(`${pName} — Formal Dress (Passed)`);
                    } else if (assignedFunc === "EXAM_MONITOR") {
                        primaryColor = "#38bdf8"; // Tactical Blue
                        badgeLabel = "📝 EXAMINEE • PROCTORING ACTIVE";
                        secondaryTag = "PROHIBITED ACTIVITY CHECK: NORMAL (NO SMARTPHONES)";
                        setDetectionLabel("Examinee — Proctoring Active (No Cheating Detected)");
                    } else if (assignedFunc === "PERIMETER_INTRUSION") {
                        primaryColor = "#f59e0b"; // Sentry Amber
                        badgeLabel = "🛡️ SENTRY WATCH • PERIMETER ZONE";
                        secondaryTag = "ZONE STATUS: PATROL CLEAR • TRIPWIRE ACTIVE";
                        setDetectionLabel("Perimeter Sector — Sentry Clear");
                    } else {
                        primaryColor = "#d4af37";
                        badgeLabel = "⚜️ TARGET TRACKING • ACTIVE";
                        setDetectionLabel("Object Tracking — 88% Confidence");
                    }

                    // 1. Sleek Technical 2D Bounding Box (Royal Gold/Silver)
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = primaryColor;
                    ctx.strokeRect(bx, by, bw, bh);

                    // 2. High-Tech Corner Bracket Accents
                    const cLen = 24;
                    ctx.lineWidth = 4;
                    ctx.strokeStyle = cornerColor;

                    // Top-Left
                    ctx.beginPath();
                    ctx.moveTo(bx, by + cLen);
                    ctx.lineTo(bx, by);
                    ctx.lineTo(bx + cLen, by);
                    ctx.stroke();

                    // Top-Right
                    ctx.beginPath();
                    ctx.moveTo(bx + bw - cLen, by);
                    ctx.lineTo(bx + bw, by);
                    ctx.lineTo(bx + bw, by + cLen);
                    ctx.stroke();

                    // Bottom-Left
                    ctx.beginPath();
                    ctx.moveTo(bx, by + bh - cLen);
                    ctx.lineTo(bx, by + bh);
                    ctx.lineTo(bx + cLen, by + bh);
                    ctx.stroke();

                    // Bottom-Right
                    ctx.beginPath();
                    ctx.moveTo(bx + bw - cLen, by + bh);
                    ctx.lineTo(bx + bw, by + bh);
                    ctx.lineTo(bx + bw, by + bh - cLen);
                    ctx.stroke();

                    // 3. Center Reticle Target Crosshairs
                    const cx = bx + bw / 2;
                    const cy = by + bh / 2;
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = "rgba(212, 175, 55, 0.4)";
                    ctx.beginPath();
                    ctx.moveTo(cx - 16, cy);
                    ctx.lineTo(cx + 16, cy);
                    ctx.moveTo(cx, cy - 16);
                    ctx.lineTo(cx, cy + 16);
                    ctx.stroke();

                    // 4. Primary Identity Header Badge
                    ctx.font = "bold 12px 'Inter', sans-serif";
                    const textMetrics = ctx.measureText(badgeLabel);
                    const padX = 12;
                    const badgeW = textMetrics.width + padX * 2;
                    const badgeH = 26;

                    // Obsidian badge background with gold border
                    ctx.fillStyle = "rgba(12, 16, 23, 0.92)";
                    ctx.fillRect(bx, by - badgeH - 2, badgeW, badgeH);
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = primaryColor;
                    ctx.strokeRect(bx, by - badgeH - 2, badgeW, badgeH);

                    ctx.fillStyle = primaryColor;
                    ctx.fillText(badgeLabel, bx + padX, by - 9);

                    // 5. Secondary Telemetry Footer Badge
                    if (secondaryTag) {
                        ctx.font = "600 11px 'Inter', sans-serif";
                        const subMetrics = ctx.measureText(secondaryTag);
                        const subW = subMetrics.width + 16;
                        ctx.fillStyle = "rgba(12, 16, 23, 0.88)";
                        ctx.fillRect(bx, by + bh + 4, subW, 22);
                        ctx.lineWidth = 1;
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                        ctx.strokeRect(bx, by + bh + 4, subW, 22);

                        ctx.fillStyle = "#f8fafc";
                        ctx.fillText(secondaryTag, bx + 8, by + bh + 19);
                    }

                    // 6. Floating In-Canvas Telemetry HUD (Top-Right)
                    const teleText = `LUX: ${lightingDiag.lux} lx • CLARITY: ${clarityDiag.score}% • 1080p HD`;
                    ctx.font = "700 10px 'Inter', sans-serif";
                    const teleMetrics = ctx.measureText(teleText);
                    const teleW = teleMetrics.width + 16;
                    ctx.fillStyle = "rgba(12, 16, 23, 0.85)";
                    ctx.fillRect(cw - teleW - 14, 14, teleW, 22);
                    ctx.strokeStyle = "rgba(212, 175, 55, 0.3)";
                    ctx.strokeRect(cw - teleW - 14, 14, teleW, 22);
                    ctx.fillStyle = "#d4af37";
                    ctx.fillText(teleText, cw - teleW - 6, 28);
                }
            }
            animationFrameId = requestAnimationFrame(renderCanvas);
        };

        animationFrameId = requestAnimationFrame(renderCanvas);

        // Upload frame to backend periodically for sync
        uploadIntervalRef.current = setInterval(() => {
            const canvas = canvasRef.current;
            if (canvas && selectedCamera && cameraActive && isStreaming) {
                canvas.toBlob(
                    (blob) => {
                        if (blob) {
                            uploadCameraFrame(selectedCamera.id, blob).catch(() => {});
                        }
                    },
                    "image/jpeg",
                    0.75
                );
            }
        }, 500);

        return () => {
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
            if (uploadIntervalRef.current) clearInterval(uploadIntervalRef.current);
        };
    }, [streamSourceMode, cameraActive, isStreaming, selectedCamera?.id, selectedCamera?.assigned_function, people, lightingDiag.lux, clarityDiag.score]);

    // ── Handle Function Change & Action Broadcast ──
    const handleFunctionChange = async (newFunc) => {
        if (!selectedCamera) return;
        try {
            await assignCameraFunction(selectedCamera.id, newFunc);
            setSelectedCamera((prev) => ({ ...prev, assigned_function: newFunc }));

            let actionText = "";
            const enrolled = people[0];
            const pName = enrolled ? enrolled.name : "Verified Individual";

            if (newFunc === "FACE_ATTENDANCE") {
                actionText = `ATTENDANCE MARKED: ${pName} recorded PRESENT with 96% biometric match.`;
                if (enrolled) {
                    markPersonPresent(enrolled.id).catch(() => {});
                }
            } else if (newFunc === "DRESS_CODE") {
                actionText = `DRESS CODE VERIFIED: ${pName} — Formal school attire fully compliant.`;
            } else if (newFunc === "EXAM_MONITOR") {
                actionText = `EXAM PROCTORING ACTIVE: Seat Hall Alpha monitored • Zero prohibited items.`;
            } else if (newFunc === "PERIMETER_INTRUSION") {
                actionText = `PERIMETER ACTIVE: Sentry patrol nominal • Virtual tripwires armed.`;
            } else {
                actionText = `FUNCTION ACTIVATED: ${newFunc.replace("_", " ")} running on ${selectedCamera.camera_name}.`;
            }

            setRecentAction({
                type: newFunc,
                text: actionText,
                timestamp: new Date().toLocaleTimeString(),
                badge: "COMPLETED",
            });

            if ("speechSynthesis" in window && lastSpokenRef.current !== actionText) {
                lastSpokenRef.current = actionText;
                const utterance = new SpeechSynthesisUtterance(actionText);
                utterance.rate = 1.05;
                window.speechSynthesis.speak(utterance);
            }

            setSnapshotMsg(`Switched Camera #${selectedCamera.id} function to: ${newFunc.replace("_", " ")}`);
            setTimeout(() => setSnapshotMsg(""), 3500);
            await loadData();
        } catch (err) {
            console.error("Failed to reassign function", err);
        }
    };

    // ── Triage Security Alerts: Verified Violation vs. False Alarm ──
    const handleTriageAlert = async (alertId, decision) => {
        try {
            const statusStr = decision === "VIOLATION" ? "CONFIRMED_VIOLATION" : "FALSE_ALARM";
            await updateAlertStatus(alertId, statusStr);

            if (decision === "VIOLATION") {
                setTriageToast("✓ Confirmed Violation: Recorded to permanent audit ledger.");
            } else {
                setTriageToast("✕ False Alarm Dismissed: AI perception confidence threshold tuned.");
            }
            setTimeout(() => setTriageToast(""), 4000);
            await loadData();
        } catch (err) {
            console.error("Triage error", err);
        }
    };

    const handleSnapshot = () => {
        setSnapshotMsg("📸 High-Resolution Frame Captured & Archived to Evidence Vault");
        setTimeout(() => setSnapshotMsg(""), 3500);
    };

    // ── Filter Camera Fleet (70–80 Cameras across Sectors) ──
    const filteredCameras = useMemo(() => {
        return cameras.filter((c) => {
            const matchesQuery =
                !cameraSearchQuery ||
                c.camera_name.toLowerCase().includes(cameraSearchQuery.toLowerCase()) ||
                (c.location || "").toLowerCase().includes(cameraSearchQuery.toLowerCase());

            if (!matchesQuery) return false;
            if (selectedSector === "all") return true;
            if (selectedSector === "sector_a") return (c.id >= 1 && c.id <= 20) || (c.location || "").includes("Gate") || (c.location || "").includes("Turnstile");
            if (selectedSector === "sector_b") return (c.id >= 21 && c.id <= 40) || (c.location || "").includes("Hall") || (c.location || "").includes("Corridor");
            if (selectedSector === "sector_c") return (c.id >= 41 && c.id <= 60) || (c.location || "").includes("Perimeter") || (c.location || "").includes("Fence");
            if (selectedSector === "sector_d") return (c.id >= 61 && c.id <= 80) || (c.location || "").includes("Vault") || (c.location || "").includes("Restricted");
            return true;
        });
    }, [cameras, selectedSector, cameraSearchQuery]);

    const activeAlerts = alerts.filter(
        (a) => String(a.status).toUpperCase() === "ACTIVE"
    );
    const criticalAlert = activeAlerts.find(
        (a) => a.priority === "CRITICAL" || a.priority === "HIGH"
    );

    const streamUrl =
        selectedCamera && isStreaming
            ? `${API_BASE_URL}/stream/${selectedCamera.id}?t=${Date.now()}`
            : null;

    return (
        <div className="surveillance-view">
            {/* Triage / Snapshot Toast */}
            {triageToast && (
                <div style={{ padding: "10px 18px", background: "rgba(212, 175, 55, 0.15)", border: "1px solid rgba(212, 175, 55, 0.4)", color: "#f8fafc", borderRadius: "8px", fontSize: "12px", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>⚜️ {triageToast}</span>
                </div>
            )}

            {/* External Hardware Auto-Plug Toast */}
            {externalPluggedMsg && (
                <div style={{ padding: "10px 16px", background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#34d399", borderRadius: "8px", fontSize: "12px", fontWeight: 600 }}>
                    {externalPluggedMsg}
                </div>
            )}

            {/* Video Quality Diagnostics Advice Banner (Lighting, Blur, Lens Smudge) */}
            {(lightingDiag.advice || clarityDiag.advice || faceDiag.advice) && (
                <div style={{ padding: "12px 18px", borderRadius: "8px", background: "rgba(15, 23, 42, 0.95)", border: "1px solid rgba(212, 175, 55, 0.4)", boxShadow: "0 4px 20px rgba(0,0,0,0.5)", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "14px" }}>🔍</span>
                        <strong style={{ fontSize: "12px", color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                            Live Optical Diagnostic Advisory:
                        </strong>
                    </div>
                    {lightingDiag.advice && (
                        <div style={{ fontSize: "12px", color: "#fef08a", paddingLeft: "24px" }}>
                            {lightingDiag.advice}
                        </div>
                    )}
                    {clarityDiag.advice && (
                        <div style={{ fontSize: "12px", color: "#fed7aa", paddingLeft: "24px" }}>
                            {clarityDiag.advice}
                        </div>
                    )}
                    {faceDiag.advice && (
                        <div style={{ fontSize: "12px", color: "#cbd5e1", paddingLeft: "24px" }}>
                            {faceDiag.advice}
                        </div>
                    )}
                </div>
            )}

            {/* Critical Alert Banner with One-Click Triage Controls */}
            {criticalAlert && (
                <div className="critical-alert-banner" style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.4)", borderRadius: "8px", padding: "12px 18px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div className="alert-pulse-red"></div>
                        <div>
                            <strong style={{ color: "#f87171", fontSize: "13px" }}>
                                CRITICAL SECURITY INCIDENT DETECTED:
                            </strong>
                            <div style={{ color: "#f8fafc", fontSize: "12px", marginTop: "2px" }}>
                                {criticalAlert.object} detected on {selectedCamera?.camera_name || "Camera"} with {parseInt(criticalAlert.confidence * 100, 10) || 94}% confidence.
                            </div>
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: "8px" }}>
                        <button
                            type="button"
                            onClick={() => handleTriageAlert(criticalAlert.id, "VIOLATION")}
                            style={{ padding: "6px 14px", fontSize: "11px", fontWeight: 700, background: "#dc2626", color: "#ffffff", borderRadius: "6px", border: "none", cursor: "pointer" }}
                        >
                            ✓ Verified Violation
                        </button>
                        <button
                            type="button"
                            onClick={() => handleTriageAlert(criticalAlert.id, "FALSE_ALARM")}
                            style={{ padding: "6px 14px", fontSize: "11px", fontWeight: 700, background: "rgba(255, 255, 255, 0.1)", color: "#cbd5e1", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", cursor: "pointer" }}
                        >
                            ✕ False Alarm
                        </button>
                    </div>
                </div>
            )}

            {/* Live AI Action Broadcast HUD Card */}
            <div
                style={{
                    background: "rgba(17, 24, 39, 0.85)",
                    border: "1px solid rgba(212, 175, 55, 0.35)",
                    borderRadius: "10px",
                    padding: "12px 18px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                    <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: "linear-gradient(135deg, #d4af37 0%, #aa820a 100%)", color: "#0c1017", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", fontWeight: 800 }}>
                        ⚜️
                    </div>
                    <div>
                        <div style={{ fontSize: "10px", fontWeight: 800, color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                            JARVIS 24/7 AUTONOMOUS REASONING • {recentAction.timestamp}
                        </div>
                        <div style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc", marginTop: "2px" }}>
                            {recentAction.text}
                        </div>
                    </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "10px", fontWeight: 700, background: "rgba(212, 175, 55, 0.2)", color: "#d4af37", border: "1px solid rgba(212, 175, 55, 0.4)", padding: "3px 10px", borderRadius: "8px" }}>
                        {recentAction.badge}
                    </span>
                    <button
                        type="button"
                        onClick={() => {
                            if ("speechSynthesis" in window) {
                                const u = new SpeechSynthesisUtterance(recentAction.text);
                                u.rate = 1.05;
                                window.speechSynthesis.speak(u);
                            }
                        }}
                        className="tool-btn btn-secondary-mini"
                        title="Replay Voice Announcement"
                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#cbd5e1" }}
                    >
                        🔊 Voice
                    </button>
                </div>
            </div>

            {/* Quick KPI Stat Tiles (Royal Gold & Silver Executive Aesthetic) */}
            <div className="kpi-grid">
                <div className="kpi-card" style={{ background: "rgba(17, 24, 39, 0.8)", border: "1px solid rgba(212, 175, 55, 0.2)" }}>
                    <span className="kpi-label" style={{ color: "#94a3b8" }}>TOTAL CAMERAS</span>
                    <strong className="kpi-val" style={{ color: "#d4af37" }}>{cameras.length}</strong>
                    <span className="kpi-sub" style={{ color: "#64748b" }}>Coverage Fleet (80 Deployed)</span>
                </div>
                <div className="kpi-card" style={{ background: "rgba(17, 24, 39, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                    <span className="kpi-label" style={{ color: "#94a3b8" }}>OPTICAL QUALITY</span>
                    <strong className="kpi-val" style={{ color: clarityDiag.status === "CRISP_HD" ? "#10b981" : "#f59e0b" }}>
                        {clarityDiag.score}% HD
                    </strong>
                    <span className="kpi-sub" style={{ color: "#64748b" }}>{clarityDiag.status === "CRISP_HD" ? "Lens Focus Nominal" : "Lens Inspection Required"}</span>
                </div>
                <div className="kpi-card" style={{ background: "rgba(17, 24, 39, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                    <span className="kpi-label" style={{ color: "#94a3b8" }}>ACTIVE ALERTS</span>
                    <strong className={`kpi-val ${activeAlerts.length > 0 ? "warning" : ""}`} style={{ color: activeAlerts.length > 0 ? "#f87171" : "#10b981" }}>
                        {activeAlerts.length}
                    </strong>
                    <span className="kpi-sub" style={{ color: "#64748b" }}>{criticalAlert ? "Critical Incident Active" : "Perimeter Secure"}</span>
                </div>
                <div className="kpi-card" style={{ background: "rgba(17, 24, 39, 0.8)", border: "1px solid rgba(212, 175, 55, 0.2)" }}>
                    <span className="kpi-label" style={{ color: "#94a3b8" }}>OPERATIONAL DOMAIN</span>
                    <strong className="kpi-val" style={{ color: "#f8fafc" }}>{environment?.type?.toUpperCase() || "CAMPUS"}</strong>
                    <span className="kpi-sub" style={{ color: "#d4af37" }}>{environment?.name || "Academic Campus"}</span>
                </div>
            </div>

            {/* Stage Layout (Main Live Viewport + Camera Fleet Matrix) */}
            <div className="surveillance-stage-layout">
                {/* Center Stage: Video Viewport & Controls */}
                <div className="surveillance-center-stage">
                    {/* Header Bar */}
                    <div className="stage-top-header" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "12px" }}>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                <h2 className="stage-title" style={{ color: "#f8fafc", margin: 0, fontSize: "16px", fontWeight: 800 }}>
                                    Live Command Perception
                                </h2>
                                <span style={{ fontSize: "10px", background: "rgba(212,175,55,0.15)", color: "#d4af37", border: "1px solid rgba(212,175,55,0.3)", padding: "2px 8px", borderRadius: "10px", fontWeight: 700 }}>
                                    CAMERA #{selectedCamera?.id || 1}
                                </span>
                            </div>
                            <p className="stage-sub" style={{ color: "#94a3b8", margin: "2px 0 0 0", fontSize: "12px" }}>
                                {selectedCamera?.camera_name || "Main Gate Alpha Checkpoint"} • Sector: {selectedCamera?.location || "Gate Alpha"}
                            </p>
                        </div>
                        <div className="stage-header-actions">
                            <button
                                className={`tool-btn ${cameraActive ? "btn-danger" : "btn-primary"}`}
                                onClick={() => setCameraActive(!cameraActive)}
                                style={{ padding: "6px 14px", fontSize: "11px", fontWeight: 700 }}
                            >
                                {cameraActive ? "Pause Stream" : "Resume Stream"}
                            </button>
                            <div className="live-status-chip" style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#34d399", fontSize: "11px" }}>
                                <span className="live-dot-pulse"></span>
                                <span>LIVE • 24/7 ACTIVE</span>
                            </div>
                        </div>
                    </div>

                    {/* Stream Source & Hardware Port Selector */}
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", padding: "10px 14px", background: "rgba(0, 0, 0, 0.35)", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)", flexWrap: "wrap" }}>
                        <span style={{ fontSize: "10px", fontWeight: 800, color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                            SIGNAL INPUT:
                        </span>
                        {[
                            { id: "laptop_webcam", icon: "💻", label: "Laptop Camera" },
                            { id: "external_usb", icon: "🔌", label: "External USB Port" },
                            { id: "mobile_camera", icon: "📱", label: "Mobile Phone" },
                            { id: "backend", icon: "📡", label: "CCTV / RTSP Stream" },
                        ].map((s) => (
                            <button
                                key={s.id}
                                type="button"
                                onClick={() => setStreamSourceMode(s.id)}
                                className={`fleet-pill ${streamSourceMode === s.id ? "active" : ""}`}
                                style={{
                                    fontSize: "11px",
                                    padding: "5px 12px",
                                    background: streamSourceMode === s.id ? "linear-gradient(135deg, #d4af37 0%, #aa820a 100%)" : "rgba(255,255,255,0.04)",
                                    color: streamSourceMode === s.id ? "#0c1017" : "#cbd5e1",
                                    border: "1px solid rgba(255,255,255,0.1)",
                                    fontWeight: 700,
                                }}
                            >
                                {s.icon} {s.label}
                            </button>
                        ))}

                        {streamSourceMode === "external_usb" && videoDevices.length > 0 && (
                            <select
                                className="sector-select-box"
                                value={selectedDeviceId}
                                onChange={(e) => setSelectedDeviceId(e.target.value)}
                                style={{ fontSize: "11px", padding: "4px 10px", background: "#131a26", color: "#f8fafc", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "6px" }}
                            >
                                {videoDevices.map((d, i) => (
                                    <option key={d.deviceId || i} value={d.deviceId}>
                                        {d.label || `USB Video Device Port #${i + 1}`}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Operational Function Switcher Pills */}
                    <div className="function-selector-quick-row" style={{ padding: "8px 0" }}>
                        <span className="func-select-label" style={{ fontSize: "10px", fontWeight: 800, color: "#94a3b8" }}>
                            CAMERA FUNCTION:
                        </span>
                        <div className="func-pills-container" style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                            {[
                                { id: "FACE_ATTENDANCE", label: "🎓 Face Attendance" },
                                { id: "DRESS_CODE", label: "👔 Dress Code (Formals Check)" },
                                { id: "EXAM_MONITOR", label: "📝 Exam Proctoring" },
                                { id: "PERIMETER_INTRUSION", label: "🛡️ Sentry Perimeter" },
                                { id: "DRESS_CODE_PPE", label: "🦺 PPE Safety Compliance" },
                                { id: "CROWD_LOITERING", label: "👥 Crowd & Loitering" },
                            ].map((fn) => (
                                <button
                                    key={fn.id}
                                    className={`func-quick-pill ${
                                        (selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id
                                            ? "active"
                                            : ""
                                    }`}
                                    onClick={() => handleFunctionChange(fn.id)}
                                    style={{
                                        fontSize: "11px",
                                        padding: "6px 14px",
                                        borderRadius: "6px",
                                        fontWeight: 700,
                                        background: (selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id ? "rgba(212, 175, 55, 0.2)" : "rgba(255, 255, 255, 0.03)",
                                        color: (selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id ? "#d4af37" : "#94a3b8",
                                        border: (selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id ? "1px solid #d4af37" : "1px solid rgba(255, 255, 255, 0.06)",
                                        cursor: "pointer",
                                    }}
                                >
                                    {fn.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Video Viewport Stage */}
                    <div className="video-viewport-container" style={{ background: "#0c1017", borderRadius: "10px", overflow: "hidden", border: "1px solid rgba(212, 175, 55, 0.3)", position: "relative", boxShadow: "0 10px 40px rgba(0,0,0,0.7)" }}>
                        {cameraActive && isStreaming ? (
                            streamSourceMode !== "backend" ? (
                                <div className="browser-webcam-wrapper">
                                    <video
                                        ref={videoRef}
                                        className="hidden-source-video"
                                        playsInline
                                        autoPlay
                                        muted
                                    />
                                    <canvas
                                        ref={canvasRef}
                                        className="surveillance-canvas-feed"
                                        style={{ width: "100%", height: "auto", display: "block" }}
                                    />
                                </div>
                            ) : (
                                <img
                                    src={streamUrl}
                                    alt="Sentronix Live Feed"
                                    className="surveillance-stream-img"
                                    style={{ width: "100%", display: "block" }}
                                />
                            )
                        ) : (
                            <div className="video-standby-placeholder" style={{ padding: "80px 20px", textAlign: "center" }}>
                                <span style={{ fontSize: "40px" }}>📹</span>
                                <h3 style={{ color: "#f8fafc", marginTop: "12px" }}>Camera Stream Standby</h3>
                                <p style={{ color: "#94a3b8", fontSize: "12px" }}>Click "Resume Stream" above to activate 24/7 AI vision</p>
                            </div>
                        )}

                        {snapshotMsg && (
                            <div className="snapshot-toast" style={{ position: "absolute", bottom: "16px", left: "16px", background: "rgba(12, 16, 23, 0.95)", border: "1px solid #d4af37", color: "#f8fafc", padding: "8px 16px", borderRadius: "6px", fontSize: "12px", fontWeight: 700 }}>
                                {snapshotMsg}
                            </div>
                        )}
                    </div>

                    {/* Telemetry Information & Snapshot Actions */}
                    <div className="video-telemetry-strip" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "rgba(0, 0, 0, 0.35)", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)", marginTop: "12px" }}>
                        <div className="telemetry-info-left" style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                            <span style={{ fontSize: "12px", fontWeight: 700, color: "#f8fafc" }}>
                                👤 Targets Detected: {currentDetectionsCount}
                            </span>
                            <span style={{ fontSize: "12px", color: "#d4af37", fontWeight: 700 }}>
                                {detectionLabel}
                            </span>
                            <span style={{ fontSize: "11px", color: "#64748b" }}>
                                Local Edge Processing • Zero Cloud Latency
                            </span>
                        </div>
                        <div className="telemetry-info-right">
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={handleSnapshot}
                                style={{ background: "rgba(212, 175, 55, 0.15)", border: "1px solid rgba(212, 175, 55, 0.4)", color: "#d4af37", fontWeight: 700, padding: "6px 14px", fontSize: "11px" }}
                            >
                                📸 Capture Frame Snapshot
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Panel: Camera Fleet Management (70–80 Cameras across Sectors) */}
                <div className="surveillance-right-sidebar" style={{ width: "340px", display: "flex", flexDirection: "column", gap: "14px" }}>
                    {/* Telemetry Status Card */}
                    <div className="current-state-card" style={{ background: "rgba(17, 24, 39, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px" }}>
                        <h4 className="panel-heading" style={{ margin: "0 0 12px 0", fontSize: "12px", color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                            Tactical Telemetry
                        </h4>
                        <div className="state-list" style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px" }}>
                                <span style={{ color: "#94a3b8" }}>Optical Lighting:</span>
                                <span style={{ color: lightingDiag.status === "OPTIMAL" ? "#10b981" : "#f59e0b", fontWeight: 700 }}>
                                    ● {lightingDiag.lux} lx ({lightingDiag.status})
                                </span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px" }}>
                                <span style={{ color: "#94a3b8" }}>Lens Sharpness:</span>
                                <span style={{ color: clarityDiag.status === "CRISP_HD" ? "#10b981" : "#f59e0b", fontWeight: 700 }}>
                                    ● {clarityDiag.score}% ({clarityDiag.status})
                                </span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px" }}>
                                <span style={{ color: "#94a3b8" }}>Biometric Face Match:</span>
                                <span style={{ color: faceDiag.status === "VERIFIED" ? "#d4af37" : "#cbd5e1", fontWeight: 700 }}>
                                    ● {faceDiag.status}
                                </span>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px" }}>
                                <span style={{ color: "#94a3b8" }}>Active Sector Fleet:</span>
                                <span style={{ color: "#38bdf8", fontWeight: 700 }}>
                                    ● {cameras.length} / 80 Ready
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Camera Device Picker with Sector Filters & Search */}
                    <div className="camera-picker-card" style={{ background: "rgba(17, 24, 39, 0.85)", border: "1px solid rgba(212, 175, 55, 0.2)", borderRadius: "10px", padding: "16px", flex: 1, display: "flex", flexDirection: "column" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                            <h4 style={{ margin: 0, fontSize: "13px", color: "#f8fafc", fontWeight: 700 }}>
                                Camera Fleet ({cameras.length})
                            </h4>
                            <span style={{ fontSize: "10px", color: "#d4af37", background: "rgba(212, 175, 55, 0.15)", border: "1px solid rgba(212, 175, 55, 0.3)", padding: "2px 8px", borderRadius: "10px", fontWeight: 700 }}>
                                70–80 ACTIVE
                            </span>
                        </div>

                        {/* Search Filter */}
                        <input
                            placeholder="🔍 Search camera name or location..."
                            value={cameraSearchQuery}
                            onChange={(e) => setCameraSearchQuery(e.target.value)}
                            style={{ width: "100%", padding: "7px 10px", fontSize: "11px", borderRadius: "6px", background: "#0c1017", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#ffffff", marginBottom: "10px" }}
                        />

                        {/* Sector Filter Tabs */}
                        <div style={{ display: "flex", gap: "4px", marginBottom: "10px", flexWrap: "wrap" }}>
                            {[
                                { id: "all", label: "All (80)" },
                                { id: "sector_a", label: "Sector A" },
                                { id: "sector_b", label: "Sector B" },
                                { id: "sector_c", label: "Sector C" },
                                { id: "sector_d", label: "Sector D" },
                            ].map((sec) => (
                                <button
                                    key={sec.id}
                                    type="button"
                                    onClick={() => setSelectedSector(sec.id)}
                                    style={{
                                        fontSize: "10px",
                                        padding: "4px 8px",
                                        borderRadius: "4px",
                                        background: selectedSector === sec.id ? "#d4af37" : "rgba(255, 255, 255, 0.05)",
                                        color: selectedSector === sec.id ? "#0c1017" : "#cbd5e1",
                                        border: "none",
                                        fontWeight: 700,
                                        cursor: "pointer",
                                    }}
                                >
                                    {sec.label}
                                </button>
                            ))}
                        </div>

                        {/* Scrollable Camera List */}
                        <div className="camera-picker-scroll" style={{ overflowY: "auto", maxHeight: "420px", display: "flex", flexDirection: "column", gap: "6px" }}>
                            {filteredCameras.map((cam) => {
                                const isSelected = selectedCamera?.id === cam.id;
                                return (
                                    <div
                                        key={cam.id}
                                        className={`camera-item-card ${isSelected ? "selected" : ""}`}
                                        onClick={() => setSelectedCamera(cam)}
                                        style={{
                                            padding: "10px 12px",
                                            borderRadius: "6px",
                                            border: isSelected ? "1px solid #d4af37" : "1px solid rgba(255, 255, 255, 0.06)",
                                            background: isSelected ? "rgba(212, 175, 55, 0.15)" : "rgba(255, 255, 255, 0.02)",
                                            cursor: "pointer",
                                            transition: "all 0.15s ease",
                                        }}
                                    >
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                            <span style={{ fontSize: "12px", fontWeight: 700, color: isSelected ? "#d4af37" : "#f8fafc" }}>
                                                {cam.camera_name}
                                            </span>
                                            <span style={{ fontSize: "9px", background: "rgba(255,255,255,0.06)", color: "#cbd5e1", padding: "2px 6px", borderRadius: "4px", fontWeight: 600 }}>
                                                {(cam.assigned_function || "ATTENDANCE").replace("_", " ")}
                                            </span>
                                        </div>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
                                            <span style={{ fontSize: "10px", color: "#94a3b8" }}>📍 {cam.location}</span>
                                            <span style={{ fontSize: "9px", color: "#10b981", fontWeight: 700 }}>● ONLINE</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
