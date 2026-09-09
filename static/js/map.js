/**
 * National Weather Big Data Analytics Platform (NWBDAP)
 * Geospatial Operational Map & Live Stream Controller
 */

let map;
let baseTileLayer = null;
let labelsTileLayer = null;
let markersLayer;
let heatmapLayer;
let isHeatmapActive = false;
let liveStationsLayer = null;
let isLiveStationsActive = false;
let userRadiusCircle = null;
let currentReports = [];
let currentClusters = [];

// 100% Watermark-Free Map Tile Imagery: High-Res Real Satellite Photography & Cartography (No API Key Required)
const MAP_STYLES = {
    satellite: {
        name: "Satellite Photo (Earth Imagery)",
        base: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        labels: "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, Earthstar Geographics'
    },
    topo: {
        name: "Vibrant Topo & Streets",
        base: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        labels: null,
        attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, USGS, NOAA'
    },
    dark: {
        name: "Dark Tactical Radar",
        base: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        labels: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
        attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin'
    },
    light: {
        name: "Daylight Administrative",
        base: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        labels: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
        attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin'
    },
    osm: {
        name: "OpenStreetMap Standard",
        base: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        labels: null,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
};

let currentMapStyle = localStorage.getItem("imd_map_style") || "satellite";

// Category Colors & FontAwesome Icons
const CATEGORY_STYLES = {
    "Rainfall": { color: "#3b82f6", icon: "fa-cloud-showers-heavy" },
    "Flooding": { color: "#0ea5e9", icon: "fa-water" },
    "Thunderstorm": { color: "#f59e0b", icon: "fa-bolt-lightning" },
    "Heatwave": { color: "#ef4444", icon: "fa-temperature-high" },
    "Fog/Smog": { color: "#94a3b8", icon: "fa-smog" },
    "Dust Storm": { color: "#d97706", icon: "fa-wind" },
    "Strong Winds": { color: "#6366f1", icon: "fa-tornado" },
    "Hailstorm": { color: "#06b6d4", icon: "fa-icicles" },
    "Cyclone": { color: "#e11d48", icon: "fa-hurricane" },
    "Snowfall": { color: "#e2e8f0", icon: "fa-snowflake" }
};

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupFilters();
    setupStreamControls();
    initLiveWeatherCard();
    initLiveStationsLayer();
    loadDashboardData();

    // Listen for theme change events
    window.addEventListener("imdThemeChanged", (e) => {
        const theme = e.detail?.theme || "dark";
        setMapBasemap(theme);
    });

    // Periodic live feed refresh
    setInterval(() => {
        loadDashboardData(true);
    }, 4000);
});

function setMapStyle(styleKey) {
    if (!map) return;
    let key = (styleKey === "voyager") ? "topo" : styleKey;
    if (!MAP_STYLES[key]) key = "satellite";
    currentMapStyle = key;
    localStorage.setItem("imd_map_style", key);

    if (baseTileLayer) {
        map.removeLayer(baseTileLayer);
        baseTileLayer = null;
    }
    if (labelsTileLayer) {
        map.removeLayer(labelsTileLayer);
        labelsTileLayer = null;
    }

    const config = MAP_STYLES[key];
    baseTileLayer = L.tileLayer(config.base, {
        attribution: config.attribution,
        subdomains: "abcd",
        maxZoom: 18
    }).addTo(map);

    if (config.labels) {
        labelsTileLayer = L.tileLayer(config.labels, {
            subdomains: "abcd",
            maxZoom: 18,
            pane: "overlayPane"
        }).addTo(map);
    }

    const selectEl = document.getElementById("map-style-select");
    if (selectEl && selectEl.value !== key) {
        selectEl.value = key;
    }
}

function setMapBasemap(theme) {
    // Only adapt if currently on standard dark or light basemaps
    const saved = localStorage.getItem("imd_map_style");
    if (!saved || saved === "dark" || saved === "light") {
        setMapStyle(theme === "light" ? "light" : "dark");
    }
}

function initMap() {
    // Center map on India
    map = L.map("map-view", {
        center: [21.5937, 79.9629],
        zoom: 5,
        minZoom: 4,
        maxZoom: 16
    });

    // Initialize with stunning Satellite Photography (or user choice)
    setMapStyle(currentMapStyle);

    markersLayer = L.layerGroup().addTo(map);

    // Map style selector dropdown listener
    const styleSelect = document.getElementById("map-style-select");
    if (styleSelect) {
        styleSelect.value = currentMapStyle;
        styleSelect.addEventListener("change", (e) => {
            setMapStyle(e.target.value);
        });
    }

    // Map controls
    document.getElementById("btn-recenter-india")?.addEventListener("click", () => {
        map.setView([21.5937, 79.9629], 5);
    });

    document.getElementById("btn-locate-me")?.addEventListener("click", () => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition((pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                map.setView([lat, lon], 10);
                if (userRadiusCircle) map.removeLayer(userRadiusCircle);
                userRadiusCircle = L.circle([lat, lon], {
                    radius: 25000, // 25km radius
                    color: "#3b82f6",
                    fillColor: "#3b82f6",
                    fillOpacity: 0.15
                }).addTo(map);
            });
        }
    });

    document.getElementById("btn-toggle-heatmap")?.addEventListener("click", () => {
        toggleHeatmap();
    });
}

function createMarkerIcon(category, isFake, severity) {
    const style = CATEGORY_STYLES[category] || { color: "#3b82f6", icon: "fa-cloud" };
    const borderColor = isFake ? "#f43f5e" : "#ffffff";
    const badgeIcon = isFake ? "fa-triangle-exclamation" : style.icon;
    const pulseClass = severity === "extreme" ? "pulse-marker" : "";

    const html = `
        <div class="custom-pin ${pulseClass}" style="
            background-color: ${style.color};
            border: 2px solid ${borderColor};
            width: 34px; height: 34px;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: #ffffff;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.75), 0 0 12px ${style.color};
            font-size: 14px;
            position: relative;
        ">
            <i class="fa-solid ${badgeIcon}"></i>
            ${isFake ? '<span style="position:absolute;top:-4px;right:-4px;background:#f43f5e;color:#fff;border:1.5px solid #fff;border-radius:50%;width:14px;height:14px;font-size:8px;display:flex;align-items:center;justify-content:center;font-weight:bold;">!</span>' : ''}
        </div>
    `;

    return L.divIcon({
        className: "custom-div-marker",
        html: html,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
        popupAnchor: [0, -17]
    });
}

async function loadDashboardData(isBackgroundPoll = false) {
    try {
        const queryParams = getActiveFilterParams();
        const url = `/api/reports?${queryParams.toString()}`;

        const [reportsRes, clustersRes, summaryRes] = await Promise.all([
            fetch(url),
            fetch("/api/clusters"),
            fetch("/api/analytics")
        ]);

        if (reportsRes.ok) {
            const data = await reportsRes.json();
            currentReports = data.reports || [];
            renderMarkers(currentReports);
            renderLiveFeed(currentReports);

            const countEl = document.getElementById("feed-count");
            if (countEl) countEl.textContent = currentReports.length;
        }

        if (clustersRes.ok) {
            const cdata = await clustersRes.json();
            currentClusters = cdata.clusters || [];
            renderIncidentClusters(currentClusters);

            const cCountEl = document.getElementById("clusters-count");
            if (cCountEl) cCountEl.textContent = currentClusters.length;
        }

        if (summaryRes.ok && !isBackgroundPoll) {
            const sdata = await summaryRes.json();
            updateKPIs(sdata);
            if (typeof updateChartsWithData === "function") {
                updateChartsWithData(sdata);
            }
        }
    } catch (err) {
        console.error("Dashboard sync error:", err);
    }
}

function renderMarkers(reports) {
    markersLayer.clearLayers();
    const heatPoints = [];

    reports.forEach((r) => {
        if (r.latitude && r.longitude) {
            const marker = L.marker([r.latitude, r.longitude], {
                icon: createMarkerIcon(r.detected_category, r.is_fake, r.severity_level)
            });

            // Rich Tooltip & Popup
            const reasonsHtml = (r.fake_reasons || [])
                .map(reason => `<span class="reason-tag">${reason}</span>`)
                .join("");

            const mediaHtml = (r.media_urls && r.media_urls.length > 0)
                ? `<div style="margin-top:6px;"><img src="${r.media_urls[0]}" style="width:100%;max-height:110px;object-fit:cover;border-radius:4px;border:1px solid #334155;"></div>`
                : "";

            const authClass = r.is_fake ? "auth-fake" : (r.authenticity_score > 75 ? "auth-high" : "auth-medium");
            const authText = r.is_fake ? "FLAGGED FAKE / HOAX" : `${r.authenticity_score}% AUTHENTIC`;

            const popupContent = `
                <div class="popup-inner">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span class="report-category-badge cat-${r.detected_category.replace('/', '-')}">
                            ${r.detected_category} (${Math.round(r.category_confidence * 100)}%)
                        </span>
                        <span class="authenticity-badge ${authClass}" style="font-size:0.75rem;">
                            <i class="fa-solid ${r.is_fake ? 'fa-triangle-exclamation' : 'fa-check'}"></i> ${authText}
                        </span>
                    </div>
                    <div class="popup-title">${r.city || "Unknown"}, ${r.state || "India"}</div>
                    <p class="popup-desc">${r.raw_text}</p>
                    ${mediaHtml}
                    ${reasonsHtml ? `<div style="margin-top:6px;">${reasonsHtml}</div>` : ''}
                    <div class="popup-meta" style="margin-top:8px;">
                        <span><i class="fa-solid fa-user"></i> ${r.author_handle} (${r.source_type})</span>
                        <span>${formatRelativeTime(r.timestamp)}</span>
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent, { className: "custom-map-popup", maxWidth: 320 });
            marker.reportId = r.id;
            markersLayer.addLayer(marker);

            // Add to heatmap data
            heatPoints.push([r.latitude, r.longitude, r.severity_level === "extreme" ? 1.0 : 0.6]);
        }
    });

    // Update heatmap layer if initialized
    if (typeof L.heatLayer === "function") {
        if (heatmapLayer) map.removeLayer(heatmapLayer);
        heatmapLayer = L.heatLayer(heatPoints, { radius: 25, blur: 15, maxZoom: 11 });
        if (isHeatmapActive) heatmapLayer.addTo(map);
    }
}

function toggleHeatmap() {
    isHeatmapActive = !isHeatmapActive;
    const btn = document.getElementById("btn-toggle-heatmap");
    if (isHeatmapActive) {
        if (heatmapLayer) heatmapLayer.addTo(map);
        if (btn) btn.classList.add("btn-primary");
    } else {
        if (heatmapLayer) map.removeLayer(heatmapLayer);
        if (btn) btn.classList.remove("btn-primary");
    }
}

function renderLiveFeed(reports) {
    const listEl = document.getElementById("live-feed-list");
    if (!listEl) return;

    if (!reports || reports.length === 0) {
        listEl.innerHTML = `<div class="empty-state" style="padding:2rem;text-align:center;color:#64748b;">No reports match current filters.</div>`;
        return;
    }

    listEl.innerHTML = reports.map(r => {
        const cardClass = r.is_fake ? "card-fake" : (r.verification_status === "verified" ? "card-verified" : "card-unverified");
        const authClass = r.is_fake ? "auth-fake" : (r.authenticity_score > 75 ? "auth-high" : "auth-medium");
        const authText = r.is_fake ? "FAKE" : `${Math.round(r.authenticity_score)}%`;

        return `
            <div class="report-card ${cardClass}" onclick="panToReport(${r.latitude}, ${r.longitude}, ${r.id})">
                <div class="report-meta-header">
                    <span class="author-pill">
                        <i class="fa-solid fa-user"></i> ${r.author_handle}
                    </span>
                    <span class="timestamp-pill">${formatRelativeTime(r.timestamp)}</span>
                </div>
                <div>
                    <span class="report-category-badge cat-${r.detected_category.replace('/', '-')}">
                        ${r.detected_category}
                    </span>
                    <span style="font-size:0.75rem;color:var(--text-secondary);font-weight:600;margin-left:4px;">
                        ${r.city}, ${r.state}
                    </span>
                </div>
                <p class="report-text">${r.raw_text}</p>
                <div class="report-footer">
                    <span><i class="fa-solid fa-satellite"></i> ${r.source_type.toUpperCase()}</span>
                    <span class="authenticity-badge ${authClass}">
                        <i class="fa-solid ${r.is_fake ? 'fa-triangle-exclamation' : 'fa-shield'}"></i> Authenticity: ${authText}
                    </span>
                </div>
            </div>
        `;
    }).join("");
}

function renderIncidentClusters(clusters) {
    const listEl = document.getElementById("incident-clusters-list");
    if (!listEl) return;

    if (!clusters || clusters.length === 0) {
        listEl.innerHTML = `<div class="empty-state" style="padding:2rem;text-align:center;color:#64748b;">No active clusters.</div>`;
        return;
    }

    listEl.innerHTML = clusters.map(c => `
        <div class="report-card card-verified" onclick="panToCluster(${c.center_lat}, ${c.center_lon})">
            <div class="report-meta-header">
                <strong style="color:var(--text-heading);font-size:0.85rem;">${c.title}</strong>
                <span class="badge-imd">${c.report_count} REPORTS MERGED</span>
            </div>
            <p class="report-text" style="color:var(--text-secondary);margin-bottom:6px;">
                ${c.summary || "Spatio-temporally clustered ground observations."}
            </p>
            <div class="report-footer">
                <span style="color:#38bdf8;"><i class="fa-solid fa-location-dot"></i> ${c.city}, ${c.state}</span>
                <span>Last updated: ${formatRelativeTime(c.last_reported_at)}</span>
            </div>
        </div>
    `).join("");
}

function panToReport(lat, lon, id) {
    if (lat && lon && map) {
        map.flyTo([lat, lon], 12, { duration: 1.0 });
        markersLayer.eachLayer(layer => {
            if (layer.reportId === id) {
                layer.openPopup();
            }
        });
    }
}

function panToCluster(lat, lon) {
    if (lat && lon && map) {
        map.flyTo([lat, lon], 11, { duration: 1.0 });
    }
}

function updateKPIs(summary) {
    if (!summary || !summary.totals) return;
    const t = summary.totals;

    const repEl = document.getElementById("kpi-total-reports");
    const cluEl = document.getElementById("kpi-active-clusters");
    const autEl = document.getElementById("kpi-authenticity");
    const fakEl = document.getElementById("kpi-fake-reports");

    if (repEl) repEl.textContent = t.total_reports || 0;
    if (cluEl) cluEl.textContent = t.active_cluster_count || 0;
    if (autEl) autEl.textContent = `${(t.avg_authenticity || 85.0).toFixed(1)}%`;
    if (fakEl) fakEl.textContent = t.fake_count || 0;
}

// Filter Listeners
function setupFilters() {
    const filterIds = ["filter-time", "filter-state", "filter-city", "filter-status", "filter-source"];
    filterIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener("change", () => loadDashboardData());
    });

    // Category chips
    const chips = document.querySelectorAll(".category-chips .chip");
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            const cat = chip.getAttribute("data-category");
            if (cat === "ALL") {
                chips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
            } else {
                document.querySelector('.chip[data-category="ALL"]')?.classList.remove("active");
                chip.classList.toggle("active");
                // If none selected, re-activate ALL
                const anyActive = Array.from(chips).some(c => c.classList.contains("active") && c.getAttribute("data-category") !== "ALL");
                if (!anyActive) {
                    document.querySelector('.chip[data-category="ALL"]')?.classList.add("active");
                }
            }
            loadDashboardData();
        });
    });

    // Reset button
    document.getElementById("btn-reset-filters")?.addEventListener("click", () => {
        filterIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = "all";
        });
        document.getElementById("filter-time").value = "all";
        chips.forEach(c => c.classList.remove("active"));
        document.querySelector('.chip[data-category="ALL"]')?.classList.add("active");
        if (userRadiusCircle) map.removeLayer(userRadiusCircle);
        loadDashboardData();
    });
}

function getActiveFilterParams() {
    const params = new URLSearchParams();

    const timeVal = document.getElementById("filter-time")?.value;
    if (timeVal && timeVal !== "all") {
        const now = new Date();
        if (timeVal === "24h") {
            const cutoff = new Date(now.getTime() - 24 * 3600 * 1000);
            params.set("start_date", cutoff.toISOString());
        } else if (timeVal === "today") {
            const todayStr = now.toISOString().split("T")[0] + "T00:00:00";
            params.set("start_date", todayStr);
        } else if (timeVal === "7d") {
            const cutoff = new Date(now.getTime() - 7 * 24 * 3600 * 1000);
            params.set("start_date", cutoff.toISOString());
        }
    }

    const state = document.getElementById("filter-state")?.value;
    if (state && state !== "all") params.set("state", state);

    const city = document.getElementById("filter-city")?.value;
    if (city && city !== "all") params.set("city", city);

    const status = document.getElementById("filter-status")?.value;
    if (status && status !== "all") params.set("status", status);

    const source = document.getElementById("filter-source")?.value;
    if (source && source !== "all") params.set("source_type", source);

    // Selected categories
    const allChipActive = document.querySelector('.chip[data-category="ALL"]')?.classList.contains("active");
    if (!allChipActive) {
        const activeChips = Array.from(document.querySelectorAll(".category-chips .chip.active"))
            .map(c => c.getAttribute("data-category"))
            .filter(Boolean);
        if (activeChips.length > 0) {
            params.set("categories", activeChips.join(","));
        }
    }

    return params;
}

// Ingestion Stream Controls
function setupStreamControls() {
    const toggleBtn = document.getElementById("btn-toggle-stream");
    const pulseBtn = document.getElementById("btn-stream-pulse");
    const syncRadarBtn = document.getElementById("btn-sync-meteo");

    if (toggleBtn) {
        toggleBtn.addEventListener("click", async () => {
            const streamStatus = document.getElementById("header-stream-status")?.textContent;
            const isLive = streamStatus.includes("LIVE");
            const endpoint = isLive ? "/api/stream/stop" : "/api/stream/start";

            try {
                const res = await fetch(endpoint, { method: "POST" });
                if (res.ok) {
                    pollTelemetry();
                }
            } catch (err) {
                console.error("Stream toggle error:", err);
            }
        });
    }

    if (pulseBtn) {
        pulseBtn.addEventListener("click", async () => {
            try {
                pulseBtn.disabled = true;
                const res = await fetch("/api/stream/pulse", { method: "POST" });
                if (res.ok) {
                    await loadDashboardData();
                }
            } catch (err) {
                console.error("Pulse error:", err);
            } finally {
                pulseBtn.disabled = false;
            }
        });
    }

    if (syncRadarBtn) {
        syncRadarBtn.addEventListener("click", async () => {
            try {
                syncRadarBtn.disabled = true;
                syncRadarBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Syncing...`;
                const res = await fetch("/api/stream/sync-meteo", { method: "POST" });
                if (res.ok) {
                    await loadDashboardData();
                }
            } catch (err) {
                console.error("Radar sync error:", err);
            } finally {
                syncRadarBtn.disabled = false;
                syncRadarBtn.innerHTML = `<i class="fa-solid fa-tower-broadcast"></i> Sync Radar`;
            }
        });
    }
}

// INSAT-3DR High-Resolution Satellite Photo Modal Controls
function openInsatModal() {
    const modal = document.getElementById("insat-photo-modal");
    if (modal) {
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }
}

function closeInsatModal() {
    const modal = document.getElementById("insat-photo-modal");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "";
    }
}

// Global modal dismiss listeners
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeInsatModal();
});

document.addEventListener("click", (e) => {
    const modal = document.getElementById("insat-photo-modal");
    if (modal && e.target === modal) {
        closeInsatModal();
    }
});

// ====================================================================
// Real-Time Live Meteorological Ground Station Controller
// ====================================================================

async function fetchAndDisplayLiveWeather(city = null, lat = null, lon = null) {
    const displayEl = document.getElementById("live-weather-display");
    if (!displayEl) return;

    try {
        let url = "/api/weather/live?";
        if (city) {
            url += `city=${encodeURIComponent(city)}`;
        } else if (lat !== null && lon !== null) {
            url += `lat=${lat}&lon=${lon}`;
        } else {
            url += "city=New%20Delhi";
        }

        const res = await fetch(url);
        if (!res.ok) throw new Error("Station offline or network error");
        const json = await res.json();
        const data = json.data;
        if (!data) return;

        // Populate Hero details
        const stationEl = document.getElementById("lw-station-name");
        const timeEl = document.getElementById("lw-timestamp");
        const tempEl = document.getElementById("lw-temp");
        const descEl = document.getElementById("lw-desc");
        const iconEl = document.getElementById("lw-icon");
        const feelsEl = document.getElementById("lw-feels-like");
        const humidEl = document.getElementById("lw-humidity");
        const windEl = document.getElementById("lw-wind");
        const rainEl = document.getElementById("lw-rain");
        const pressEl = document.getElementById("lw-pressure");
        const catEl = document.getElementById("lw-category");
        const hourlyStrip = document.getElementById("lw-hourly-strip");

        if (stationEl) stationEl.textContent = `${data.city}, ${data.state}`;
        if (timeEl) timeEl.innerHTML = `<span class="live-sensor-dot"></span> Live Telemetry &bull; Ground Station Sensor (${data.latitude.toFixed(2)}°N, ${data.longitude.toFixed(2)}°E)`;
        if (tempEl) tempEl.textContent = `${data.temperature}°`;
        if (descEl) descEl.innerHTML = `${data.emoji} <strong>${data.condition_desc}</strong> &bull; Ground Truth Sensor`;
        if (iconEl) iconEl.className = `fa-solid ${data.icon} hero-weather-icon`;
        if (feelsEl) feelsEl.textContent = `${data.apparent_temperature}°C`;
        if (humidEl) humidEl.textContent = `${data.humidity}%`;
        if (windEl) windEl.textContent = `${data.wind_speed_kmh} km/h`;
        if (rainEl) rainEl.textContent = `${data.precipitation_mm} mm`;
        if (pressEl) pressEl.textContent = `${data.pressure_hpa} hPa`;
        if (catEl) catEl.textContent = data.category;

        // Populate Hourly Strip
        if (hourlyStrip && data.hourly && data.hourly.length > 0) {
            hourlyStrip.innerHTML = data.hourly.map(h => `
                <div class="hourly-pill">
                    <span class="h-time">${h.time}</span>
                    <span class="h-icon"><i class="fa-solid ${h.icon}"></i></span>
                    <span class="h-temp">${h.temp}°C</span>
                    <span class="h-rain"><i class="fa-solid fa-droplet"></i> ${h.rain_prob}%</span>
                </div>
            `).join("");
        }
    } catch (err) {
        console.error("[LIVE WEATHER] Fetch error:", err);
    }
}

function initLiveWeatherCard() {
    const select = document.getElementById("live-weather-city-select");
    const detectBtn = document.getElementById("btn-detect-my-weather");
    const refreshBtn = document.getElementById("btn-refresh-live-weather");

    if (select) {
        select.addEventListener("change", (e) => {
            fetchAndDisplayLiveWeather(e.target.value);
        });
    }

    if (detectBtn) {
        detectBtn.addEventListener("click", () => {
            if (!navigator.geolocation) {
                alert("Geolocation is not supported by your browser.");
                return;
            }
            detectBtn.disabled = true;
            detectBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Detecting...`;
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    fetchAndDisplayLiveWeather(null, lat, lon);
                    detectBtn.disabled = false;
                    detectBtn.innerHTML = `<i class="fa-solid fa-location-crosshairs"></i> My Live Weather`;
                    if (map) {
                        map.flyTo([lat, lon], 9, { duration: 1.2 });
                    }
                },
                (err) => {
                    alert("Could not acquire GPS position: " + err.message);
                    detectBtn.disabled = false;
                    detectBtn.innerHTML = `<i class="fa-solid fa-location-crosshairs"></i> My Live Weather`;
                }
            );
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            const currentCity = select ? select.value : "New Delhi";
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
            fetchAndDisplayLiveWeather(currentCity).finally(() => {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i>`;
            });
        });
    }

    // Load initial city weather (New Delhi default)
    fetchAndDisplayLiveWeather("New Delhi");
}

// ====================================================================
// Map Live Ground Weather Stations Layer
// ====================================================================

function initLiveStationsLayer() {
    if (!map) return;
    liveStationsLayer = L.layerGroup();

    const toggleBtn = document.getElementById("btn-toggle-live-stations");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            toggleLiveStations();
        });
    }
}

async function toggleLiveStations() {
    isLiveStationsActive = !isLiveStationsActive;
    const btn = document.getElementById("btn-toggle-live-stations");

    if (isLiveStationsActive) {
        if (btn) {
            btn.classList.add("btn-primary");
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Loading Stations...`;
        }

        try {
            const res = await fetch("/api/weather/stations");
            if (!res.ok) throw new Error("Failed to load stations");
            const data = await res.json();
            const stations = data.stations || [];

            liveStationsLayer.clearLayers();

            stations.forEach(st => {
                if (st.lat && st.lon) {
                    // Custom HTML Temperature Badge
                    const badgeHtml = `
                        <div class="station-map-badge">
                            <span class="st-emoji">${st.emoji}</span>
                            <span class="st-temp">${st.temp}°</span>
                            <span class="st-name">${st.city}</span>
                        </div>
                    `;

                    const customIcon = L.divIcon({
                        className: "station-div-icon",
                        html: badgeHtml,
                        iconSize: [88, 30],
                        iconAnchor: [44, 15]
                    });

                    const marker = L.marker([st.lat, st.lon], { icon: customIcon });

                    const popupContent = `
                        <div class="popup-inner">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                                <span class="badge-station-live"><i class="fa-solid fa-tower-broadcast"></i> LIVE IMD SENSOR</span>
                                <span style="font-weight:700;font-size:1.1rem;color:#38bdf8;">${st.temp}°C</span>
                            </div>
                            <div class="popup-title">${st.city}, ${st.state}</div>
                            <div style="font-size:0.88rem;color:#cbd5e1;margin-bottom:8px;">${st.emoji} ${st.desc} (Feels like ${st.feels_like}°C)</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.8rem;background:rgba(255,255,255,0.04);padding:8px;border-radius:6px;">
                                <div><i class="fa-solid fa-droplet text-cyan"></i> Humidity: <strong>${st.humidity}%</strong></div>
                                <div><i class="fa-solid fa-wind text-blue"></i> Wind: <strong>${st.wind} km/h</strong></div>
                                <div><i class="fa-solid fa-cloud-rain text-emerald"></i> Rain: <strong>${st.rain} mm</strong></div>
                                <div><i class="fa-solid fa-layer-group text-amber"></i> Category: <strong>${st.category}</strong></div>
                            </div>
                            <button class="btn btn-secondary btn-sm" style="width:100%;margin-top:8px;" onclick="selectCityForWeather('${st.city}')">
                                <i class="fa-solid fa-chart-line"></i> Inspect Full Forecast
                            </button>
                        </div>
                    `;

                    marker.bindPopup(popupContent, { className: "custom-map-popup", maxWidth: 290 });
                    liveStationsLayer.addLayer(marker);
                }
            });

            liveStationsLayer.addTo(map);
            if (btn) {
                btn.innerHTML = `<i class="fa-solid fa-temperature-three-quarters"></i> Live Stations (ON)`;
            }
        } catch (err) {
            console.error("[LIVE STATIONS] Error loading stations layer:", err);
            if (btn) {
                btn.classList.remove("btn-primary");
                btn.innerHTML = `<i class="fa-solid fa-temperature-three-quarters"></i> Live Stations`;
            }
            isLiveStationsActive = false;
        }
    } else {
        if (liveStationsLayer) map.removeLayer(liveStationsLayer);
        if (btn) {
            btn.classList.remove("btn-primary");
            btn.innerHTML = `<i class="fa-solid fa-temperature-three-quarters"></i> Live Stations`;
        }
    }
}
