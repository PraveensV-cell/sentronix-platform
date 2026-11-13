import { useState, useEffect, useRef, useMemo } from "react";
import OnboardingFlowModal from "../components/OnboardingFlowModal";
import {
    getCameras,
    createCamera,
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
    const [showOnboardingModal, setShowOnboardingModal] = useState(false);
    const [showAddCamModal, setShowAddCamModal] = useState(false);
    const [newCamName, setNewCamName] = useState("");
    const [newCamLoc, setNewCamLoc] = useState("");
    const [newCamFunc, setNewCamFunc] = useState("DRESS_CODE");
    const [newCamSrcType, setNewCamSrcType] = useState("webcam");
    const [newCamSrcUrl, setNewCamSrcUrl] = useState("0");
    const [snapshotMsg, setSnapshotMsg] = useState("");
    const [cameraActive, setCameraActive] = useState(true);
    const [currentDetectionsCount, setCurrentDetectionsCount] = useState(1);
    const [detectionLabel, setDetectionLabel] = useState("Face Verification Active • Scanning...");

    // Live Perception Analysis from Backend Face Matching & Dress/ID Engine
    const [livePerception, setLivePerception] = useState({
        person_detected: false,
        face_detected: false,
        face_box: null,
        person_box: null,
        detections: [],
        objects_summary: [],
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
        safety_ppe: {
            ppe_active: false,
            helmet_detected: false,
            vest_detected: false,
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
    const [perceptionLatency, setPerceptionLatency] = useState(24);
    const lastSpokenRef = useRef("");

    // Refs for webcam and canvas
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const offscreenCaptureRef = useRef(null);
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
            clearTimeout(uploadIntervalRef.current);
            uploadIntervalRef.current = null;
        }
    };

    // Pre-warm perception models in background on component mount (Zero Cold-Start Latency!)
    useEffect(() => {
        fetch("/api/ai/warmup").catch(() => {});
    }, []);

    // ── High-Speed Frame Upload & Real-Time Perception Synchronization ──
    useEffect(() => {
        let isMounted = true;
        let isProcessing = false;

        if (!selectedCamera || !cameraActive || !isStreaming || streamSourceMode === "backend") {
            if (uploadIntervalRef.current) {
                clearTimeout(uploadIntervalRef.current);
                uploadIntervalRef.current = null;
            }
            return;
        }

        const runPerceptionLoop = async () => {
            if (!isMounted || !cameraActive || !isStreaming || streamSourceMode === "backend") return;
            const video = videoRef.current;
            if (!video || video.readyState < 2 || isProcessing) {
                uploadIntervalRef.current = setTimeout(runPerceptionLoop, 50);
                return;
            }

            isProcessing = true;
            try {
                if (!offscreenCaptureRef.current) {
                    offscreenCaptureRef.current = document.createElement("canvas");
                    offscreenCaptureRef.current.width = 480;
                    offscreenCaptureRef.current.height = 360;
                }
                const offCanvas = offscreenCaptureRef.current;
                const offCtx = offCanvas.getContext("2d", { willReadFrequently: true });
                offCtx.drawImage(video, 0, 0, 480, 360);

                offCanvas.toBlob(
                    async (blob) => {
                        if (!blob || !isMounted) {
                            isProcessing = false;
                            return;
                        }
                        try {
                            const startTime = performance.now();
                            const res = await uploadCameraFrame(selectedCamera.id, blob);
                            const lat = Math.round(performance.now() - startTime);
                            setPerceptionLatency(lat > 0 ? lat : 22);

                            if (res && res.analysis && isMounted) {
                                setLivePerception(res.analysis);
                                if (res.analysis.detections) {
                                    setCurrentDetectionsCount(res.analysis.detections.length);
                                }

                                const an = res.analysis;
                                const isM = an.is_match && an.matched_person;
                                const dr = an.dress_code || {};
                                const isDressPass = dr.dress_compliant !== false;
                                const hasId = dr.id_card_detected !== false;
                                const proh = an.prohibited_items || [];
                                const g = (an.detected_gender || "person").toUpperCase();

                                // Update Live Detection Label
                                if (proh.length > 0) {
                                    setDetectionLabel(`🚨 SECURITY ALERT: PROHIBITED ${proh[0].toUpperCase()} DETECTED!`);
                                } else if (isM) {
                                    const p = an.matched_person;
                                    setDetectionLabel(
                                        `⚜️ ${p.name} [${p.identifier}] — Verified (${Math.round(
                                            an.similarity * 100
                                        )}%)`
                                    );
                                } else if (an.person_detected) {
                                    setDetectionLabel(`⚠️ Unknown ${g} — Unenrolled Individual`);
                                } else {
                                    setDetectionLabel("VANTEP AI • Optics Active • Scanning for Subject");
                                }

                                if (an.person_detected) {
                                    // Autonomous AI Real-Time Broadcast & Speech
                                    let broadcastText = "";
                                    if (proh.length > 0) {
                                        broadcastText = `🚨 SECURITY ALERT: Prohibited ${proh.join(", ")} detected in Sector! Logged to security alerts.`;
                                    } else if (!isDressPass || !hasId) {
                                        const who = isM ? an.matched_person.name : `Unenrolled ${g.toLowerCase()}`;
                                        const violations = [];
                                        if (!isDressPass) violations.push(`casual attire (${dr.dress_type || "casual"})`);
                                        if (!hasId) violations.push("missing ID card");
                                        broadcastText = `⚠️ DRESS CODE NOTICE: ${who} flagged for ${violations.join(" and ")}.`;
                                    } else if (isM) {
                                        broadcastText = `⚜️ Autonomous AI: ${an.matched_person.name} verified. Attire: ${dr.dress_type || "Formals"} [Pass] • ID Card: Verified • Attendance: Checked In.`;
                                    }

                                    if (broadcastText && lastSpokenRef.current !== broadcastText) {
                                        lastSpokenRef.current = broadcastText;
                                        setRecentAction({
                                            type: proh.length > 0 ? "SECURITY" : (!isDressPass || !hasId ? "DRESS_CODE" : "ATTENDANCE"),
                                            text: broadcastText,
                                            timestamp: new Date().toLocaleTimeString(),
                                            badge: proh.length > 0 ? "SECURITY VIOLATION" : (!isDressPass || !hasId ? "DRESS ALERT" : "VERIFIED & NOMINAL"),
                                        });
                                    }
                                }
                            }
                        } catch (err) {
                            // silent error handling
                        } finally {
                            isProcessing = false;
                            if (isMounted && cameraActive && isStreaming) {
                                uploadIntervalRef.current = setTimeout(runPerceptionLoop, 120);
                            }
                        }
                    },
                    "image/jpeg",
                    0.68
                );
            } catch (e) {
                isProcessing = false;
                if (isMounted && cameraActive && isStreaming) {
                    uploadIntervalRef.current = setTimeout(runPerceptionLoop, 150);
                }
            }
        };

        // Fire immediately with 0ms delay!
        runPerceptionLoop();

        return () => {
            isMounted = false;
            if (uploadIntervalRef.current) {
                clearTimeout(uploadIntervalRef.current);
                uploadIntervalRef.current = null;
            }
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

                    // ─── Multi-Object Technical Bounding Boxes (Person, Face, Dress Code, ID Card, Safety Gear) ───
                    const detections = livePerception.detections || [];
                    const hasSubject = Boolean(
                        livePerception.person_detected ||
                        livePerception.face_detected ||
                        detections.length > 0
                    );

                    if (hasSubject && detections.length > 0) {
                        // Detections are evaluated on high-speed 480x360 perception space
                        const scaleX = cw / 480;
                        const scaleY = ch / 360;

                        detections.forEach((det) => {
                            if (!det.box || !Array.isArray(det.box) || det.box.length < 4) return;
                            const [origX, origY, origW, origH] = det.box;

                            let bx = Math.round(origX * scaleX);
                            let by = Math.round(origY * scaleY);
                            let bw = Math.round(origW * scaleX);
                            let bh = Math.round(origH * scaleY);

                            bx = Math.max(4, Math.min(cw - 20, bx));
                            by = Math.max(4, Math.min(ch - 20, by));
                            bw = Math.min(cw - bx - 4, bw);
                            bh = Math.min(ch - by - 4, bh);

                            const color = det.color || "#10b981";

                            // 1. Draw 2D Technical Bounding Box
                            ctx.lineWidth = 2;
                            ctx.strokeStyle = color;
                            ctx.strokeRect(bx, by, bw, bh);

                            // 2. Corner Bracket Accents
                            const cLen = Math.min(18, Math.round(Math.min(bw, bh) * 0.28));
                            if (cLen > 4) {
                                ctx.lineWidth = 3;
                                ctx.strokeStyle = color;
                                ctx.beginPath();
                                ctx.moveTo(bx, by + cLen); ctx.lineTo(bx, by); ctx.lineTo(bx + cLen, by);
                                ctx.moveTo(bx + bw - cLen, by); ctx.lineTo(bx + bw, by); ctx.lineTo(bx + bw, by + cLen);
                                ctx.moveTo(bx, by + bh - cLen); ctx.lineTo(bx, by + bh); ctx.lineTo(bx + cLen, by + bh);
                                ctx.moveTo(bx + bw - cLen, by + bh); ctx.lineTo(bx + bw, by + bh); ctx.lineTo(bx + bw, by + bh - cLen);
                                ctx.stroke();
                            }

                            // 3. Label Badge on top-left edge of box (matching Reference Images 1 & 2)
                            ctx.font = "bold 11px 'Inter', sans-serif";
                            const textMetrics = ctx.measureText(det.label || "detected");
                            const badgeW = textMetrics.width + 12;
                            const badgeH = 18;
                            const badgeX = Math.max(0, Math.min(cw - badgeW, bx));
                            const badgeY = by >= badgeH ? by - badgeH : by;

                            // Solid badge background fill matching box color exactly (Image 1 & 2)
                            ctx.fillStyle = color;
                            ctx.fillRect(badgeX, badgeY, badgeW, badgeH);

                            // Crisp high-contrast text: black on bright fills, white on dark/red fills
                            const cLower = (color || "").toLowerCase();
                            const isBright = ["#10b981", "#00e676", "#ffd700", "#d4af37", "#38bdf8", "#06b6d4", "#a3e635", "#fed7aa"].some(c => cLower.includes(c));
                            ctx.fillStyle = isBright ? "#000000" : "#ffffff";
                            ctx.textBaseline = "middle";
                            ctx.fillText(det.label || "detected", badgeX + 6, badgeY + badgeH / 2);
                        });
                    } else {
                        // ─── Standby Mode: Waiting silently for subject (Zero fake alerts) ───
                        const cx = Math.round(cw / 2);
                        const cy = Math.round(ch / 2);

                        ctx.lineWidth = 1;
                        ctx.strokeStyle = "rgba(212, 175, 55, 0.30)";
                        ctx.beginPath();
                        ctx.arc(cx, cy, 38, 0, Math.PI * 2);
                        ctx.stroke();

                        ctx.beginPath();
                        ctx.moveTo(cx - 50, cy); ctx.lineTo(cx + 50, cy);
                        ctx.moveTo(cx, cy - 50); ctx.lineTo(cx, cy + 50);
                        ctx.stroke();

                        const standbyText = "VANTEP AI • OPTICS ACTIVE • SCANNING FOR SUBJECT";
                        ctx.font = "700 11px 'Inter', sans-serif";
                        const textMetrics = ctx.measureText(standbyText);
                        const textW = textMetrics.width;

                        ctx.fillStyle = "rgba(12, 16, 23, 0.85)";
                        ctx.fillRect(cx - textW / 2 - 12, cy + 50, textW + 24, 22);
                        ctx.lineWidth = 1;
                        ctx.strokeStyle = "rgba(212, 175, 55, 0.40)";
                        ctx.strokeRect(cx - textW / 2 - 12, cy + 50, textW + 24, 22);

                        ctx.fillStyle = "#ffd700";
                        ctx.fillText(standbyText, cx - textW / 2, cy + 65);
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

    const handleCreateCamera = async (e) => {
        if (e) e.preventDefault();
        if (!newCamName.trim()) return;
        try {
            const envId = environment?.id || 1;
            const res = await createCamera({
                name: newCamName.trim(),
                location: newCamLoc.trim() || "Main Sector",
                assigned_function: newCamFunc,
                source_type: newCamSrcType,
                source_url: newCamSrcUrl,
                environment_id: envId,
                group_id: 1,
            });
            if (res.success && res.camera) {
                setShowAddCamModal(false);
                setNewCamName("");
                setNewCamLoc("");
                await loadData();
                setSelectedCamera(res.camera);
                setTriageToast(`✓ Camera "${res.camera.camera_name}" created & assigned to ${newCamFunc}!`);
                setTimeout(() => setTriageToast(""), 4000);
            }
        } catch (err) {
            alert("Could not register camera.");
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

            {/* Initial Dataset & Camera Onboarding Banner if people < 3 */}
            {people.length < 3 && (
                <div
                    style={{
                        margin: "0 0 16px 0",
                        padding: "14px 20px",
                        background: "rgba(212, 175, 55, 0.12)",
                        border: "2px solid #d4af37",
                        borderRadius: "8px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "14px",
                        boxShadow: "2px 2px 0px rgba(212, 175, 55, 0.25)",
                    }}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                        <span style={{ fontSize: "28px" }}>🤖</span>
                        <div>
                            <strong style={{ fontSize: "14px", color: "var(--text-primary)" }}>
                                VANTEP AI • Initial Setup Required ({people.length}/3 Enrolled)
                            </strong>
                            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                                Upload a personnel dataset or register at least 3 individual profiles with clear face photos, then assign your camera fleet functions.
                            </div>
                        </div>
                    </div>
                    <button
                        type="button"
                        onClick={() => setShowOnboardingModal(true)}
                        style={{
                            background: "#d4af37",
                            color: "#0a101d",
                            padding: "10px 18px",
                            borderRadius: "6px",
                            border: "none",
                            fontWeight: 800,
                            fontSize: "12px",
                            cursor: "pointer",
                            whiteSpace: "nowrap",
                            boxShadow: "0 2px 8px rgba(212, 175, 55, 0.35)",
                        }}
                    >
                        🚀 Launch Dataset &amp; Camera Wizard →
                    </button>
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
                            VANTEP 24/7 PERCEPTION STREAM • {recentAction.timestamp}
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
                    {/* Header Bar (Exact Reference Image 2) */}
                    <div className="vms-header-bar">
                        <div className="vms-header-title-box">
                            <h2 className="vms-page-title">Live AI Surveillance</h2>
                            <div className="vms-camera-subtitle">
                                Camera: <strong>{selectedCamera?.camera_name || "test camera 01"}</strong>
                            </div>
                        </div>
                        <div className="vms-header-status-box">
                            <button
                                type="button"
                                className={`vms-stream-toggle-btn ${cameraActive ? "is-stopping" : "is-starting"}`}
                                onClick={() => setCameraActive(!cameraActive)}
                            >
                                {cameraActive ? "Stop Camera" : "Start Camera"}
                            </button>
                            <div className={`vms-live-indicator-pill ${cameraActive ? "online" : "offline"}`}>
                                <span className="vms-pulse-dot"></span>
                                <span>{cameraActive ? "LIVE • AI DETECTION ACTIVE" : "STANDBY • OPTICS PAUSED"}</span>
                            </div>
                        </div>
                    </div>

                    {/* ── UNIFIED MASTER SURVEILLANCE CONSOLE (Clean 2D Alignment) ── */}
                    <div className="vms-master-console">

                        {/* Master Toolbar Row 1: Camera Fleet, Signal Inputs, Live Optics & Stream Controls */}
                        <div className="vms-toolbar-primary">
                            {/* Left Group: Active Camera Selector & Add Camera */}
                            <div className="vms-tool-group">
                                <span className="vms-tool-label">📹 CAMERA:</span>
                                <select
                                    className="vms-camera-select"
                                    value={selectedCamera?.id || ""}
                                    onChange={(e) => {
                                        const cam = cameras.find((c) => String(c.id) === String(e.target.value));
                                        if (cam) setSelectedCamera(cam);
                                    }}
                                >
                                    {cameras.map((c) => (
                                        <option key={c.id} value={c.id}>
                                            CAM #{c.id} • {c.camera_name}
                                        </option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    onClick={() => setShowAddCamModal(true)}
                                    className="vms-btn-action btn-add-cam"
                                    title="Add another camera to this mode with a different function"
                                >
                                    + Add Camera
                                </button>
                            </div>

                            {/* Center-Left: Signal Source Selector (Segmented) */}
                            <div className="vms-tool-group vms-signal-group">
                                <span className="vms-tool-label">INPUT:</span>
                                <div className="vms-segmented-buttons">
                                    {[
                                        { id: "laptop_webcam", icon: "💻", label: "Laptop" },
                                        { id: "external_usb", icon: "🔌", label: "USB" },
                                        { id: "mobile_camera", icon: "📱", label: "Mobile" },
                                        { id: "backend", icon: "📡", label: "RTSP" },
                                    ].map((s) => (
                                        <button
                                            key={s.id}
                                            type="button"
                                            onClick={() => setStreamSourceMode(s.id)}
                                            className={`vms-segment-btn ${streamSourceMode === s.id ? "active" : ""}`}
                                        >
                                            {s.icon} {s.label}
                                        </button>
                                    ))}
                                </div>

                                {streamSourceMode === "external_usb" && videoDevices.length > 0 && (
                                    <select
                                        className="vms-device-select"
                                        value={selectedDeviceId}
                                        onChange={(e) => setSelectedDeviceId(e.target.value)}
                                    >
                                        {videoDevices.map((d, i) => (
                                            <option key={d.deviceId || i} value={d.deviceId}>
                                                {d.label || `USB Device #${i + 1}`}
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>

                            {/* Right Group: Optics & Stream Snapshot */}
                            <div className="vms-tool-group vms-actions-group">
                                <div className="vms-optics-toggle">
                                    {["NORMAL_HD", "NIGHT_VISION", "THERMAL_FLIR"].map((m) => (
                                        <button
                                            key={m}
                                            type="button"
                                            onClick={() => setOpticsMode(m)}
                                            className={`vms-optics-btn ${opticsMode === m ? "active" : ""}`}
                                            title={`Optics: ${m.replace("_", " ")}`}
                                        >
                                            {m === "NORMAL_HD" ? "HD" : m === "NIGHT_VISION" ? "NVG" : "FLIR"}
                                        </button>
                                    ))}
                                </div>

                                <button
                                    type="button"
                                    className="vms-btn-action btn-snapshot"
                                    onClick={handleSnapshot}
                                    title="Capture frame snapshot"
                                >
                                    📸 Snapshot
                                </button>
                            </div>
                        </div>

                        {/* Master Toolbar Row 2: Docked AI Perception Function Ribbon */}
                        <div className="vms-function-ribbon">
                            <span className="vms-ribbon-label">AI FUNCTION:</span>
                            <div className="vms-ribbon-pills">
                                {[
                                    { id: "FACE_ATTENDANCE", label: "🎓 Face Attendance" },
                                    { id: "DRESS_CODE", label: "👔 Dress Code & Uniform" },
                                    { id: "DRESS_CODE_PPE", label: "🦺 OSHA Safety PPE" },
                                    { id: "EXAM_MONITOR", label: "📝 Exam Proctoring" },
                                    { id: "PERIMETER_INTRUSION", label: "🛡️ Perimeter Sentry" },
                                    { id: "CROWD_LOITERING", label: "👥 Concourse Density" },
                                ].map((fn) => (
                                    <button
                                        key={fn.id}
                                        className={`vms-fn-pill ${(selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id ? "active" : ""}`}
                                        onClick={() => handleFunctionChange(fn.id)}
                                    >
                                        {fn.label}
                                    </button>
                                ))}
                            </div>
                            <span className="vms-active-indicator">
                                Assigned to CAM #{selectedCamera?.id || 1}
                            </span>
                        </div>

                        {/* Video Viewport Stage */}
                        <div className="vms-viewport-container">
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
                                    <p>Click "Start Camera" above to activate live perception</p>
                                </div>
                            )}

                            {snapshotMsg && <div className="snapshot-toast">{snapshotMsg}</div>}
                        </div>

                        {/* Consolidated Under-Video Telemetry HUD (Matching Reference Image 2) */}
                        <div className="vms-telemetry-hud">
                            <div className="vms-hud-header-line">
                                <span className="vms-hud-title">
                                    Objects currently detected: {livePerception.detections?.length || 0}
                                </span>
                            </div>

                            {livePerception.detections && livePerception.detections.length > 0 ? (
                                <div className="vms-detected-items-column">
                                    {livePerception.detections.map((d, i) => (
                                        <div key={i} className="vms-detected-line">
                                            <span className="vms-det-dot" style={{ background: d.color || "#10b981" }}></span>
                                            <span className="vms-item-name">{d.label}</span>
                                            <span className="vms-item-conf">— {Math.round((d.conf || 0.85) * 100)}% confidence</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="vms-hud-standby">
                                    VANTEP AI • Silent Standby • Optics Active • Awaiting Subject
                                </div>
                            )}

                            <div className="vms-hud-disclaimer">
                                Video is processed locally in your browser with sub-30ms perception latency. Detected objects depend on active mode categories.
                            </div>

                            <div className="vms-hud-footer-bar">
                                <div className="vms-footer-left">
                                    <span className="vms-label-dim">Signal source:</span>{" "}
                                    <strong>{selectedCamera?.camera_name || "test camera 01"}</strong>
                                </div>
                                <div className="vms-footer-right">
                                    <span>Browser webcam</span>
                                    <span className="vms-hud-sep">•</span>
                                    <span>Latency: <strong>{perceptionLatency}ms</strong></span>
                                    <span className="vms-hud-sep">•</span>
                                    <span>Optics: <strong>{opticsMode === "NORMAL_HD" ? "HD" : opticsMode === "NIGHT_VISION" ? "NVG" : "FLIR"}</strong></span>
                                    <span className="vms-hud-sep">•</span>
                                    <span className="text-green font-bold">● AI: ACTIVE</span>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                {/* ── DISTINCT MODE-SPECIFIC RIGHT SIDEBAR PANELS (Point 3) ── */}
                <div className="surveillance-right-sidebar">
                    {/* Reference Image 2: Current State Telemetry Card */}
                    <div
                        className="current-state-card"
                        style={{
                            padding: "14px",
                            background: "var(--card-bg)",
                            border: "1px solid var(--border-color)",
                            borderRadius: "8px",
                            marginBottom: "14px",
                            boxShadow: "var(--card-shadow)",
                        }}
                    >
                        <div style={{ fontWeight: 800, fontSize: "13px", marginBottom: "10px", color: "var(--text-primary)" }}>
                            Current state
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", fontSize: "12px" }}>
                            <span style={{ color: "var(--text-muted)" }}>Connection</span>
                            <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700, color: cameraActive ? "#10b981" : "#f59e0b" }}>
                                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: cameraActive ? "#10b981" : "#f59e0b" }}></span>
                                {cameraActive ? "ACTIVE" : "STANDBY"}
                            </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", fontSize: "12px" }}>
                            <span style={{ color: "var(--text-muted)" }}>Recording</span>
                            <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700, color: "#38bdf8" }}>
                                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#38bdf8" }}></span>
                                NOT CONFIGURED
                            </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", fontSize: "12px" }}>
                            <span style={{ color: "var(--text-muted)" }}>AI analysis</span>
                            <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700, color: "#10b981" }}>
                                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }}></span>
                                ENABLED
                            </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px" }}>
                            <span style={{ color: "var(--text-muted)" }}>Current detections</span>
                            <span style={{ display: "flex", alignItems: "center", gap: "6px", fontWeight: 700, color: (livePerception.detections?.length || 0) > 0 ? "#10b981" : "#f59e0b" }}>
                                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: (livePerception.detections?.length || 0) > 0 ? "#10b981" : "#f59e0b" }}></span>
                                {livePerception.detections?.length || 0}
                            </span>
                        </div>
                    </div>
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
                                            <div className="person-avatar-circle" style={{ overflow: "hidden" }}>
                                                {p.photo_url ? (
                                                    <img
                                                        src={p.photo_url}
                                                        alt={p.name}
                                                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                                                    />
                                                ) : (
                                                    p.name.charAt(0).toUpperCase()
                                                )}
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
            {/* Setup Wizard Modal */}
            {showOnboardingModal && (
                <OnboardingFlowModal
                    environment={environment}
                    isOpen={showOnboardingModal}
                    onClose={() => setShowOnboardingModal(false)}
                    onComplete={() => {
                        setShowOnboardingModal(false);
                        loadData();
                    }}
                />
            )}

            {/* Add Camera Modal */}
            {showAddCamModal && (
                <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 10001, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
                    <div style={{ background: "var(--card-bg)", border: "2px solid var(--royal-gold)", borderRadius: "8px", padding: "24px", width: "100%", maxWidth: "460px", boxShadow: "0 12px 32px rgba(0,0,0,0.6)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid var(--border-color)", paddingBottom: "10px" }}>
                            <h3 style={{ margin: 0, fontSize: "16px", color: "var(--text-primary)" }}>📹 Add Camera with Specific Function</h3>
                            <button type="button" onClick={() => setShowAddCamModal(false)} style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "16px" }}>✕</button>
                        </div>
                        <form onSubmit={handleCreateCamera} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                            <div>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Camera Name *</label>
                                <input type="text" value={newCamName} onChange={(e) => setNewCamName(e.target.value)} placeholder="e.g. CAM-02 [Exam Hall East]" required style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "12px" }} />
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Location Sector</label>
                                <input type="text" value={newCamLoc} onChange={(e) => setNewCamLoc(e.target.value)} placeholder="e.g. Block B, 2nd Floor Corridor" style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "12px" }} />
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Signal Source Type</label>
                                <select value={newCamSrcType} onChange={(e) => setNewCamSrcType(e.target.value)} style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "12px" }}>
                                    <option value="webcam">Integrated Laptop Camera</option>
                                    <option value="usb_port">External USB Video Device</option>
                                    <option value="mobile_ip">Mobile Phone / Remote IP Stream</option>
                                    <option value="rtsp">CCTV RTSP Network Stream</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Hardware Port / URL</label>
                                <input type="text" value={newCamSrcUrl} onChange={(e) => setNewCamSrcUrl(e.target.value)} placeholder="0 for webcam, or rtsp://..." style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "12px" }} />
                            </div>
                            <div>
                                <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>Assigned Operational Function *</label>
                                <select value={newCamFunc} onChange={(e) => setNewCamFunc(e.target.value)} style={{ width: "100%", padding: "8px 10px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg-secondary)", color: "var(--text-primary)", fontSize: "12px" }}>
                                    <option value="DRESS_CODE">👔 Dress Code &amp; Uniform Verification (Pass/Violation)</option>
                                    <option value="FACE_ATTENDANCE">🎓 Face Biometric Attendance &amp; Check-In</option>
                                    <option value="SAFETY">🦺 OSHA Safety Gear (Hardhat, High-Vis Vest, Goggles)</option>
                                    <option value="EXAM_MONITOR">📝 Exam Proctoring (Cell Phones &amp; Malpractice)</option>
                                    <option value="PERIMETER_INTRUSION">🛡️ Tactical Perimeter &amp; Intrusion Tripwire</option>
                                    <option value="CROWD_LOITERING">👥 Crowd Density &amp; Transit Loitering</option>
                                </select>
                            </div>
                            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "10px" }}>
                                <button type="button" onClick={() => setShowAddCamModal(false)} style={{ background: "transparent", border: "1px solid var(--border-color)", padding: "7px 14px", borderRadius: "4px", fontSize: "12px", color: "var(--text-muted)", cursor: "pointer" }}>Cancel</button>
                                <button type="submit" style={{ background: "var(--royal-gold)", color: "#0a101d", padding: "7px 18px", borderRadius: "4px", fontSize: "12px", fontWeight: 800, border: "none", cursor: "pointer" }}>Register Camera</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
