(function () {
    const currentTimeElements = Array.from(document.querySelectorAll("[data-current-time]"));
    const syncConfig = document.querySelector("[data-myanmar-time-url]");
    const SYNC_INTERVAL = 60 * 1000;

    if (currentTimeElements.length === 0) {
        return;
    }

    let baseTime = new Date(currentTimeElements[0].dataset.currentTimeIso);
    let basePerformanceTime = performance.now();

    function formatMyanmarTime(date) {
        return new Intl.DateTimeFormat("en-US", {
            timeZone: "Asia/Yangon",
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit",
            hour12: true,
        }).format(date);
    }

    function getCurrentMyanmarTime() {
        const elapsedMilliseconds = performance.now() - basePerformanceTime;

        return new Date(baseTime.getTime() + elapsedMilliseconds);
    }

    function renderCurrentTime() {
        const currentTime = getCurrentMyanmarTime();
        const formattedTime = formatMyanmarTime(currentTime);

        currentTimeElements.forEach(function (element) {
            element.textContent = formattedTime;
        });
    }

    function setBaseTime(isoTime) {
        const syncedTime = new Date(isoTime);

        if (Number.isNaN(syncedTime.getTime())) {
            return;
        }

        baseTime = syncedTime;
        basePerformanceTime = performance.now();
        renderCurrentTime();
    }

    function syncWithServer() {
        if (!syncConfig) {
            return;
        }

        fetch(syncConfig.dataset.myanmarTimeUrl, {
            headers: {
                "Accept": "application/json",
            },
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Could not sync Myanmar time.");
                }

                return response.json();
            })
            .then(function (data) {
                if (data.myanmar_time) {
                    setBaseTime(data.myanmar_time);
                }
            })
            .catch(function () {
                // Keep using the current local baseline if sync fails.
            });
    }

    renderCurrentTime();
    setInterval(renderCurrentTime, 1000);
    setInterval(syncWithServer, SYNC_INTERVAL);

    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
            syncWithServer();
        }
    });
})();
