const offlineRetryButton = document.querySelector("[data-offline-retry]");
const offlineContent = document.querySelector("[data-offline-content]");
const offlineTitle = document.querySelector("[data-offline-title]");
const offlineCachedAt = document.querySelector("[data-offline-cached-at]");
const offlineSelector = document.querySelector("[data-offline-selector]");
let offlineScheduleData = null;
let activeScheduleKey = null;

function formatCachedAt(value) {
    if (!value) {
        return "Not available";
    }

    return new Intl.DateTimeFormat("en-US", {
        timeZone: "Asia/Yangon",
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    }).format(new Date(value));
}

function createSlot(slot) {
    const slotElement = document.createElement("div");
    slotElement.className = `offline-slot ${slot.status === "ON" ? "is-on" : "is-off"}`;

    slotElement.innerHTML = `
        <div class="offline-slot-time"></div>
        <div class="offline-slot-status"></div>
    `;

    slotElement.querySelector(".offline-slot-time").textContent = slot.time;
    slotElement.querySelector(".offline-slot-status").textContent = slot.status;

    return slotElement;
}

function createDayCard(day) {
    const dayCard = document.createElement("section");
    dayCard.className = `offline-schedule-day card shadow-sm ${day.is_today ? "is-today" : ""}`;

    dayCard.innerHTML = `
        <div class="card-header bg-white d-flex align-items-center justify-content-between gap-3">
            <div class="d-flex align-items-center gap-2">
                <span class="offline-calendar">□</span>
                <strong></strong>
                <span class="badge text-bg-light border text-muted d-none" data-yesterday>Yesterday</span>
                <span class="badge text-bg-warning d-none" data-today>Today</span>
            </div>
            <span class="text-muted" data-day-name></span>
        </div>
        <div class="card-body">
            <div class="offline-slot-grid"></div>
        </div>
    `;

    dayCard.querySelector("strong").textContent = day.date;
    dayCard.querySelector("[data-day-name]").textContent = day.day;

    if (day.is_yesterday) {
        dayCard.querySelector("[data-yesterday]").classList.remove("d-none");
    }

    if (day.is_today) {
        dayCard.querySelector("[data-today]").classList.remove("d-none");
    }

    const slotGrid = dayCard.querySelector(".offline-slot-grid");

    if (day.slots.length === 0) {
        slotGrid.innerHTML = `<p class="text-secondary mb-0">No schedule</p>`;
        return dayCard;
    }

    day.slots.forEach(function (slot) {
        slotGrid.appendChild(createSlot(slot));
    });

    return dayCard;
}

function createScheduleSection(title, timetable) {
    const section = document.createElement("div");
    section.className = "d-grid gap-3";

    const heading = document.createElement("div");
    heading.className = "offline-group-title";
    heading.textContent = title;
    section.appendChild(heading);

    timetable.forEach(function (day) {
        section.appendChild(createDayCard(day));
    });

    return section;
}

function createTownshipList(townships) {
    const listCard = document.createElement("section");
    listCard.className = "offline-township-list card shadow-sm";

    listCard.innerHTML = `
        <div class="card-body">
            <p class="offline-group-title mb-3">Townships in this group</p>
            <div class="offline-township-chips"></div>
        </div>
    `;

    const chipContainer = listCard.querySelector(".offline-township-chips");

    townships.forEach(function (townshipName) {
        const chip = document.createElement("span");
        chip.className = "offline-township-chip";
        chip.textContent = townshipName;
        chipContainer.appendChild(chip);
    });

    return listCard;
}

function getScheduleOptions(data) {
    const options = [];

    if (data.first_favorite) {
        options.push({
            key: "favorite",
            label: "Favorite",
            title: data.first_favorite.name,
            sectionTitle: `${data.first_favorite.name} Schedule`,
            timetable: data.first_favorite.timetable,
        });

        return options;
    }

    options.push({
        key: "group-a",
        label: "Group A",
        title: "Group A",
        sectionTitle: "Group A Schedule",
        townships: data.groups.A.townships,
        timetable: data.groups.A.timetable,
    });

    options.push({
        key: "group-b",
        label: "Group B",
        title: "Group B",
        sectionTitle: "Group B Schedule",
        townships: data.groups.B.townships,
        timetable: data.groups.B.timetable,
    });

    return options;
}

function renderSelector(options) {
    if (!offlineSelector) {
        return;
    }

    offlineSelector.innerHTML = "";

    if (options.length <= 1) {
        return;
    }

    options.forEach(function (option) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `btn btn-sm ${option.key === activeScheduleKey ? "btn-dark" : "btn-outline-dark"}`;
        button.textContent = option.label;
        button.dataset.scheduleKey = option.key;

        button.addEventListener("click", function () {
            activeScheduleKey = option.key;
            renderOfflineSchedule(offlineScheduleData);
        });

        offlineSelector.appendChild(button);
    });
}

function renderOfflineSchedule(data) {
    if (!offlineContent || !data) {
        return;
    }

    offlineScheduleData = data;

    offlineContent.innerHTML = "";

    if (offlineCachedAt) {
        offlineCachedAt.textContent = formatCachedAt(data.cached_at);
    }

    const options = getScheduleOptions(data);

    if (!activeScheduleKey) {
        activeScheduleKey = options[0].key;
    }

    const activeOption = options.find(function (option) {
        return option.key === activeScheduleKey;
    }) || options[0];

    activeScheduleKey = activeOption.key;
    renderSelector(options);

    if (offlineTitle) {
        offlineTitle.textContent = activeOption.title;
    }

    if (activeOption.townships) {
        offlineContent.appendChild(createTownshipList(activeOption.townships));
    }

    offlineContent.appendChild(
        createScheduleSection(activeOption.sectionTitle, activeOption.timetable)
    );
}

function loadOfflineSchedule() {
    const rawData = localStorage.getItem(OFFLINE_SCHEDULE_CACHE_KEY);

    if (!rawData) {
        return;
    }

    try {
        renderOfflineSchedule(JSON.parse(rawData));
    } catch (error) {
        console.error(error);
    }
}

if (offlineRetryButton) {
    offlineRetryButton.addEventListener("click", function () {
        window.location.reload();
    });
}

loadOfflineSchedule();
window.addEventListener("offlineScheduleCached", loadOfflineSchedule);
