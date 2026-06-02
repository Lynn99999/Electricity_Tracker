const viewport = document.querySelector("[data-map-viewport]");
const canvas = document.querySelector("[data-map-canvas]");

const zoomInButton = document.querySelector('[data-map-zoom="in"]');
const zoomOutButton = document.querySelector('[data-map-zoom="out"]');
const zoomResetButton = document.querySelector('[data-map-zoom="reset"]');

window.mapInteraction = {
    suppressNextClick: false,
};

let pointerStartX = 0;
let pointerStartY = 0;
let hasDragged = false;
const dragThreshold = 6;

let mapScale = 2.5;
let mapX = 0;
let mapY = -250;

let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;



function clampMapPosition() {
    const viewportRect = viewport.getBoundingClientRect();

    const scaledWidth = viewportRect.width * mapScale;
    const scaledHeight = viewportRect.height * mapScale;

    const maxX = (scaledWidth - viewportRect.width) / 2;
    const maxY = (scaledHeight - viewportRect.height) / 2;

    if (mapX > maxX) {
        mapX = maxX;
    }

    if (mapX < -maxX) {
        mapX = -maxX;
    }

    if (mapY > maxY) {
        mapY = maxY;
    }

    if (mapY < -maxY) {
        mapY = -maxY;
    }
}

function updateMapTransform() {
    clampMapPosition();

    canvas.style.transform =
        "translate(" + mapX + "px, " + mapY + "px) scale(" + mapScale + ")";
}

function zoomMap(amount) {
    mapScale = mapScale + amount;

    if (mapScale < 1) {
        mapScale = 1;
        mapX = 0;
        mapY = 0;
    }

    if (mapScale > 8) {
        mapScale = 8;
    }

    updateMapTransform();
}

function resetMapZoom() {
    mapScale = 2.5;
    mapX = 0;
    mapY = -250;

    updateMapTransform();
}

function startDragging(event) {
    if (mapScale <= 1) {
        return;
    }

    event.preventDefault();

    isDragging = true;
    hasDragged = false;

    viewport.classList.add("is-dragging");

    pointerStartX = event.clientX;
    pointerStartY = event.clientY;

    dragStartX = event.clientX - mapX;
    dragStartY = event.clientY - mapY;
}

function dragMap(event) {
    if (!isDragging) {
        return;
    }

    const movedX = event.clientX - pointerStartX;
    const movedY = event.clientY - pointerStartY;
    const movedDistance = Math.sqrt((movedX * movedX) + (movedY * movedY));

    if (movedDistance > dragThreshold) {
        hasDragged = true;
        window.mapInteraction.suppressNextClick = true;
    }

    mapX = event.clientX - dragStartX;
    mapY = event.clientY - dragStartY;

    updateMapTransform();
}

function stopDragging() {
    if (hasDragged) {
        setTimeout(function () {
            window.mapInteraction.suppressNextClick = false;
        }, 200);
    }

    isDragging = false;
    viewport.classList.remove("is-dragging");
}

function initMapZoom() {
    if (!viewport || !canvas) {
        return;
    }

    zoomInButton.addEventListener("click", function () {
        zoomMap(0.25);
    });

    zoomOutButton.addEventListener("click", function () {
        zoomMap(-0.25);
    });

    zoomResetButton.addEventListener("click", function () {
        resetMapZoom();
    });

    viewport.addEventListener("wheel", function (event) {
        event.preventDefault();

        if (event.deltaY < 0) {
            zoomMap(0.1);
        } else {
            zoomMap(-0.1);
        }
    });

    viewport.addEventListener("mousedown", function (event) {
        startDragging(event);
    });

    window.addEventListener("mousemove", function (event) {
        dragMap(event);
    });

    window.addEventListener("mouseup", function () {
        stopDragging();
    });
    updateMapTransform();
}

initMapZoom();