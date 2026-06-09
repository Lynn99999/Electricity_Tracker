function getTimelinePoints() {
    const timelinePointsElement = document.getElementById("timeline-points");

    if (!timelinePointsElement) {
        return [];
    }

    return JSON.parse(timelinePointsElement.textContent);
}

function buildScheduleTrack(track, points) {
    points.forEach(function (point, index) {
        const item = document.createElement("div");
        const marker = document.createElement("span");
        const label = document.createElement("span");

        item.className = "schedule-hour";
        item.dataset.pointIndex = index;

        marker.className = "schedule-hour-marker";

        label.className = "schedule-hour-label";
        label.textContent = point.label;

        item.appendChild(label);
        item.appendChild(marker);
        track.appendChild(item);
    });
}

function getFocusedPointIndex(scroll, points) {
    const maxScrollLeft = scroll.scrollWidth - scroll.clientWidth;

    if (maxScrollLeft <= 0) {
        return 0;
    }

    const progress = scroll.scrollLeft / maxScrollLeft;
    const focusedIndex = Math.round(progress * (points.length - 1));

    return Math.max(0, Math.min(focusedIndex, points.length - 1));
}

function previewPointOnMap(point) {
    if (!window.electricityMap || !point) {
        return;
    }

    if (point.is_current_period) {
        window.electricityMap.setCurrentStatusColors();
        return;
    }

    window.electricityMap.setSchedulePreviewColors(point.active_group);
}

function updateSelectedTime(selectedTime, point) {
    if (!selectedTime || !point) {
        return;
    }

    selectedTime.textContent = point.label;
}

function updateActiveHour(scroll, points, selectedTime) {
    const focusedIndex = getFocusedPointIndex(scroll, points);
    const items = Array.from(scroll.querySelectorAll(".schedule-hour"));

    items.forEach(function (item, index) {
        item.classList.toggle("is-active", index === focusedIndex);
    });

    updateSelectedTime(selectedTime, points[focusedIndex]);
    previewPointOnMap(points[focusedIndex]);
}

function initScheduleMapPreview() {
    const timeline = document.querySelector("[data-schedule-timeline]");
    const scroll = timeline ? timeline.querySelector(".schedule-scroll") : null;
    const track = timeline ? timeline.querySelector("[data-schedule-track]") : null;
    const selectedTime = timeline ? timeline.querySelector("[data-schedule-selected-time]") : null;
    const points = getTimelinePoints();

    if (!timeline || !scroll || !track || points.length === 0) {
        return;
    }

    buildScheduleTrack(track, points);
    updateActiveHour(scroll, points, selectedTime);

    scroll.addEventListener("scroll", function () {
        updateActiveHour(scroll, points, selectedTime);
    });
}

initScheduleMapPreview();
