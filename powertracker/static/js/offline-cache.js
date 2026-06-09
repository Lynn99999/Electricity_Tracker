const OFFLINE_SCHEDULE_CACHE_KEY = "electricityTrackerOfflineSchedule";
const offlineDataUrlElement = document.querySelector("[data-offline-data-url]");

function cacheOfflineScheduleData() {
    if (!offlineDataUrlElement) {
        return;
    }

    fetch(offlineDataUrlElement.dataset.offlineDataUrl, {
        headers: {
            "Accept": "application/json",
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Could not cache offline schedule.");
            }

            return response.json();
        })
        .then(function (data) {
            localStorage.setItem(OFFLINE_SCHEDULE_CACHE_KEY, JSON.stringify(data));
            window.dispatchEvent(new CustomEvent("offlineScheduleCached"));
        })
        .catch(function () {});
}

cacheOfflineScheduleData();
