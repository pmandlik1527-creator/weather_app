/**
 * National Weather Big Data Analytics Platform (NWBDAP)
 * IMD Admin & AI Moderation Console Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    loadModerationQueue();
    loadAuditLogs();
    setupRetrainButton();
});

// Fetch and render reports requiring human-in-the-loop review
async function loadModerationQueue() {
    const tbody = document.getElementById("moderation-queue-body");
    if (!tbody) return;

    try {
        const res = await fetch("/api/reports?limit=50");
        if (!res.ok) return;

        const data = await res.json();
        const reports = data.reports || [];

        if (reports.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#64748b;padding:2rem;">All incoming reports moderated. Moderation queue clear!</td></tr>`;
            return;
        }

        tbody.innerHTML = reports.map(r => {
            const reasonsHtml = (r.fake_reasons || []).map(re => `<span class="reason-tag">${re}</span>`).join("");
            const isFlagged = r.is_fake || r.verification_status === "flagged_fake";
            const authColor = isFlagged ? "#f43f5e" : (r.authenticity_score > 75 ? "#10b981" : "#f59e0b");

            return `
                <tr id="mod-row-${r.id}">
                    <td>
                        <strong style="font-family:var(--font-mono);color:#93c5fd;font-size:0.75rem;">${r.report_uuid}</strong>
                        <br>
                        <span style="font-size:0.7rem;color:#64748b;"><i class="fa-solid fa-satellite"></i> ${r.source_type.toUpperCase()}</span>
                    </td>
                    <td>
                        <strong>${r.city || "Unknown"}, ${r.state || "India"}</strong>
                        <br>
                        <small style="color:#38bdf8;">${r.author_handle}</small>
                    </td>
                    <td>
                        <span class="report-category-badge cat-${r.detected_category.replace('/', '-')}">
                            ${r.detected_category}
                        </span>
                        <div style="font-size:0.7rem;color:#94a3b8;margin-top:2px;">
                            Confidence: <strong>${Math.round(r.category_confidence * 100)}%</strong>
                        </div>
                    </td>
                    <td>
                        <strong style="color:${authColor};font-family:var(--font-mono);font-size:0.85rem;">
                            ${Math.round(r.authenticity_score)}%
                        </strong>
                        <span style="font-size:0.7rem;color:${isFlagged ? '#fda4af' : '#6ee7b7'};">
                            (${isFlagged ? 'FLAGGED FAKE' : 'AUTHENTIC'})
                        </span>
                        <div>${reasonsHtml}</div>
                    </td>
                    <td style="max-width:280px;">
                        <p style="font-size:0.78rem;color:#e2e8f0;line-height:1.35;margin-bottom:4px;">${r.raw_text}</p>
                        <small style="color:#64748b;">${r.timestamp}</small>
                    </td>
                    <td>
                        <div style="display:flex;flex-direction:column;gap:4px;">
                            <button class="btn btn-success btn-sm" onclick="moderateAction(${r.id}, 'verified')" title="Confirm as Authentic Ground Truth">
                                <i class="fa-solid fa-circle-check"></i> Verify
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="moderateAction(${r.id}, 'flagged_fake')" title="Flag as Misleading/Fake">
                                <i class="fa-solid fa-triangle-exclamation"></i> Flag Fake
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="moderateAction(${r.id}, 'rejected')" title="Dismiss from Intelligence">
                                <i class="fa-solid fa-ban"></i> Reject
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Moderation queue fetch error:", err);
    }
}

// Execute analyst moderation decision
async function moderateAction(reportId, newStatus) {
    try {
        const res = await fetch("/api/admin/moderate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                report_id: reportId,
                new_status: newStatus,
                operator: "IMD Duty Officer",
                notes: `Analyst human-in-the-loop action: marked as ${newStatus}`
            })
        });

        if (res.ok) {
            const row = document.getElementById(`mod-row-${reportId}`);
            if (row) {
                row.style.transition = "all 0.4s";
                row.style.opacity = "0.3";
                row.style.backgroundColor = newStatus === "verified" ? "rgba(16, 185, 129, 0.15)" : "rgba(244, 63, 94, 0.15)";
                setTimeout(() => row.remove(), 400);
            }
            loadAuditLogs();
        }
    } catch (err) {
        console.error("Moderation action error:", err);
    }
}

// Ingestion Source Toggle
async function toggleSource(sourceId, targetActive) {
    try {
        const res = await fetch("/api/admin/source/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                source_id: sourceId,
                is_active: targetActive === 1
            })
        });

        if (res.ok) {
            location.reload();
        }
    } catch (err) {
        console.error("Toggle source error:", err);
    }
}

// Fetch Audit Logs
async function loadAuditLogs() {
    const tbody = document.getElementById("audit-logs-body");
    if (!tbody) return;

    try {
        const res = await fetch("/api/admin/audit-logs?limit=25");
        if (!res.ok) return;

        const logs = await res.json();
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#64748b;padding:1.5rem;">No moderation actions recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td style="font-family:var(--font-mono);font-size:0.75rem;color:#94a3b8;">${l.timestamp}</td>
                <td><strong><i class="fa-solid fa-user-shield"></i> ${l.operator_name}</strong></td>
                <td style="font-family:var(--font-mono);color:#60a5fa;">#${l.report_id}</td>
                <td>
                    <span class="reason-tag" style="background:rgba(59,130,246,0.15);color:#93c5fd;border-color:rgba(59,130,246,0.3);">
                        ${l.previous_status || 'unverified'} &rarr; <strong>${l.new_status}</strong>
                    </span>
                </td>
                <td>${l.previous_category === l.new_category ? `<span style="color:#64748b;">Unchanged (${l.new_category})</span>` : `<strong>${l.previous_category} &rarr; ${l.new_category}</strong>`}</td>
                <td style="font-size:0.75rem;color:#cbd5e1;">${l.notes || "Standard analyst confirmation"}</td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Audit log error:", err);
    }
}

// Continuous Learning Retraining Button
function setupRetrainButton() {
    const btn = document.getElementById("btn-trigger-retrain");
    if (!btn) return;

    btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Assimilating Feedback into ML Weights...`;

        try {
            const res = await fetch("/api/admin/retrain", { method: "POST" });
            if (res.ok) {
                const data = await res.json();
                alert(data.message || "Feedback assimilation complete.");
                location.reload();
            }
        } catch (err) {
            console.error("Retrain error:", err);
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Assimilate Feedback & Retrain`;
        }
    });
}
