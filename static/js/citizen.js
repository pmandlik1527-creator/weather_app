/**
 * National Weather Big Data Analytics Platform (NWBDAP)
 * Citizen Weather Intelligence Desk Script
 */

document.addEventListener("DOMContentLoaded", () => {
    setupGeolocation();
    setupCategoryPicker();
    setupPhotoDropzone();
    setupFormSubmission();
});

// GPS Auto-Detection
function setupGeolocation() {
    const btn = document.getElementById("btn-acquire-gps");
    const statusText = document.getElementById("gps-display-status");
    const coordsText = document.getElementById("gps-coords-text");
    const inputLat = document.getElementById("input-latitude");
    const inputLon = document.getElementById("input-longitude");
    const inputCity = document.getElementById("input-city");
    const selectState = document.getElementById("select-state");

    if (!btn) return;

    btn.addEventListener("click", () => {
        if (!("geolocation" in navigator)) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Acquiring GPS Satellites...`;
        statusText.textContent = "Locking GPS Coordinates...";
        statusText.style.color = "#f59e0b";

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(5);
                const lon = pos.coords.longitude.toFixed(5);

                inputLat.value = lat;
                inputLon.value = lon;

                statusText.textContent = "GPS Coordinates Locked Successfully";
                statusText.style.color = "#10b981";
                coordsText.textContent = `Lat: ${lat}, Lon: ${lon} (Accuracy: ±${Math.round(pos.coords.accuracy)}m)`;

                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-circle-check"></i> GPS Locked`;
                btn.className = "btn btn-success btn-sm";

                // Reverse Geocode lookup via Open-Meteo or free nominatim fallback if needed
                reverseGeocode(lat, lon, inputCity, selectState);
            },
            (err) => {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-crosshairs"></i> Retry GPS Detection`;
                statusText.textContent = "Location Permission Denied or Unavailable";
                statusText.style.color = "#f43f5e";
                coordsText.textContent = "Please enter your City and State manually below.";
            },
            { enableHighAccuracy: true, timeout: 8000 }
        );
    });
}

// Reverse Geocode Helper
async function reverseGeocode(lat, lon, inputCity, selectState) {
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`);
        if (res.ok) {
            const data = await res.json();
            const addr = data.address || {};
            const detectedCity = addr.city || addr.town || addr.suburb || addr.district || addr.county || "";
            const detectedState = addr.state || "";

            if (detectedCity && !inputCity.value) inputCity.value = detectedCity;
            if (detectedState) {
                // Select matching option in state dropdown
                for (let opt of selectState.options) {
                    if (opt.value.toLowerCase() === detectedState.toLowerCase()) {
                        selectState.value = opt.value;
                        break;
                    }
                }
            }
        }
    } catch {
        // Fallback: rely on backend nearest Indian city mapper
    }
}

// Category Card Picker
function setupCategoryPicker() {
    const cards = document.querySelectorAll(".cat-card-opt");
    const inputCat = document.getElementById("input-category");

    cards.forEach(card => {
        card.addEventListener("click", () => {
            cards.forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            const cat = card.getAttribute("data-category");
            if (inputCat) inputCat.value = cat;
        });
    });
}

function addTag(tag) {
    const textarea = document.getElementById("input-description");
    if (!textarea) return;
    if (!textarea.value.includes(tag)) {
        textarea.value = (textarea.value.trim() + " " + tag).trim();
    }
    textarea.focus();
}

// Photo Preview & Dropzone
function setupPhotoDropzone() {
    const dropzone = document.getElementById("photo-dropzone");
    const fileInput = document.getElementById("file-photo");
    const previewBox = document.getElementById("photo-preview-box");
    const imgPreview = document.getElementById("img-preview");
    const inputPhotoUrl = document.getElementById("input-photo-url");

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener("click", (e) => {
        if (e.target.tagName !== "BUTTON") {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (re) => {
                imgPreview.src = re.target.result;
                previewBox.style.display = "flex";
                inputPhotoUrl.value = re.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
}

function setDemoPhoto(url) {
    const previewBox = document.getElementById("photo-preview-box");
    const imgPreview = document.getElementById("img-preview");
    const inputPhotoUrl = document.getElementById("input-photo-url");

    if (imgPreview && previewBox && inputPhotoUrl) {
        imgPreview.src = url;
        previewBox.style.display = "flex";
        inputPhotoUrl.value = url;
    }
}

// Form Submit
function setupFormSubmission() {
    const form = document.getElementById("citizen-report-form");
    const receipt = document.getElementById("submission-receipt");
    const receiptUuid = document.getElementById("receipt-uuid");
    const submitBtn = document.getElementById("btn-submit-report");

    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Ingesting & Running AI Verification...`;

        const severityMap = { "1": "mild", "2": "moderate", "3": "severe", "4": "extreme" };
        const sevVal = document.getElementById("input-severity")?.value || "2";

        const payload = {
            description: document.getElementById("input-description")?.value,
            latitude: document.getElementById("input-latitude")?.value || null,
            longitude: document.getElementById("input-longitude")?.value || null,
            city: document.getElementById("input-city")?.value,
            state: document.getElementById("select-state")?.value,
            category: document.getElementById("input-category")?.value,
            severity: severityMap[sevVal] || "moderate",
            citizen_name: document.getElementById("input-citizen-name")?.value,
            citizen_contact: document.getElementById("input-citizen-contact")?.value,
            photo_url: document.getElementById("input-photo-url")?.value
        };

        try {
            const res = await fetch("/api/report/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (data.success) {
                form.style.display = "none";
                receiptUuid.textContent = data.report_uuid;
                receipt.classList.add("show");
            } else {
                alert("Submission notice: " + (data.message || "Failed to ingest"));
            }
        } catch (err) {
            console.error("Submission error:", err);
            alert("Network error submitting report. Please check server status.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Ground Weather Report to IMD`;
        }
    });
}

function resetFormForNew() {
    const form = document.getElementById("citizen-report-form");
    const receipt = document.getElementById("submission-receipt");
    if (form && receipt) {
        form.reset();
        document.getElementById("photo-preview-box").style.display = "none";
        document.getElementById("input-photo-url").value = "";
        form.style.display = "block";
        receipt.classList.remove("show");
    }
}
