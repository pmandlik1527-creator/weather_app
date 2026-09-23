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
    if (typeof fetchAndDisplayLiveWeather === "function") {
        fetchAndDisplayLiveWeather(cityName);
    }
    const displayEl = document.getElementById("live-weather-display");
    if (displayEl) {
        displayEl.scrollIntoView({ behavior: "smooth", block: "center" });
    }
};

// Initial ticker load & periodic 3-min update
document.addEventListener("DOMContentLoaded", () => {
    refreshLiveTicker();
    setInterval(() => refreshLiveTicker(), 180000);
});

// Theme Controller (Executive Cream / Dark Command Mode)
function initTheme() {
    let savedTheme = localStorage.getItem("imd_theme_v2");
    if (!savedTheme) {
        // First load of the new Cream theme: enforce cream default
        savedTheme = "cream";
        localStorage.setItem("imd_theme_v2", "cream");
    }
    applyTheme(savedTheme);

    const toggleBtn = document.getElementById("theme-toggle-btn");
    if (toggleBtn && !toggleBtn.dataset.themeBound) {
        toggleBtn.dataset.themeBound = "true";
        toggleBtn.addEventListener("click", () => {
            const isCurrentlyDark = document.body.classList.contains("dark-theme");
            const newTheme = isCurrentlyDark ? "cream" : "dark";
            applyTheme(newTheme);
            localStorage.setItem("imd_theme_v2", newTheme);
        });
    }
}

function applyTheme(theme) {
    const label = document.getElementById("theme-text-label");
    if (theme === "dark") {
        document.body.classList.remove("light-theme", "cream-theme");
        document.body.classList.add("dark-theme");
        document.documentElement.setAttribute("data-theme", "dark");
        if (label) label.textContent = "Dark";
    } else {
        document.body.classList.remove("dark-theme");
        document.body.classList.add("cream-theme", "light-theme");
        document.documentElement.setAttribute("data-theme", "cream");
        if (label) label.textContent = "Cream";
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

// ==========================================
// 30-Second Live Scrape & Auto-Refresh Engine
// ==========================================
let liveSyncSecondsRemaining = 30;
let liveSyncTimerInterval = null;
let isScrapingInProgress = false;

function showLiveToast(message, iconClass = "fa-circle-check") {
    const toastEl = document.getElementById("live-toast-alert");
    const msgEl = document.getElementById("live-toast-msg");
    if (!toastEl || !msgEl) return;

    msgEl.innerHTML = `<i class="fa-solid ${iconClass}" style="color: var(--accent-emerald); margin-right: 6px;"></i> ${message}`;
    toastEl.classList.add("show");
    setTimeout(() => {
        toastEl.classList.remove("show");
    }, 4500);
}

async function performLiveScrapeAndRefresh(isManual = false) {
    if (isScrapingInProgress) return;
    isScrapingInProgress = true;

    const countdownEl = document.getElementById("live-sync-countdown");
    const syncBtn = document.getElementById("btn-manual-sync");
    if (syncBtn) syncBtn.classList.add("spinning");
    if (countdownEl) countdownEl.textContent = "Syncing...";

    try {
        // 1. Scrape latest live IMD news, RSS bulletins & ground-truth observations
        const scrapeRes = await fetch("/api/scrape/live-sync?force=true", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        
        let scrapedCount = 0;
        if (scrapeRes.ok) {
            const scrapeData = await scrapeRes.json();
            scrapedCount = scrapeData.scraped_count || 0;
        }

        // 2. Refresh top ticker with updated ground station telemetry
        if (typeof refreshLiveTicker === "function") {
            await refreshLiveTicker(true);
        }

        // 3. Refresh Radar Dashboard data (markers, feed, clusters, KPIs, charts)
        if (typeof window.loadDashboardData === "function") {
            await window.loadDashboardData(false);
        }

        // 4. Refresh live station weather card if present on page
        if (typeof window.fetchAndDisplayLiveWeather === "function") {
            const stateSel = document.getElementById("live-weather-state-select");
            const distSel = document.getElementById("live-weather-district-select");
            const activeState = (stateSel && stateSel.value) ? stateSel.value : (localStorage.getItem("nwbdap_selected_state") || "Maharashtra");
            const activeDist = (distSel && distSel.value) ? distSel.value : (localStorage.getItem("nwbdap_selected_district") || "Pune");
            if (activeDist) {
                window.fetchAndDisplayLiveWeather(activeDist, null, null, activeState, activeDist, true);
            }
        }

        // 5. Notify user via sleek live toast
        if (scrapedCount > 0) {
            showLiveToast(`Live Scrape: ${scrapedCount} new meteorological reports ingested.`);
        } else if (isManual) {
            showLiveToast("Scraped real feeds: All stations and bulletins up to date.");
        }
    } catch (err) {
        console.warn("[LIVE SYNC] Scrape refresh error:", err);
    } finally {
        isScrapingInProgress = false;
        liveSyncSecondsRemaining = 30;
        if (countdownEl) countdownEl.textContent = `${liveSyncSecondsRemaining}s`;
        if (syncBtn) syncBtn.classList.remove("spinning");
    }
}

function initLiveSyncCountdown() {
    const countdownEl = document.getElementById("live-sync-countdown");
    const syncBtn = document.getElementById("btn-manual-sync");

    if (syncBtn && !syncBtn.dataset.bound) {
        syncBtn.dataset.bound = "true";
        syncBtn.addEventListener("click", () => {
            performLiveScrapeAndRefresh(true);
        });
    }

    if (liveSyncTimerInterval) clearInterval(liveSyncTimerInterval);

    liveSyncSecondsRemaining = 30;
    if (countdownEl) countdownEl.textContent = `${liveSyncSecondsRemaining}s`;

    liveSyncTimerInterval = setInterval(() => {
        if (isScrapingInProgress) return;
        liveSyncSecondsRemaining -= 1;
        if (countdownEl) {
            countdownEl.textContent = `${liveSyncSecondsRemaining}s`;
        }
        if (liveSyncSecondsRemaining <= 0) {
            performLiveScrapeAndRefresh(false);
        }
    }, 1000);
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    initLiveSyncCountdown();
});

// Expose globally
window.performLiveScrapeAndRefresh = performLiveScrapeAndRefresh;
