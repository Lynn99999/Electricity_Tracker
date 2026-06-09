const statusRefreshRoot = document.querySelector("[data-statuses-url]");
const STATUS_REFRESH_INTERVAL =  30 * 1000;

function refreshTownshipStatuses() {
    if (!statusRefreshRoot || !window.electricityMap) {
        return;
    }

    fetch(statusRefreshRoot.dataset.statusesUrl, {
        headers: {
            "Accept": "application/json",
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Could not load township statuses.");
            }

            return response.json();
        })
        .then(function (data) {
            window.electricityMap.updateStatuses(data.townships);
        })
        .catch(function () {
            // Keep the existing map colors if the refresh fails.
        });
}

if (statusRefreshRoot) {
    setInterval(refreshTownshipStatuses, STATUS_REFRESH_INTERVAL);
}
