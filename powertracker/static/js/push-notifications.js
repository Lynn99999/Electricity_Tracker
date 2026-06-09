(function () {
    const configElement = document.querySelector("[data-push-public-key-url]");

    if (!configElement || !("serviceWorker" in navigator) || !("PushManager" in window)) {
        return;
    }

    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (const cookie of cookies) {
            const trimmedCookie = cookie.trim();

            if (trimmedCookie.startsWith(name + "=")) {
                return decodeURIComponent(trimmedCookie.slice(name.length + 1));
            }
        }

        return "";
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = "=".repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, "+")
            .replace(/_/g, "/");
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let index = 0; index < rawData.length; index += 1) {
            outputArray[index] = rawData.charCodeAt(index);
        }

        return outputArray;
    }

    function saveSubscription(subscription) {
        return fetch(configElement.dataset.pushSubscribeUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify(subscription),
        });
    }

    function subscribe(publicKey) {
        if (!publicKey || Notification.permission === "denied") {
            return Promise.resolve();
        }

        return navigator.serviceWorker.ready
            .then(function (registration) {
                return registration.pushManager.getSubscription()
                    .then(function (existingSubscription) {
                        if (existingSubscription) {
                            return existingSubscription;
                        }

                        return registration.pushManager.subscribe({
                            userVisibleOnly: true,
                            applicationServerKey: urlBase64ToUint8Array(publicKey),
                        });
                    });
            })
            .then(function (subscription) {
                if (subscription) {
                    return saveSubscription(subscription);
                }

                return null;
            });
    }

    window.addEventListener("load", function () {
        if (Notification.permission === "default") {
            return Notification.requestPermission()
                .then(function (permission) {
                    if (permission !== "granted") {
                        return null;
                    }

                    return fetch(configElement.dataset.pushPublicKeyUrl)
                        .then(function (response) {
                            return response.json();
                        })
                        .then(function (data) {
                            return subscribe(data.public_key);
                        });
                })
                .catch(function (error) {
                    console.error("Push notification setup failed:", error);
                });
        }

        if (Notification.permission === "granted") {
            fetch(configElement.dataset.pushPublicKeyUrl)
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    return subscribe(data.public_key);
                })
                .catch(function (error) {
                    console.error("Push notification setup failed:", error);
                });
        }

        return null;
    });
})();
