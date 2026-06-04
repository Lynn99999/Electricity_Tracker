function getStatusColor(status) {
    if (status === "ON") {
        return "#9bd1e5"; 
    }

    if (status === "OFF") {
        return "#ffffff"; 
    }

    return "#ffcf56"; 
}

function getScheduleStatusForTownship(township, activeGroup) {
    if (activeGroup === "All") {
        return "ON";
    }

    if (township.group === activeGroup) {
        return "ON";
    }

    return "OFF";
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

function setTownshipColor(township, status) {
    const shapes = getTownshipShapes(township.name);

    shapes.forEach(function (shape) {
        shape.style.fill = getStatusColor(status);
    });
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

function setCurrentStatusColors(townshipLinks) {
    townshipLinks.forEach(function (township) {
        setTownshipColor(township, township.status);
    });
}

function setSchedulePreviewColors(townshipLinks, activeGroup) {
    townshipLinks.forEach(function (township) {
        const status = getScheduleStatusForTownship(township, activeGroup);

        setTownshipColor(township, status);
    });
}

function initClickableMap() {
    const townshipLinks = getTownshipLinks();

    townshipLinks.forEach(function (township) {
        makeTownshipClickable(township);
    });

    window.electricityMap = {
        townships: townshipLinks,
        setCurrentStatusColors: function () {
            setCurrentStatusColors(townshipLinks);
        },
        setSchedulePreviewColors: function (activeGroup) {
            setSchedulePreviewColors(townshipLinks, activeGroup);
        },
    };
}

initClickableMap();
