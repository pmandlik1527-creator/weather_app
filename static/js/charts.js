/**
 * National Weather Big Data Analytics Platform (NWBDAP)
 * Chart.js Operational Visualizations
 */

let timelineChartInstance = null;
let categoryChartInstance = null;
let hotspotsChartInstance = null;

function getActiveTheme() {
    return (typeof document !== "undefined" && (
        document.body?.classList.contains("light-theme") ||
        document.documentElement?.getAttribute("data-theme") === "light" ||
        localStorage.getItem("imd_theme") === "light"
    )) ? "light" : "dark";
}

function applyChartThemeDefaults(theme) {
    if (typeof Chart === "undefined") return;
    if (theme === "light") {
        Chart.defaults.color = "#475569";
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.size = 11;
        Chart.defaults.borderColor = "rgba(0, 0, 0, 0.08)";
    } else {
        Chart.defaults.color = "#94a3b8";
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.size = 11;
        Chart.defaults.borderColor = "rgba(255, 255, 255, 0.06)";
    }
}

// Set initial styling based on active theme
applyChartThemeDefaults(getActiveTheme());

// Listen for global theme switches
if (typeof window !== "undefined") {
    window.addEventListener("imdThemeChanged", (e) => {
        const theme = e.detail?.theme || getActiveTheme();
        applyChartThemeDefaults(theme);

        if (categoryChartInstance && categoryChartInstance.data?.datasets?.[0]) {
            categoryChartInstance.data.datasets[0].borderColor = theme === "light" ? "#ffffff" : "#111827";
        }

        if (timelineChartInstance) timelineChartInstance.update();
        if (categoryChartInstance) categoryChartInstance.update();
        if (hotspotsChartInstance) hotspotsChartInstance.update();
    });
}

function updateChartsWithData(summary) {
    if (!summary) return;
    renderTimelineChart(summary.timeline || []);
    renderCategoryChart(summary.categories || []);
    renderHotspotsChart(summary.state_hotspots || []);
}

function renderTimelineChart(timelineData) {
    const ctx = document.getElementById("timelineChart");
    if (!ctx) return;

    const labels = timelineData.map(d => d.date_str);
    const totalCounts = timelineData.map(d => d.total_count);
    const verifiedCounts = timelineData.map(d => d.verified_count);
    const fakeCounts = timelineData.map(d => d.fake_count);

    if (timelineChartInstance) {
        timelineChartInstance.destroy();
    }

    timelineChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels.length > 0 ? labels : ["Today"],
            datasets: [
                {
                    label: "Total Ingested",
                    data: totalCounts.length > 0 ? totalCounts : [12],
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 4
                },
                {
                    label: "Verified Ground Truth",
                    data: verifiedCounts.length > 0 ? verifiedCounts : [8],
                    borderColor: "#10b981",
                    backgroundColor: "transparent",
                    tension: 0.35,
                    borderWidth: 2,
                    borderDash: [4, 4],
                    pointRadius: 3
                },
                {
                    label: "Flagged Misinformation",
                    data: fakeCounts.length > 0 ? fakeCounts : [3],
                    borderColor: "#f43f5e",
                    backgroundColor: "transparent",
                    tension: 0.35,
                    borderWidth: 1.5,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: { boxWidth: 12, padding: 10 }
                },
                tooltip: {
                    mode: "index",
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

function renderCategoryChart(categoryData) {
    const ctx = document.getElementById("categoryChart");
    if (!ctx) return;

    const labels = categoryData.map(c => c.detected_category);
    const counts = categoryData.map(c => c.count);

    const defaultColors = [
        "#3b82f6", "#0ea5e9", "#f59e0b", "#ef4444", "#94a3b8",
        "#d97706", "#6366f1", "#06b6d4", "#e11d48", "#f1f5f9"
    ];

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels.length > 0 ? labels : ["Rainfall", "Flooding", "Heatwave"],
            datasets: [{
                data: counts.length > 0 ? counts : [5, 4, 3],
                backgroundColor: defaultColors.slice(0, labels.length || 3),
                borderWidth: 1,
                borderColor: getActiveTheme() === "light" ? "#ffffff" : "#111827"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 10, padding: 8 }
                }
            }
        }
    });
}

function renderHotspotsChart(hotspotsData) {
    const ctx = document.getElementById("hotspotsChart");
    if (!ctx) return;

    const labels = hotspotsData.map(h => h.state);
    const counts = hotspotsData.map(h => h.count);

    if (hotspotsChartInstance) {
        hotspotsChartInstance.destroy();
    }

    hotspotsChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels.length > 0 ? labels : ["Maharashtra", "Delhi", "Karnataka"],
            datasets: [{
                label: "Weather Events Reported",
                data: counts.length > 0 ? counts : [6, 4, 3],
                backgroundColor: "rgba(56, 189, 248, 0.65)",
                borderColor: "#38bdf8",
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}
