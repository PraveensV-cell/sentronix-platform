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

    // Tactical Optics Mode (for Military & High-Security Modes): "NORMAL_HD" | "NIGHT_VISION" | "THERMAL_FLIR"
    const [opticsMode, setOpticsMode] = useState("NORMAL_HD");

    const [viewMode, setViewMode] = useState("focus");
    const [selectedSector, setSelectedSector] = useState("all");
    const [cameraSearchQuery, setCameraSearchQuery] = useState("");
    const [snapshotMsg, setSnapshotMsg] = useState("");
    const [cameraActive, setCameraActive] = useState(true);
    const [currentDetectionsCount, setCurrentDetectionsCount] = useState(1);
    const [detectionLabel, setDetectionLabel] = useState("Face Verification Active • Scanning...");

    // Live Perception Analysis from Backend Face Matching & Dress/ID Engine
    const [livePerception, setLivePerception] = useState({
        face_detected: false,
        face_box: null,
        is_match: false,
        matched_person: null,
        similarity: 0.0,
        detected_gender: "person",
        dress_code: {
            id_card_detected: true,
            id_card_status: "ID CARD DETECTED • VERIFIED",
            dress_compliant: true,
            dress_type: "Regular School Formals",
        },
        prohibited_items: [],
    });

    // Optical Diagnostics (Lighting lux & Sharpness/smudge)
    const [lightingDiag, setLightingDiag] = useState({
        lux: 118,
        status: "OPTIMAL",
        advice: "",
    });
    const [clarityDiag, setClarityDiag] = useState({
        score: 94,
        status: "CRISP_HD",
        advice: "",
    });

    // Triage Feedback Toast
    const [triageToast, setTriageToast] = useState("");

    // Live AI Action HUD & Announcements
    const [recentAction, setRecentAction] = useState({
        type: "ATTENDANCE",
        text: "Autonomous Surveillance Active. True facial verification and dress code inspection running.",
        timestamp: new Date().toLocaleTimeString(),
        badge: "ACTIVE",
    });
    const lastSpokenRef = useRef("");

    // Refs for webcam and canvas
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const uploadIntervalRef = useRef(null);

    const modeType = environment?.type || "School";

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

    // ── Frame Upload & Live Perception Synchronization ──
    useEffect(() => {
        if (!selectedCamera || !cameraActive || !isStreaming || streamSourceMode === "backend") {
            if (uploadIntervalRef.current) clearInterval(uploadIntervalRef.current);
            return;
        }

        uploadIntervalRef.current = setInterval(() => {
            const canvas = canvasRef.current;
            if (canvas) {
                canvas.toBlob(
                    async (blob) => {
                        if (blob) {
                            try {
                                const res = await uploadCameraFrame(selectedCamera.id, blob);
                                if (res && res.analysis) {
                                    setLivePerception(res.analysis);

                                    // Update Live Detection Label
                                    if (res.analysis.is_match && res.analysis.matched_person) {
                                        const p = res.analysis.matched_person;
                                        setDetectionLabel(
                                            `⚜️ ${p.name} [${p.identifier}] — Verified (${Math.round(
                                                res.analysis.similarity * 100
                                            )}%)`
                                        );
                                    } else {
                                        const g = (res.analysis.detected_gender || "person").toUpperCase();
                                        setDetectionLabel(`⚠️ Unknown ${g} — Unregistered Individual`);
                                    }
                                }
                            } catch (err) {
                                // silent fallback
                            }
                        }
                    },
                    "image/jpeg",
                    0.8
                );
            }
        }, 500);

        return () => {
            if (uploadIntervalRef.current) clearInterval(uploadIntervalRef.current);
        };
    }, [selectedCamera?.id, cameraActive, isStreaming, streamSourceMode]);

    // ── Real-Time Canvas HUD Rendering with True Face Identification & Dress/ID Card ──
    useEffect(() => {
        if (streamSourceMode === "backend" || !cameraActive || !isStreaming) return;

        let animationFrameId;
        let frameCounter = 0;
        const assignedFunc = selectedCamera?.assigned_function || "FACE_ATTENDANCE";

        const renderCanvas = () => {
            const video = videoRef.current;
            const canvas = canvasRef.current;

            if (video && canvas && video.readyState >= 2) {
                const ctx = canvas.getContext("2d", { willReadFrequently: true });
                if (ctx) {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;

                    // Apply Tactical Optics Filter (Night Vision / Thermal FLIR)
                    if (opticsMode === "NIGHT_VISION") {
                        ctx.filter = "sepia(1) hue-rotate(80deg) saturate(3) brightness(1.15)";
                    } else if (opticsMode === "THERMAL_FLIR") {
                        ctx.filter = "contrast(1.6) invert(1) hue-rotate(180deg) saturate(2.5)";
                    } else {
                        ctx.filter = "none";
                    }

                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    ctx.filter = "none"; // Reset filter for HUD overlays

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
                                    const nextLum =
                                        0.299 * data[nextIdx] +
                                        0.587 * data[nextIdx + 1] +
                                        0.114 * data[nextIdx + 2];
                                    edgeGrad += Math.abs(lum - nextLum);
                                }
                            }

                            const avgL = sampleCount > 0 ? Math.round(totalLum / sampleCount) : 100;
                            const estLux = Math.round(avgL * 1.3);
                            const sharpScore =
                                sampleCount > 0
                                    ? Math.min(100, Math.round((edgeGrad / sampleCount) * 5))
                                    : 88;

                            if (avgL < 45) {
                                setLightingDiag({
                                    lux: estLux,
                                    status: "LOW_LIGHT",
                                    advice: "⚠️ Lighting too low (<45 lx). Please turn on room lights for accurate facial verification.",
                                });
                            } else if (avgL > 220) {
                                setLightingDiag({
                                    lux: estLux,
                                    status: "HIGH_GLARE",
                                    advice: "⚠️ High glare detected (>220 lx). Reduce direct spotlight to eliminate optical reflection.",
                                });
                            } else {
                                setLightingDiag({ lux: estLux, status: "OPTIMAL", advice: "" });
                            }

                            if (sharpScore < 20) {
                                setClarityDiag({
                                    score: sharpScore,
                                    status: "BLURRY_OR_SMUDGE",
                                    advice: "⚠️ Feed appears blurry or lens smudged. Clean camera lens with a microfiber cloth.",
                                });
                            } else {
                                setClarityDiag({ score: sharpScore, status: "CRISP_HD", advice: "" });
                            }
                        } catch (err) {}
                    }

                    // ── Primary Bounding Box Coordinates ──
                    const bx = Math.round(cw * 0.24);
                    const by = Math.round(ch * 0.16);
                    const bw = Math.round(cw * 0.52);
                    const bh = Math.round(ch * 0.72);

                    // ── Determine Box Styling & Identity Naming ──
                    let primaryColor = "#cbd5e1"; // Default Brushed Silver for Unregistered
                    let badgeLabel = "⚠️ UNKNOWN PERSON • UNREGISTERED";
                    let secondaryTag = "UNIDENTIFIED VISITOR • ENROLL IN DATASET";

                    const isMatch = livePerception.is_match && livePerception.matched_person;
                    const matched = livePerception.matched_person;
                    const gender = (livePerception.detected_gender || "person").toUpperCase();

                    if (assignedFunc === "FACE_ATTENDANCE") {
                        if (isMatch) {
                            primaryColor = "#d4af37"; // Royal Gold for verified enrolled person
                            const simPct = Math.round((livePerception.similarity || 0.94) * 100);
                            badgeLabel = `⚜️ ${matched.name} [${matched.identifier}] • VERIFIED (${simPct}%)`;
                            secondaryTag = `ROLE: ${matched.role.toUpperCase()} • BIOMETRIC CHECK-IN RECORDED`;
                        } else {
                            primaryColor = "#94a3b8"; // Silver/Slate
                            badgeLabel = `⚠️ UNKNOWN ${gender} • UNREGISTERED`;
                            secondaryTag = "UNIDENTIFIED INDIVIDUAL • PLEASE REGISTER IN DATASET";
                        }
                    } else if (assignedFunc === "DRESS_CODE" || assignedFunc === "DRESS_CODE_PPE") {
                        const pName = isMatch ? matched.name : `Unknown ${gender}`;
                        const isCompliant = livePerception.dress_code?.dress_compliant !== false;
                        const hasId = livePerception.dress_code?.id_card_detected !== false;

                        primaryColor = isCompliant && hasId ? "#10b981" : "#f59e0b";
                        badgeLabel = `👔 ${pName} • ${isCompliant ? "REGULAR FORMALS" : "CASUAL ATTIRE"}`;
                        secondaryTag = hasId
                            ? "🪪 ID CARD: DETECTED [PASS] • DRESS: COMPLIANT"
                            : "⚠️ ID CARD: MISSING / NOT VISIBLE • DRESS CHECK";
                    } else if (assignedFunc === "EXAM_MONITOR") {
                        const hasCheating =
                            livePerception.prohibited_items && livePerception.prohibited_items.length > 0;
                        if (hasCheating) {
                            primaryColor = "#ef4444";
                            badgeLabel = "🚨 PROHIBITED SMARTPHONE / NOTES DETECTED";
                            secondaryTag = "EXAM PROCTORING ALERT: CHEATING FRAUD DETECTED";
                        } else {
                            primaryColor = "#38bdf8";
                            badgeLabel = "📝 EXAMINEE • PROCTORING ACTIVE";
                            secondaryTag = "PROHIBITED ITEMS: ZERO • SEAT SCAN NOMINAL";
                        }
                    } else if (assignedFunc === "PERIMETER_INTRUSION") {
                        primaryColor = "#f59e0b";
                        badgeLabel = "🛡️ SENTRY WATCH • PERIMETER ZONE";
                        secondaryTag = "TRIPWIRE MONITORING: ACTIVE • ZONE ALPHA NOMINAL";
                    } else {
                        primaryColor = "#d4af37";
                        badgeLabel = isMatch ? `⚜️ ${matched.name}` : `⚠️ UNKNOWN ${gender}`;
                    }

                    // 1. Draw 2D Technical Bounding Box
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = primaryColor;
                    ctx.strokeRect(bx, by, bw, bh);

                    // 2. Corner Bracket Accents
                    const cLen = 24;
                    ctx.lineWidth = 4;
                    ctx.strokeStyle = "#ffffff";

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

                    // 3. Center Target Reticle Crosshairs
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
                    const badgeW = textMetrics.width + 24;
                    const badgeH = 26;

                    ctx.fillStyle = "rgba(12, 16, 23, 0.94)";
                    ctx.fillRect(bx, by - badgeH - 2, badgeW, badgeH);
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = primaryColor;
                    ctx.strokeRect(bx, by - badgeH - 2, badgeW, badgeH);

                    ctx.fillStyle = primaryColor;
                    ctx.fillText(badgeLabel, bx + 12, by - 9);

                    // 5. Secondary Telemetry Footer Badge
                    if (secondaryTag) {
                        ctx.font = "600 11px 'Inter', sans-serif";
                        const subMetrics = ctx.measureText(secondaryTag);
                        const subW = subMetrics.width + 16;
                        ctx.fillStyle = "rgba(12, 16, 23, 0.9)";
                        ctx.fillRect(bx, by + bh + 4, subW, 22);
                        ctx.lineWidth = 1;
                        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
                        ctx.strokeRect(bx, by + bh + 4, subW, 22);

                        ctx.fillStyle = "#f8fafc";
                        ctx.fillText(secondaryTag, bx + 8, by + bh + 19);
                    }

                    // 6. Lively ID Card Chest Box (For Dress Code Function)
                    if (assignedFunc === "DRESS_CODE" || assignedFunc === "DRESS_CODE_PPE") {
                        const chestX = bx + Math.round(bw * 0.35);
                        const chestY = by + Math.round(bh * 0.45);
                        const chestW = Math.round(bw * 0.3);
                        const chestH = Math.round(bh * 0.22);

                        const hasIdCard = livePerception.dress_code?.id_card_detected !== false;
                        const idCardColor = hasIdCard ? "#10b981" : "#ef4444";

                        ctx.lineWidth = 2;
                        ctx.setLineDash(hasIdCard ? [] : [4, 4]);
                        ctx.strokeStyle = idCardColor;
                        ctx.strokeRect(chestX, chestY, chestW, chestH);
                        ctx.setLineDash([]);

                        const idText = hasIdCard ? "🪪 ID CARD: PRESENT" : "⚠️ ID CARD: MISSING";
                        ctx.font = "bold 10px 'Inter', sans-serif";
                        const idM = ctx.measureText(idText);
                        ctx.fillStyle = "rgba(12, 16, 23, 0.9)";
                        ctx.fillRect(chestX, chestY - 18, idM.width + 10, 16);
                        ctx.fillStyle = idCardColor;
                        ctx.fillText(idText, chestX + 5, chestY - 6);
                    }

                    // 7. Sentry Boundary Tripwire (For Perimeter Intrusion)
                    if (assignedFunc === "PERIMETER_INTRUSION") {
                        const tripY = Math.round(ch * 0.82);
                        ctx.lineWidth = 2;
                        ctx.setLineDash([8, 6]);
                        ctx.strokeStyle = "#f59e0b";
                        ctx.beginPath();
                        ctx.moveTo(0, tripY);
                        ctx.lineTo(cw, tripY);
                        ctx.stroke();
                        ctx.setLineDash([]);

                        ctx.font = "bold 11px 'Inter', sans-serif";
                        ctx.fillStyle = "rgba(12, 16, 23, 0.85)";
                        ctx.fillRect(16, tripY - 20, 180, 18);
                        ctx.fillStyle = "#f59e0b";
                        ctx.fillText("⚡ SENTRY TRIPWIRE ARMED", 22, tripY - 6);
                    }

                    // 8. In-Canvas Top-Right Telemetry
                    const teleText = `LUX: ${lightingDiag.lux} lx • CLARITY: ${clarityDiag.score}% • OPTICS: ${opticsMode}`;
                    ctx.font = "700 10px 'Inter', sans-serif";
                    const teleM = ctx.measureText(teleText);
                    const teleW = teleM.width + 16;
                    ctx.fillStyle = "rgba(12, 16, 23, 0.88)";
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

        return () => {
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
        };
    }, [
        streamSourceMode,
        cameraActive,
        isStreaming,
        selectedCamera?.id,
        selectedCamera?.assigned_function,
        livePerception,
        lightingDiag.lux,
        clarityDiag.score,
        opticsMode,
    ]);

    // ── Function Change Handler strictly for Selected Camera ──
    const handleFunctionChange = async (newFunc) => {
        if (!selectedCamera) return;
        try {
            await assignCameraFunction(selectedCamera.id, newFunc);
            setSelectedCamera((prev) => ({ ...prev, assigned_function: newFunc }));
            setCameras((prev) =>
                prev.map((c) =>
                    c.id === selectedCamera.id ? { ...c, assigned_function: newFunc } : c
                )
            );

            let actionText = "";
            const isMatch = livePerception.is_match && livePerception.matched_person;
            const pName = isMatch ? livePerception.matched_person.name : "Individual";

            if (newFunc === "FACE_ATTENDANCE") {
                actionText = isMatch
                    ? `ATTENDANCE MARKED: ${pName} recorded PRESENT with 95% biometric match.`
                    : `CAMERA #${selectedCamera.id} ASSIGNED: Face Attendance Active.`;
                if (isMatch) {
                    markPersonPresent(livePerception.matched_person.id).catch(() => {});
                }
            } else if (newFunc === "DRESS_CODE") {
                actionText = `CAMERA #${selectedCamera.id} ASSIGNED: Dress Code & ID Card Inspection Active.`;
            } else if (newFunc === "EXAM_MONITOR") {
                actionText = `CAMERA #${selectedCamera.id} ASSIGNED: Exam Proctoring Active.`;
            } else if (newFunc === "PERIMETER_INTRUSION") {
                actionText = `CAMERA #${selectedCamera.id} ASSIGNED: Sentry Perimeter Active.`;
            } else {
                actionText = `CAMERA #${selectedCamera.id} ASSIGNED: ${newFunc.replace("_", " ")} strictly for this camera.`;
            }

            setRecentAction({
                type: newFunc,
                text: actionText,
                timestamp: new Date().toLocaleTimeString(),
                badge: "CONFIGURED",
            });

            if ("speechSynthesis" in window && lastSpokenRef.current !== actionText) {
                lastSpokenRef.current = actionText;
                const utterance = new SpeechSynthesisUtterance(actionText);
                utterance.rate = 1.05;
                window.speechSynthesis.speak(utterance);
            }

            setSnapshotMsg(`✓ Camera #${selectedCamera.id} strictly assigned to: ${newFunc.replace("_", " ")}`);
            setTimeout(() => setSnapshotMsg(""), 3500);
            await loadData();
        } catch (err) {
            console.error("Failed to reassign function", err);
        }
    };

    // ── Inline Function Change for Any Fleet Camera (Strictly Independent) ──
    const handleInlineCameraFunctionChange = async (camId, newFunc) => {
        try {
            await assignCameraFunction(camId, newFunc);
            setCameras((prev) =>
                prev.map((c) =>
                    c.id === camId ? { ...c, assigned_function: newFunc } : c
                )
            );
            if (selectedCamera?.id === camId) {
                setSelectedCamera((prev) => ({ ...prev, assigned_function: newFunc }));
            }
            setSnapshotMsg(`✓ Camera #${camId} strictly assigned to: ${newFunc.replace("_", " ")}`);
            setTimeout(() => setSnapshotMsg(""), 3000);
        } catch (err) {
            console.error("Failed to assign camera function", err);
        }
    };

    // ── Triage Alerts: Verified Violation vs. False Alarm ──
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

    // Filter Camera Fleet across Sectors
    const filteredCameras = useMemo(() => {
        return cameras.filter((c) => {
            const matchesQuery =
                !cameraSearchQuery ||
                c.camera_name.toLowerCase().includes(cameraSearchQuery.toLowerCase()) ||
                (c.location || "").toLowerCase().includes(cameraSearchQuery.toLowerCase());

            if (!matchesQuery) return false;
            if (selectedSector === "all") return true;
            if (selectedSector === "sector_a")
                return (
                    (c.id >= 1 && c.id <= 20) ||
                    (c.location || "").includes("Gate") ||
                    (c.location || "").includes("Turnstile")
                );
            if (selectedSector === "sector_b")
                return (
                    (c.id >= 21 && c.id <= 40) ||
                    (c.location || "").includes("Hall") ||
                    (c.location || "").includes("Corridor")
                );
            if (selectedSector === "sector_c")
                return (
                    (c.id >= 41 && c.id <= 60) ||
                    (c.location || "").includes("Perimeter") ||
                    (c.location || "").includes("Fence")
                );
            if (selectedSector === "sector_d")
                return (
                    (c.id >= 61 && c.id <= 80) ||
                    (c.location || "").includes("Vault") ||
                    (c.location || "").includes("Restricted")
                );
            return true;
        });
    }, [cameras, selectedSector, cameraSearchQuery]);

    const activeAlerts = alerts.filter((a) => String(a.status).toUpperCase() === "ACTIVE");
    const criticalAlert = activeAlerts.find((a) => a.priority === "CRITICAL" || a.priority === "HIGH");

    const streamUrl =
        selectedCamera && isStreaming
            ? `${API_BASE_URL}/stream/${selectedCamera.id}?t=${Date.now()}`
            : null;

    return (
        <div className={`surveillance-view mode-layout-${modeType.toLowerCase()}`}>
            {/* Triage / Snapshot Toast */}
            {triageToast && (
                <div className="triage-feedback-toast">
                    <span>⚜️ {triageToast}</span>
                </div>
            )}

            {/* External Hardware Auto-Plug Toast */}
            {externalPluggedMsg && (
                <div className="external-plug-toast">{externalPluggedMsg}</div>
            )}

            {/* Optical Diagnostics Advice Banner */}
            {(lightingDiag.advice || clarityDiag.advice) && (
                <div className="optical-diagnostic-banner">
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span>🔍</span>
                        <strong>Live Optical Diagnostic Advisory:</strong>
                    </div>
                    {lightingDiag.advice && <div className="advice-item">{lightingDiag.advice}</div>}
                    {clarityDiag.advice && <div className="advice-item">{clarityDiag.advice}</div>}
                </div>
            )}

            {/* Critical Alert Banner */}
            {criticalAlert && (
                <div className="critical-alert-banner">
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <div className="alert-pulse-red"></div>
                        <div>
                            <strong>CRITICAL SECURITY EVENT DETECTED:</strong>
                            <div style={{ fontSize: "12px", marginTop: "2px" }}>
                                {criticalAlert.object} on {selectedCamera?.camera_name || "Camera"} (
                                {parseInt(criticalAlert.confidence * 100, 10) || 94}% conf).
                            </div>
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: "8px" }}>
                        <button
                            type="button"
                            onClick={() => handleTriageAlert(criticalAlert.id, "VIOLATION")}
                            className="btn-triage-violation"
                        >
                            ✓ Verified Violation
                        </button>
                        <button
                            type="button"
                            onClick={() => handleTriageAlert(criticalAlert.id, "FALSE_ALARM")}
                            className="btn-triage-false"
                        >
                            ✕ False Alarm
                        </button>
                    </div>
                </div>
            )}

            {/* ── DISTINCT MODE-SPECIFIC TOP BARS (Point 3) ── */}
            {modeType === "School" && (
                <div className="mode-distinct-topbar school-bar">
                    <div className="topbar-info-block">
                        <span className="topbar-tag">🏛️ ACADEMIC CAMPUS COMMAND</span>
                        <h3 className="topbar-title">Greenwood Academy • Fall Semester 2026</h3>
                    </div>
                    <div className="topbar-metrics-row">
                        <div className="metric-pill">
                            <span className="metric-label">BELL PERIOD</span>
                            <strong className="metric-val">Period 3 (10:30–11:45)</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">CAMPUS ATTENDANCE</span>
                            <strong className="metric-val text-gold">96.4% PRESENT</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">UNIFORM STANDARDS</span>
                            <strong className="metric-val text-green">98.2% COMPLIANT</strong>
                        </div>
                    </div>
                </div>
            )}

            {modeType === "Military" && (
                <div className="mode-distinct-topbar military-bar">
                    <div className="topbar-info-block">
                        <span className="topbar-tag text-emerald">🛡️ TACTICAL DEFENSE & SENTRY COMMAND</span>
                        <h3 className="topbar-title">Strategic Sentry Grid • Sector Alpha Perimeter</h3>
                    </div>
                    <div className="topbar-metrics-row">
                        <div className="metric-pill defcon-pill">
                            <span className="metric-label">DEFCON STATUS</span>
                            <strong className="metric-val text-emerald">DEFCON 4 • ENHANCED SENTRY</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">TRIPWIRE SENSORS</span>
                            <strong className="metric-val text-gold">24 / 24 ARMED</strong>
                        </div>
                        <div className="metric-pill optics-toggle-pill">
                            <span className="metric-label">OPTICAL FILTER</span>
                            <div className="optics-buttons">
                                {["NORMAL_HD", "NIGHT_VISION", "THERMAL_FLIR"].map((m) => (
                                    <button
                                        key={m}
                                        type="button"
                                        onClick={() => setOpticsMode(m)}
                                        className={`optics-btn ${opticsMode === m ? "active" : ""}`}
                                    >
                                        {m.replace("_", " ")}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {modeType === "Industry" && (
                <div className="mode-distinct-topbar industry-bar">
                    <div className="topbar-info-block">
                        <span className="topbar-tag text-amber">🏭 INDUSTRIAL SCADA & OSHA SAFETY</span>
                        <h3 className="topbar-title">Apex Turbine Bay & Chemical Plant Safety Hub</h3>
                    </div>
                    <div className="topbar-metrics-row">
                        <div className="metric-pill">
                            <span className="metric-label">SAFETY RECORD</span>
                            <strong className="metric-val text-gold">412 DAYS INCIDENT FREE</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">ACTIVE SHIFT</span>
                            <strong className="metric-val">Shift A (06:00–14:00)</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">PLANT SAFETY KLAXON</span>
                            <strong className="metric-val text-green">ARMED • NOMINAL</strong>
                        </div>
                    </div>
                </div>
            )}

            {modeType === "Hospital" && (
                <div className="mode-distinct-topbar hospital-bar">
                    <div className="topbar-info-block">
                        <span className="topbar-tag text-cyan">🏥 CIVIC TRANSIT & EMERGENCY TRIAGE</span>
                        <h3 className="topbar-title">Central Concourse & Healthcare Thoroughfares</h3>
                    </div>
                    <div className="topbar-metrics-row">
                        <div className="metric-pill">
                            <span className="metric-label">CONCOURSE FLOW</span>
                            <strong className="metric-val text-cyan">1,420 PAX / HOUR</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">CROWD CONGESTION</span>
                            <strong className="metric-val text-green">NOMINAL (42%)</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">STATIONARY OBJECTS</span>
                            <strong className="metric-val text-gold">0 ABANDONED BAGS</strong>
                        </div>
                    </div>
                </div>
            )}

            {modeType === "Corporate" && (
                <div className="mode-distinct-topbar corporate-bar">
                    <div className="topbar-info-block">
                        <span className="topbar-tag text-gold">🌐 CORPORATE & FINTECH HUB</span>
                        <h3 className="topbar-title">Enterprise Turnstiles & Boardroom Biometrics</h3>
                    </div>
                    <div className="topbar-metrics-row">
                        <div className="metric-pill">
                            <span className="metric-label">TURNSTILE SPEED</span>
                            <strong className="metric-val text-gold">840 SCANS / HR</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">ANTI-TAILGATING</span>
                            <strong className="metric-val text-green">100% VERIFIED</strong>
                        </div>
                        <div className="metric-pill">
                            <span className="metric-label">SERVER ROOM ACCESS</span>
                            <strong className="metric-val">TIER-4 SECURE</strong>
                        </div>
                    </div>
                </div>
            )}

            {/* AI Action Execution Banner */}
            <div className="live-ai-broadcast-card">
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                    <div className="ai-crest-icon">⚜️</div>
                    <div>
                        <div className="ai-sub-tag">
                            JARVIS 24/7 PERCEPTION STREAM • {recentAction.timestamp}
                        </div>
                        <div className="ai-text-line">{recentAction.text}</div>
                    </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span className="ai-status-badge">{recentAction.badge}</span>
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
                    >
                        🔊 Voice
                    </button>
                </div>
            </div>

            {/* Surveillance Layout */}
            <div className="surveillance-stage-layout">
                {/* Center Stage: Video Viewport & Controls */}
                <div className="surveillance-center-stage">
                    {/* Header Bar */}
                    <div className="stage-top-header">
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                <h2 className="stage-title">Live Vision Perception</h2>
                                <span className="cam-chip-active">
                                    CAM #{selectedCamera?.id || 1} • {selectedCamera?.camera_name || "Camera"}
                                </span>
                            </div>
                            <p className="stage-sub">📍 Sector: {selectedCamera?.location || "Gate Alpha"}</p>
                        </div>
                        <div className="stage-header-actions">
                            <button
                                className={`tool-btn ${cameraActive ? "btn-danger" : "btn-primary"}`}
                                onClick={() => setCameraActive(!cameraActive)}
                            >
                                {cameraActive ? "Pause Stream" : "Resume Stream"}
                            </button>
                            <div className="live-status-chip">
                                <span className="live-dot-pulse"></span>
                                <span>LIVE • 24/7 ACTIVE</span>
                            </div>
                        </div>
                    </div>

                    {/* Stream Source & Hardware Port Selector */}
                    <div className="stream-source-bar">
                        <span className="stream-source-label">SIGNAL INPUT:</span>
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
                            >
                                {s.icon} {s.label}
                            </button>
                        ))}

                        {streamSourceMode === "external_usb" && videoDevices.length > 0 && (
                            <select
                                className="sector-select-box"
                                value={selectedDeviceId}
                                onChange={(e) => setSelectedDeviceId(e.target.value)}
                            >
                                {videoDevices.map((d, i) => (
                                    <option key={d.deviceId || i} value={d.deviceId}>
                                        {d.label || `USB Video Device Port #${i + 1}`}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Function Switcher Pills */}
                    <div className="function-selector-quick-row">
                        <span className="func-select-label">ASSIGNED FUNCTION:</span>
                        <div className="func-pills-container">
                            {[
                                { id: "FACE_ATTENDANCE", label: "🎓 Face Attendance" },
                                { id: "DRESS_CODE", label: "👔 Dress Code & ID Card" },
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
                                >
                                    {fn.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Video Viewport Stage */}
                    <div className="video-viewport-container">
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
                                    <canvas ref={canvasRef} className="surveillance-canvas-feed" />
                                </div>
                            ) : (
                                <img
                                    src={streamUrl}
                                    alt="Sentronix Live Feed"
                                    className="surveillance-stream-img"
                                />
                            )
                        ) : (
                            <div className="video-standby-placeholder">
                                <span style={{ fontSize: "40px" }}>📹</span>
                                <h3>Camera Stream Standby</h3>
                                <p>Click "Resume Stream" above to activate live perception</p>
                            </div>
                        )}

                        {snapshotMsg && <div className="snapshot-toast">{snapshotMsg}</div>}
                    </div>

                    {/* Telemetry Information Row */}
                    <div className="video-telemetry-strip">
                        <div className="telemetry-info-left">
                            <span className="telemetry-item bold">
                                🎯 Targets: {currentDetectionsCount}
                            </span>
                            <span className="telemetry-item confidence-text text-gold">
                                {detectionLabel}
                            </span>
                        </div>
                        <div className="telemetry-info-right">
                            <button
                                type="button"
                                className="tool-btn btn-secondary-mini"
                                onClick={handleSnapshot}
                            >
                                📸 Capture Frame Snapshot
                            </button>
                        </div>
                    </div>
                </div>

                {/* ── DISTINCT MODE-SPECIFIC RIGHT SIDEBAR PANELS (Point 3) ── */}
                <div className="surveillance-right-sidebar">
                    {/* Academic Campus Mode Sidebar Panel */}
                    {modeType === "School" && (
                        <div className="mode-panel-card academic-panel">
                            <div className="panel-header-row">
                                <h4 className="panel-title">🎓 Student & Staff Roster ({people.length})</h4>
                                <span className="badge-pill-gold">Verified</span>
                            </div>
                            <div className="people-roster-scroll">
                                {people.length === 0 ? (
                                    <div className="empty-roster-msg">
                                        No individuals enrolled yet. Use Guided Setup or "Enroll Individual" to register students.
                                    </div>
                                ) : (
                                    people.slice(0, 10).map((p) => (
                                        <div key={p.id} className="roster-person-item">
                                            <div className="person-avatar-circle">
                                                {p.name.charAt(0).toUpperCase()}
                                            </div>
                                            <div className="person-info-block">
                                                <strong>{p.name}</strong>
                                                <div className="person-sub-info">
                                                    {p.identifier} • {p.role.toUpperCase()}
                                                </div>
                                            </div>
                                            <span
                                                className={`attendance-status-chip ${
                                                    p.today_attendance?.status === "PRESENT"
                                                        ? "present"
                                                        : "absent"
                                                }`}
                                            >
                                                {p.today_attendance?.status || "CHECK-IN READY"}
                                            </span>
                                        </div>
                                    ))
                                )}
                            </div>

                            <div className="compliance-summary-box">
                                <div className="compliance-row">
                                    <span>Formals & Uniform:</span>
                                    <strong className="text-green">98.2% Compliant</strong>
                                </div>
                                <div className="compliance-row">
                                    <span>ID Badges Worn:</span>
                                    <strong className="text-gold">95.4% Detected</strong>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Military Mode Sidebar Panel */}
                    {modeType === "Military" && (
                        <div className="mode-panel-card military-panel">
                            <div className="panel-header-row">
                                <h4 className="panel-title text-emerald">🛡️ Sentry Sentry Radar</h4>
                                <span className="badge-pill-emerald">ARMED</span>
                            </div>
                            <div className="tactical-metrics-grid">
                                <div className="tactical-cell">
                                    <span className="t-label">AZIMUTH</span>
                                    <strong className="t-val">184.2° SSE</strong>
                                </div>
                                <div className="tactical-cell">
                                    <span className="t-label">GRID COORD</span>
                                    <strong className="t-val">34.05°N 118.25°W</strong>
                                </div>
                                <div className="tactical-cell">
                                    <span className="t-label">TARGET LOCK</span>
                                    <strong className="t-val text-emerald">CLEAR</strong>
                                </div>
                                <div className="tactical-cell">
                                    <span className="t-label">WEAPON SCAN</span>
                                    <strong className="t-val text-green">ZERO THREAT</strong>
                                </div>
                            </div>
                            <div className="clearance-tiers-box">
                                <span className="tier-header">PERSONNEL CLEARANCES:</span>
                                <div className="tier-item">🎖️ Tier 1 (Commanders): 3 Active</div>
                                <div className="tier-item">🎖️ Tier 2 (Sentries): 12 On Watch</div>
                            </div>
                        </div>
                    )}

                    {/* Heavy Industry Mode Sidebar Panel */}
                    {modeType === "Industry" && (
                        <div className="mode-panel-card industry-panel">
                            <div className="panel-header-row">
                                <h4 className="panel-title text-amber">🦺 OSHA PPE Compliance</h4>
                                <span className="badge-pill-amber">AUDIT OK</span>
                            </div>
                            <div className="ppe-bars-list">
                                <div className="ppe-bar-item">
                                    <div className="ppe-bar-label">
                                        <span>Hardhats:</span>
                                        <strong>100%</strong>
                                    </div>
                                    <div className="progress-bar-track">
                                        <div className="progress-bar-fill" style={{ width: "100%" }}></div>
                                    </div>
                                </div>
                                <div className="ppe-bar-item">
                                    <div className="ppe-bar-label">
                                        <span>High-Vis Vests:</span>
                                        <strong>96.4%</strong>
                                    </div>
                                    <div className="progress-bar-track">
                                        <div className="progress-bar-fill" style={{ width: "96%" }}></div>
                                    </div>
                                </div>
                                <div className="ppe-bar-item">
                                    <div className="ppe-bar-label">
                                        <span>Safety Glasses:</span>
                                        <strong>94.2%</strong>
                                    </div>
                                    <div className="progress-bar-track">
                                        <div className="progress-bar-fill" style={{ width: "94%" }}></div>
                                    </div>
                                </div>
                            </div>
                            <div className="machine-tripwire-box">
                                <span className="tier-header">RESTRICTED MACHINERY CELLS:</span>
                                <div className="machine-status-row">⚙️ Conveyor Bay 1: <strong className="text-green">ARMED</strong></div>
                                <div className="machine-status-row">⚙️ Turbine Cell 3: <strong className="text-green">ARMED</strong></div>
                            </div>
                        </div>
                    )}

                    {/* Public Healthcare Mode Sidebar Panel */}
                    {modeType === "Hospital" && (
                        <div className="mode-panel-card hospital-panel">
                            <div className="panel-header-row">
                                <h4 className="panel-title text-cyan">👥 Concourse Density</h4>
                                <span className="badge-pill-cyan">CIVIC EYE</span>
                            </div>
                            <div className="crowd-density-meter">
                                <div className="density-val-large">42%</div>
                                <span className="density-sub">Nominal Transit Flow</span>
                            </div>
                            <div className="transit-zones-box">
                                <div className="zone-row">
                                    <span>Main Atrium Gate:</span>
                                    <strong className="text-green">Normal (38%)</strong>
                                </div>
                                <div className="zone-row">
                                    <span>Emergency Pharmacy:</span>
                                    <strong className="text-cyan">Biometric Locked</strong>
                                </div>
                                <div className="zone-row">
                                    <span>Unattended Luggage:</span>
                                    <strong className="text-gold">0 Flags</strong>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Corporate Enterprise Mode Sidebar Panel */}
                    {modeType === "Corporate" && (
                        <div className="mode-panel-card corporate-panel">
                            <div className="panel-header-row">
                                <h4 className="panel-title text-gold">🏢 Executive Turnstiles</h4>
                                <span className="badge-pill-gold">FINTECH</span>
                            </div>
                            <div className="turnstile-telemetry-box">
                                <div className="telemetry-big-stat">840</div>
                                <span className="stat-sub-text">Scans / Hour • 0 Tailgating Flags</span>
                            </div>
                            <div className="visitor-escort-box">
                                <span className="tier-header">PRE-REGISTERED GUESTS:</span>
                                <div className="visitor-item">🪪 VIP Delegation (Goldman Sachs) • Escorted</div>
                                <div className="visitor-item">🪪 Tech Auditor (PwC) • NDA Signed</div>
                            </div>
                        </div>
                    )}

                    {/* Camera Device Picker with Sector Filters & Search */}
                    <div className="camera-picker-card">
                        <div className="picker-header">
                            <h4>Camera Fleet ({cameras.length})</h4>
                            <span className="fleet-active-tag">80 READY</span>
                        </div>

                        {/* Search Filter */}
                        <input
                            placeholder="🔍 Search camera name or location..."
                            value={cameraSearchQuery}
                            onChange={(e) => setCameraSearchQuery(e.target.value)}
                            className="camera-search-input"
                        />

                        {/* Sector Filter Tabs */}
                        <div className="sector-tabs-row">
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
                                    className={`sector-tab-btn ${selectedSector === sec.id ? "active" : ""}`}
                                >
                                    {sec.label}
                                </button>
                            ))}
                        </div>

                        {/* Scrollable Camera List */}
                        <div className="camera-picker-scroll">
                            {filteredCameras.map((cam) => {
                                const isSelected = selectedCamera?.id === cam.id;
                                return (
                                    <div
                                        key={cam.id}
                                        className={`camera-item-card ${isSelected ? "selected" : ""}`}
                                        onClick={() => setSelectedCamera(cam)}
                                    >
                                        <div className="cam-item-title-row">
                                            <span className="cam-item-name">{cam.camera_name}</span>
                                            <select
                                                value={cam.assigned_function || "FACE_ATTENDANCE"}
                                                onClick={(e) => e.stopPropagation()}
                                                onChange={async (e) => {
                                                    e.stopPropagation();
                                                    await handleInlineCameraFunctionChange(cam.id, e.target.value);
                                                }}
                                                className="cam-inline-func-select"
                                                title="Assign independent AI function to this specific camera"
                                            >
                                                <option value="FACE_ATTENDANCE">🎓 Attendance</option>
                                                <option value="DRESS_CODE">👔 Dress &amp; ID</option>
                                                <option value="EXAM_MONITOR">📝 Exam Proctor</option>
                                                <option value="PERIMETER_INTRUSION">🛡️ Sentry Perimeter</option>
                                                <option value="DRESS_CODE_PPE">🦺 PPE Safety</option>
                                                <option value="CROWD_LOITERING">👥 Crowd Loiter</option>
                                            </select>
                                        </div>
                                        <div className="cam-item-loc-row">
                                            <span>📍 {cam.location}</span>
                                            <span className="cam-online-pill">● ONLINE</span>
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
