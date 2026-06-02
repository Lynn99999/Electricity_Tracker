function getStatusColor(status) {
    if (status === "ON") {
        return "#4e598c"; // soft green
    }

    if (status === "OFF") {
        return "#ffffff"; // pale cool gray
    }

    return "#F2C94C"; // muted amber
}

function getTownshipLinks() {
    const townshipLinksElement = document.getElementById("township-links");

    if (!townshipLinksElement) {
        return [];
    }

    return JSON.parse(townshipLinksElement.textContent);
}

function getTownshipShapes(townshipName) {
    const shapes = [];
    const normalShape = document.getElementById(townshipName);
    const splitShapes = document.querySelectorAll(
        '[data-name="' + townshipName + '"]'
    );

    if (normalShape) {
        shapes.push(normalShape);
    }

    splitShapes.forEach(function (shape) {
        shapes.push(shape);
    });

    return shapes;
}

function makeTownshipClickable(township) {
    const shapes = getTownshipShapes(township.name);

    shapes.forEach(function (shape) {
        shape.classList.add("is-clickable");
        shape.style.fill = getStatusColor(township.status);
        shape.addEventListener("click", function (event) {
            if (window.mapInteraction && window.mapInteraction.suppressNextClick) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }

            window.location.href = township.url;
        });

        shape.addEventListener("mouseenter", function () {
            shapes.forEach(function (part) {
                part.classList.add("is-hovered");
            });
        });

        shape.addEventListener("mouseleave", function () {
            shapes.forEach(function (part) {
                part.classList.remove("is-hovered");
            });
        });
    });
}

function initClickableMap() {
    const townshipLinks = getTownshipLinks();

    townshipLinks.forEach(function (township) {
        makeTownshipClickable(township);
    });
}

initClickableMap();