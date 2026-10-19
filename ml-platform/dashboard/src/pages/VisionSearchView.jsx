import { useState, useEffect } from "react";
import { searchVisionEvents, getCameras, getExportCsvUrl } from "../api/api";

export default function VisionSearchView() {
    const [query, setQuery] = useState("");
    const [selectedCamera, setSelectedCamera] = useState("all");
    const [selectedType, setSelectedType] = useState("all");
    const [sortBy, setSortBy] = useState("newest");
    const [layout, setLayout] = useState("grid"); // 'grid' | 'list'
    const [cameras, setCameras] = useState([]);
    const [results, setResults] = useState([]);
    const [totalFound, setTotalFound] = useState(0);
    const [loading, setLoading] = useState(false);
    const [activeInspector, setActiveInspector] = useState(null);

    const loadCameras = async () => {
        try {
            const res = await getCameras();
            setCameras(res.cameras || []);
        } catch (e) {
            console.error("Failed to load cameras", e);
        }
    };

    const executeSearch = async (searchTerm = query) => {
        setLoading(true);
        try {
            const data = await searchVisionEvents({
                q: searchTerm || undefined,
                camera_id: selectedCamera,
                object_type: selectedType,
                sort_by: sortBy,
            });
            setResults(data.results || []);
            setTotalFound(data.total_found || 0);
        } catch (e) {
            console.error("Search failed", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCameras();
        executeSearch("");
    }, [selectedCamera, selectedType, sortBy]);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        executeSearch(query);
    };

    const handleClearFilters = () => {
        setQuery("");
        setSelectedCamera("all");
        setSelectedType("all");
        setSortBy("newest");
        executeSearch("");
    };

    const sampleQueries = [
        "A red car",
        "Person with backpack",
        "Unauthorized entry",
        "Student without uniform",
        "Fire or smoke detected",
    ];

    return (
        <div className="vision-search-container">
            {/* Header banner */}
            <div className="vision-search-header">
                <div className="header-badge-row">
                    <span className="vision-logo-pill">✨ VisionAI Semantic Search</span>
                    <span className="vision-sub-tag">Zero-Shot Object & Event Discovery</span>
                </div>
                <h2>Natural Language Surveillance Search</h2>
                <p>Search across video streams, detected events, and temporal incidents using descriptive visual queries.</p>
            </div>

            {/* Main Search Input Form */}
            <form className="vision-search-bar-form" onSubmit={handleSearchSubmit}>
                <div className="vision-input-wrapper">
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        placeholder="Search incidents, objects, or behaviors (e.g. 'A red car', 'Student in hallway', 'Backpack')..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="vision-main-input"
                    />
                    <button type="submit" className="btn-ai-search">
                        <span>✨ AI Search</span>
                    </button>
                </div>
            </form>

            {/* Quick Suggestion Pills */}
            <div className="suggestion-pills-row">
                <span className="suggestion-label">Suggested:</span>
                {sampleQueries.map((sq, idx) => (
                    <button
                        key={idx}
                        className="suggestion-pill"
                        onClick={() => {
                            setQuery(sq);
                            executeSearch(sq);
                        }}
                    >
                        {sq}
                    </button>
                ))}
            </div>

            {/* Filter & Controls Toolbar */}
            <div className="vision-controls-bar">
                <div className="controls-left">
                    {/* Camera Filter */}
                    <div className="filter-select-wrapper">
                        <label>Camera:</label>
                        <select
                            value={selectedCamera}
                            onChange={(e) => setSelectedCamera(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Cameras ({cameras.length})</option>
                            {cameras.map((c) => (
                                <option key={c.id} value={c.id}>
                                    {c.camera_name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Object Type Filter */}
                    <div className="filter-select-wrapper">
                        <label>Type:</label>
                        <select
                            value={selectedType}
                            onChange={(e) => setSelectedType(e.target.value)}
                            className="filter-select"
                        >
                            <option value="all">All Types</option>
                            <option value="person">Person</option>
                            <option value="car">Vehicle / Car</option>
                            <option value="backpack">Backpack / Bag</option>
                            <option value="cell phone">Phone</option>
                            <option value="fire">Fire / Smoke</option>
                            <option value="knife">Weapon / Threat</option>
                        </select>
                    </div>

                    {/* Sort Order */}
                    <div className="filter-select-wrapper">
                        <label>Sort By:</label>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="filter-select"
                        >
                            <option value="newest">Sort by: Newest</option>
                            <option value="confidence">Sort by: Confidence</option>
                        </select>
                    </div>

                    <button className="btn-clear-filters" onClick={handleClearFilters}>
                        Clear All
                    </button>
                </div>

                <div className="controls-right">
                    <span className="results-count-badge">
                        <strong>{totalFound}</strong> objects found
                    </span>

                    <div className="layout-toggle-group">
                        <button
                            className={`layout-btn ${layout === "grid" ? "active" : ""}`}
                            onClick={() => setLayout("grid")}
                            title="Grid Layout"
                        >
                            田
                        </button>
                        <button
                            className={`layout-btn ${layout === "list" ? "active" : ""}`}
                            onClick={() => setLayout("list")}
                            title="List Layout"
                        >
                            ☰
                        </button>
                    </div>
                </div>
            </div>

            {/* Results Grid / List */}
            {loading ? (
                <div className="vision-loading-state">
                    <div className="spinner"></div>
                    <p>Scanning video frames & database embeddings...</p>
                </div>
            ) : results.length === 0 ? (
                <div className="vision-empty-state">
                    <span className="empty-icon">📹</span>
                    <h3>No matching detections found</h3>
                    <p>Try modifying your search term or selecting "All Cameras" in the filter.</p>
                </div>
            ) : layout === "grid" ? (
                <div className="vision-results-grid">
                    {results.map((item) => (
                        <div
                            key={item.id}
                            className="vision-card"
                            onClick={() => setActiveInspector(item)}
                        >
                            <div className="card-media-wrapper">
                                <div className="card-mock-frame">
                                    <span className="cam-chip">{item.camera_name}</span>
                                    <span className="object-bbox-tag">
                                        {item.object.toUpperCase()} ({(item.confidence * 100).toFixed(0)}%)
                                    </span>
                                </div>
                            </div>
                            <div className="card-body">
                                <div className="card-title-row">
                                    <strong>{item.camera_name}</strong>
                                    <span className="cam-icon">📹</span>
                                </div>
                                <div className="card-meta-row">
                                    <span className="meta-time">{item.timestamp}</span>
                                    <span className="meta-loc">{item.location}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="vision-results-list">
                    <table className="soc-table">
                        <thead>
                            <tr>
                                <th># ID</th>
                                <th>CAMERA SOURCE</th>
                                <th>LOCATION</th>
                                <th>DETECTED OBJECT</th>
                                <th>CONFIDENCE</th>
                                <th>TIMESTAMP</th>
                                <th>ACTION</th>
                            </tr>
                        </thead>
                        <tbody>
                            {results.map((item) => (
                                <tr key={item.id}>
                                    <td>#{item.id}</td>
                                    <td><strong>{item.camera_name}</strong></td>
                                    <td>{item.location}</td>
                                    <td>
                                        <span className={`class-chip ${item.object.toLowerCase()}`}>
                                            {item.object.toUpperCase()}
                                        </span>
                                    </td>
                                    <td>{(item.confidence * 100).toFixed(1)}%</td>
                                    <td>{item.timestamp}</td>
                                    <td>
                                        <button
                                            className="btn-inspect-mini"
                                            onClick={() => setActiveInspector(item)}
                                        >
                                            View Evidence
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Modal Evidence Inspector */}
            {activeInspector && (
                <div className="modal-backdrop" onClick={() => setActiveInspector(null)}>
                    <div className="modal-content evidence-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3>Evidence Inspector: Incident #{activeInspector.id}</h3>
                                <p>{activeInspector.camera_name} • {activeInspector.location}</p>
                            </div>
                            <button className="modal-close-btn" onClick={() => setActiveInspector(null)}>✕</button>
                        </div>
                        <div className="evidence-modal-body">
                            <div className="evidence-frame-stage">
                                <div className="mock-live-box">
                                    <div className="crosshair-hud"></div>
                                    <span className="hud-target-label">
                                        TARGET: {activeInspector.object.toUpperCase()} [CONF: {(activeInspector.confidence * 100).toFixed(1)}%]
                                    </span>
                                </div>
                            </div>
                            <div className="evidence-details-pane">
                                <h4>Detection Telemetry</h4>
                                <div className="telemetry-row">
                                    <span>Object Classification:</span>
                                    <strong>{activeInspector.object.toUpperCase()}</strong>
                                </div>
                                <div className="telemetry-row">
                                    <span>Confidence Score:</span>
                                    <strong>{(activeInspector.confidence * 100).toFixed(2)}%</strong>
                                </div>
                                <div className="telemetry-row">
                                    <span>Time of Capture:</span>
                                    <strong>{activeInspector.timestamp}</strong>
                                </div>
                                <div className="telemetry-row">
                                    <span>Camera ID:</span>
                                    <strong>{activeInspector.camera_id}</strong>
                                </div>
                                <div className="telemetry-row">
                                    <span>Bounding Box:</span>
                                    <code>{activeInspector.bbox || "[x: 140, y: 80, w: 220, h: 310]"}</code>
                                </div>
                                <div className="telemetry-row">
                                    <span>Storage Archive:</span>
                                    <span className="status-badge-chip verified">ARCHIVED IN EVIDENCE DB</span>
                                </div>
                                <div className="modal-actions-bar">
                                    <a
                                        href={getExportCsvUrl("detections")}
                                        className="btn-primary"
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Export Incident CSV
                                    </a>
                                    <button
                                        className="btn-secondary"
                                        onClick={() => setActiveInspector(null)}
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
