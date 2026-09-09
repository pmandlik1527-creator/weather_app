/**
 * National Weather Big Data Analytics Platform (NWBDAP)
 * Global Application Controller
 */

// Live IST Clock
function updateClock() {
    const clockEl = document.getElementById("header-clock");
    if (!clockEl) return;
    const now = new Date();
    // India Standard Time (UTC+5:30)
    const options = {
        timeZone: "Asia/Kolkata",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
    };
    clockEl.textContent = `${now.toLocaleTimeString("en-GB", options)} IST`;
}
setInterval(updateClock, 1000);
updateClock();

// ==========================================
// National Live Weather Ticker Strip Controller
// ==========================================
async function refreshLiveTicker(force = false) {
    const trackEl = document.getElementById("live-weather-ticker-track");
    if (!trackEl) return;

    try {
        const res = await fetch("/api/weather/ticker");
        if (!res.ok) return;
        const data = await res.json();
        const items = data.ticker || [];

        if (items.length === 0) return;

        // Build continuous HTML string
        const html = items.map(item => `
            <div class="ticker-city-chip" onclick="selectCityForWeather('${item.city}')" title="Click to inspect ${item.city} live telemetry">
                <span class="t-city"><i class="fa-solid fa-location-dot"></i> ${item.city}</span>
                <span class="t-temp">${item.temp}°C</span>
                <span class="t-emoji">${item.emoji}</span>
                <span class="t-desc">${item.desc}</span>
                <span class="t-meta"><i class="fa-solid fa-droplet"></i> ${item.humidity}%</span>
                <span class="t-meta"><i class="fa-solid fa-wind"></i> ${item.wind}km/h</span>
            </div>
        `).join("");

        // Double the items for seamless infinite horizontal loop
        trackEl.innerHTML = html + html;
    } catch (err) {
        console.warn("[TICKER] Error loading live weather:", err);
    }
}

// Expose globally
window.refreshLiveTicker = refreshLiveTicker;
window.selectCityForWeather = function(cityName) {
    const citySelect = document.getElementById("live-weather-city-select");
    if (citySelect) {
        citySelect.value = cityName;
        citySelect.dispatchEvent(new Event("change"));
        citySelect.scrollIntoView({ behavior: "smooth", block: "center" });
    }
};

// Initial ticker load & periodic 3-min update
document.addEventListener("DOMContentLoaded", () => {
    refreshLiveTicker();
    setInterval(() => refreshLiveTicker(), 180000);
});

// Theme Controller (Light / Dark Mode)
function initTheme() {
    const savedTheme = localStorage.getItem("imd_theme");
    // Default to dark theme as the national operational command aesthetic
    const initialTheme = savedTheme || "dark";
    applyTheme(initialTheme);

    const toggleBtn = document.getElementById("theme-toggle-btn");
    if (toggleBtn && !toggleBtn.dataset.themeBound) {
        toggleBtn.dataset.themeBound = "true";
        toggleBtn.addEventListener("click", () => {
            const isCurrentlyDark = document.body.classList.contains("dark-theme");
            const newTheme = isCurrentlyDark ? "light" : "dark";
            applyTheme(newTheme);
            localStorage.setItem("imd_theme", newTheme);
        });
    }
}

function applyTheme(theme) {
    const label = document.getElementById("theme-text-label");
    if (theme === "light") {
        document.body.classList.remove("dark-theme");
        document.body.classList.add("light-theme");
        document.documentElement.setAttribute("data-theme", "light");
        if (label) label.textContent = "Light";
    } else {
        document.body.classList.remove("light-theme");
        document.body.classList.add("dark-theme");
        document.documentElement.setAttribute("data-theme", "dark");
        if (label) label.textContent = "Dark";
    }
    // Broadcast event for Leaflet map and Chart.js to adapt
    window.dispatchEvent(new CustomEvent("imdThemeChanged", { detail: { theme: theme } }));
}

// Initialize theme immediately on script execution and on DOM load
initTheme();
document.addEventListener("DOMContentLoaded", initTheme);

// Polling System Telemetry
async function pollTelemetry() {
    try {
        const res = await fetch("/api/telemetry");
        if (res.ok) {
            const data = await res.json();
            const throughputEl = document.getElementById("kpi-throughput");
            const latencyEl = document.getElementById("kpi-latency");
            const streamStatusEl = document.getElementById("header-stream-status");
            const streamIcon = document.getElementById("stream-icon");
            const streamBtnText = document.getElementById("stream-btn-text");

            if (throughputEl) throughputEl.textContent = `${data.throughput_per_min || 0}/min`;
            if (latencyEl) latencyEl.textContent = `Latency: ${data.average_latency_ms || 15}ms`;

            if (streamStatusEl) {
                if (data.is_social_streaming) {
                    streamStatusEl.textContent = "LIVE STREAMING";
                    streamStatusEl.className = "status-online";
                    if (streamIcon) streamIcon.className = "fa-solid fa-pause";
                    if (streamBtnText) streamBtnText.textContent = "Pause Stream";
                } else {
                    streamStatusEl.textContent = "STANDBY";
                    streamStatusEl.className = "status-standby";
                    if (streamIcon) streamIcon.className = "fa-solid fa-play";
                    if (streamBtnText) streamBtnText.textContent = "Start Live Stream";
                }
            }
        }
    } catch (err) {
        // Silently tolerate temporary polling blip
    }
}
setInterval(pollTelemetry, 3000);
pollTelemetry();

// Side Tab Switcher (Live Feed vs Incident Clusters)
function switchSideTab(tabName) {
    const btnFeed = document.getElementById("tab-btn-feed");
    const btnClusters = document.getElementById("tab-btn-clusters");
    const feedList = document.getElementById("live-feed-list");
    const clustersList = document.getElementById("incident-clusters-list");

    if (!btnFeed || !btnClusters || !feedList || !clustersList) return;

    if (tabName === "feed") {
        btnFeed.classList.add("active");
        btnClusters.classList.remove("active");
        feedList.style.display = "flex";
        clustersList.style.display = "none";
    } else {
        btnClusters.classList.add("active");
        btnFeed.classList.remove("active");
        clustersList.style.display = "flex";
        feedList.style.display = "none";
    }
}

// Utility: Format relative timestamp
function formatRelativeTime(dateStr) {
    try {
        const d = new Date(dateStr);
        const now = new Date();
        const diffSec = Math.floor((now - d) / 1000);
        if (diffSec < 60) return `${diffSec}s ago`;
        if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
        if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
        return d.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
    } catch {
        return dateStr;
    }
}
