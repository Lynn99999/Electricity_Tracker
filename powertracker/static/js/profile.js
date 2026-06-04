const editButton = document.getElementById("edit-username-button");
const cancelButton = document.getElementById("cancel-username-button");
const usernameDisplay = document.getElementById("username-display");
const usernameForm = document.getElementById("username-form");

if (editButton && cancelButton && usernameDisplay && usernameForm) {
    editButton.addEventListener("click", function () {
        usernameDisplay.classList.add("d-none");
        usernameForm.classList.remove("d-none");
    });

    cancelButton.addEventListener("click", function () {
        usernameForm.classList.add("d-none");
        usernameDisplay.classList.remove("d-none");
    });
}

document.querySelectorAll(".alert").forEach(function (alert) {
    setTimeout(function () {
        alert.classList.remove("show");

        setTimeout(function () {
            alert.remove();
        }, 150);
    }, 1000);
});

const favoriteList = document.querySelector("[data-favorite-list]");

function getCsrfToken() {
    const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
    return csrfInput ? csrfInput.value : "";
}

function getFavoriteRows() {
    return Array.from(favoriteList.querySelectorAll("[data-township-id]"));
}

function updateFavoritePositions() {
    getFavoriteRows().forEach(function (row, index) {
        const position = row.querySelector(".favorite-position");

        if (position) {
            position.textContent = index + 1;
        }
    });
}

function saveFavoriteOrder() {
    const townshipIds = getFavoriteRows().map(function (row) {
        return row.dataset.townshipId;
    });

    return fetch(favoriteList.dataset.reorderUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            township_ids: townshipIds,
        }),
    }).then(function (response) {
        if (!response.ok) {
            throw new Error("Favorite order was not saved.");
        }
    });
}

function getDropTarget(container, pointerY) {
    const rows = getFavoriteRows().filter(function (row) {
        return !row.classList.contains("is-dragging");
    });

    return rows.find(function (row) {
        const box = row.getBoundingClientRect();
        return pointerY < box.top + box.height / 2;
    });
}

if (favoriteList) {
    let draggedRow = null;

    favoriteList.addEventListener("dragstart", function (event) {
        draggedRow = event.target.closest("[data-township-id]");

        if (!draggedRow) {
            return;
        }

        draggedRow.classList.add("is-dragging");
        event.dataTransfer.effectAllowed = "move";
    });

    favoriteList.addEventListener("dragover", function (event) {
        event.preventDefault();

        if (!draggedRow) {
            return;
        }

        const target = getDropTarget(favoriteList, event.clientY);

        if (target) {
            favoriteList.insertBefore(draggedRow, target);
        } else {
            favoriteList.appendChild(draggedRow);
        }

        updateFavoritePositions();
    });

    favoriteList.addEventListener("dragend", function () {
        if (!draggedRow) {
            return;
        }

        draggedRow.classList.remove("is-dragging");
        draggedRow = null;

        updateFavoritePositions();
        saveFavoriteOrder().catch(function () {
            window.location.reload();
        });
    });
}
