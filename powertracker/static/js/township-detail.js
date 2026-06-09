function getStatusColor(status) {
    if (status === "ON") {
        return "#9bd1e5";
    }

    if (status === "OFF") {
        return "#ffffff";
    }

    return "#ffcf56";
}

function normalizeName(value) {
    return value
        .toLowerCase()
        .replace(" township", "")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function addUniqueNode(nodes, node) {
    if (node && !nodes.includes(node)) {
        nodes.push(node);
    }
}

function getDrawableNodes(node) {
    if (node.matches("path, polygon, polyline, rect")) {
        return [node];
    }

    return Array.from(node.querySelectorAll("path, polygon, polyline, rect"));
}

function getCandidateNodes(svg) {
    return Array.from(svg.querySelectorAll("[id], [data-name]"));
}

function nodeMatchesTownship(node, townshipName) {
    const targetName = normalizeName(townshipName);
    const idName = normalizeName(node.id || "");
    const dataName = normalizeName(node.dataset.name || "");

    return idName === targetName || dataName === targetName;
}

function nodeContainsTownship(node, townshipName) {
    const targetName = normalizeName(townshipName);
    const idName = normalizeName(node.id || "");
    const dataName = normalizeName(node.dataset.name || "");

    return idName.includes(targetName) || dataName.includes(targetName);
}

function getTownshipShapes(svg, townshipName) {
    const matchedNodes = [];
    const fallbackNodes = [];

    getCandidateNodes(svg).forEach(function (node) {
        if (nodeMatchesTownship(node, townshipName)) {
            addUniqueNode(matchedNodes, node);
            return;
        }

        if (nodeContainsTownship(node, townshipName)) {
            addUniqueNode(fallbackNodes, node);
        }
    });

    const nodes = matchedNodes.length > 0 ? matchedNodes : fallbackNodes;
    const shapes = [];

    nodes.forEach(function (node) {
        getDrawableNodes(node).forEach(function (shape) {
            addUniqueNode(shapes, shape);
        });
    });

    return shapes;
}

function getCombinedBox(shapes) {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    shapes.forEach(function (shape) {
        const box = shape.getBBox();

        minX = Math.min(minX, box.x);
        minY = Math.min(minY, box.y);
        maxX = Math.max(maxX, box.x + box.width);
        maxY = Math.max(maxY, box.y + box.height);
    });

    if (!isFinite(minX)) {
        return null;
    }

    return {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY,
    };
}

function getShapeArea(shape) {
    const box = shape.getBBox();

    return box.width * box.height;
}

function filterMainShapes(shapes) {
    if (shapes.length <= 1) {
        return shapes;
    }

    const largestArea = Math.max.apply(null, shapes.map(getShapeArea));

    return shapes.filter(function (shape) {
        return getShapeArea(shape) >= largestArea * 0.2;
    });
}

function getTownshipLabel(svg, townshipName) {
    const targetName = normalizeName(townshipName);
    const labels = Array.from(svg.querySelectorAll("text"));

    return labels.find(function (label) {
        return normalizeName(label.textContent || "") === targetName;
    });
}

function getLabelCenter(label) {
    const box = label.getBBox();

    return {
        x: box.x + (box.width / 2),
        y: box.y + (box.height / 2),
    };
}

function getPaddedViewBox(map, center, box) {
    const mapRatio = map.clientWidth / map.clientHeight;
    const minimumHeight = 230;
    const boxWidth = box ? box.width : minimumHeight;
    const boxHeight = box ? box.height : minimumHeight;
    const paddedWidth = Math.max(boxWidth * 1.9, minimumHeight * mapRatio);
    const paddedHeight = Math.max(boxHeight * 1.9, minimumHeight);
    let viewWidth = Math.max(paddedWidth, paddedHeight * mapRatio);
    let viewHeight = viewWidth / mapRatio;

    return {
        x: center.x - (viewWidth / 2),
        y: center.y - (viewHeight / 2),
        width: viewWidth,
        height: viewHeight,
    };
}

function focusMiniMapOnTownship() {
    const map = document.querySelector("[data-township-map]");
    const svg = map ? map.querySelector("svg") : null;

    if (!svg || !window.townshipDetail) {
        return;
    }

    const shapes = filterMainShapes(
        getTownshipShapes(svg, window.townshipDetail.name)
    );
    const label = getTownshipLabel(svg, window.townshipDetail.name);
    const color = getStatusColor(window.townshipDetail.status);

    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

    svg.querySelectorAll("path, polygon, polyline, rect, text").forEach(function (node) {
        node.style.opacity = "0";
        node.style.pointerEvents = "none";
    });

    if (shapes.length === 0 && !label) {
        svg.querySelectorAll("path, polygon, polyline, rect").forEach(function (node) {
            node.style.opacity = "0.2";
        });
        return;
    }

    shapes.forEach(function (shape) {
        shape.style.opacity = "1";
        shape.style.pointerEvents = "auto";
        shape.style.fill = color;
        shape.style.stroke = "#212529";
        shape.style.strokeWidth = "2";
    });

    const box = getCombinedBox(shapes);
    const center = label ? getLabelCenter(label) : {
        x: box.x + (box.width / 2),
        y: box.y + (box.height / 2),
    };
    const viewBox = getPaddedViewBox(map, center, box);

    svg.setAttribute(
        "viewBox",
        [
            viewBox.x,
            viewBox.y,
            viewBox.width,
            viewBox.height,
        ].join(" ")
    );
}

function getStatusBadgeClass(status) {
    if (status === "ON") {
        return "text-bg-info";
    }

    if (status === "OFF") {
        return "text-bg-secondary";
    }

    return "text-bg-warning";
}

function updateStatusBadge(type, status) {
    const badge = document.querySelector(`[data-status-badge="${type}"]`);

    if (!badge) {
        return;
    }

    badge.textContent = status;
    badge.classList.remove("text-bg-info", "text-bg-secondary", "text-bg-warning");
    badge.classList.add(getStatusBadgeClass(status));
}

function updateReportButtons(reportedStatus) {
    document.querySelectorAll("[data-report-button]").forEach(function (button) {
        const status = button.dataset.reportButton;

        button.classList.remove(
            "btn-success",
            "btn-outline-success",
            "btn-danger",
            "btn-outline-danger"
        );

        if (status === "ON") {
            button.classList.add(
                reportedStatus === "ON" ? "btn-success" : "btn-outline-success"
            );
        }

        if (status === "OFF") {
            button.classList.add(
                reportedStatus === "OFF" ? "btn-danger" : "btn-outline-danger"
            );
        }
    });
}

function updateTownshipDetail(data) {
    if (!window.townshipDetail) {
        return;
    }

    window.townshipDetail.status = data.current_status;

    updateStatusBadge("expected", data.expected_status);
    updateStatusBadge("current", data.current_status);
    updateReportButtons(data.reported_status);
    focusMiniMapOnTownship();
}

function refreshTownshipDetailStatus() {
    const root = document.querySelector("[data-township-status-url]");

    if (!root) {
        return;
    }

    fetch(root.dataset.townshipStatusUrl, {
        headers: {
            "Accept": "application/json",
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Could not load township status.");
            }

            return response.json();
        })
        .then(updateTownshipDetail)
        .catch(function (error) {
            console.error(error);
        });
}

focusMiniMapOnTownship();

if (document.querySelector("[data-township-status-url]")) {
    setInterval(refreshTownshipDetailStatus, 30000);
}
