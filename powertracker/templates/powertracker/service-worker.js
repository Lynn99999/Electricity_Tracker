{% load static %}

const CACHE_NAME = "electricity-tracker-offline-v4";
const OFFLINE_URL = "{% url 'offline' %}?fallback=1";
const PRECACHE_URLS = [
    OFFLINE_URL,
    "{% static 'bootstrap/css/bootstrap.min.css' %}",
    "{% static 'bootstrap/js/bootstrap.bundle.min.js' %}",
    "{% static 'css/offline.css' %}",
    "{% static 'js/offline-cache.js' %}",
    "{% static 'js/register-service-worker.js' %}",
    "{% static 'js/offline.js' %}",
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
                return cache.addAll(PRECACHE_URLS);
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys()
            .then(function (cacheNames) {
                return Promise.all(
                    cacheNames.map(function (cacheName) {
                        if (cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }

                        return null;
                    })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});

self.addEventListener("fetch", function (event) {
    const request = event.request;

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request).catch(function () {
                return caches.match(OFFLINE_URL);
            })
        );
        return;
    }

    event.respondWith(
        caches.match(request).then(function (cachedResponse) {
            return cachedResponse || fetch(request);
        })
    );
});

self.addEventListener("push", function (event) {
    let payload = {
        title: "Electricity Tracker",
        body: "You have a new electricity schedule reminder.",
        url: "/",
        tag: "electricity-tracker-reminder",
    };

    if (event.data) {
        payload = Object.assign(payload, event.data.json());
    }

    event.waitUntil(
        self.registration.showNotification(payload.title, {
            body: payload.body,
            tag: payload.tag,
            data: {
                url: payload.url,
            },
        })
    );
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();

    const targetUrl = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : "/";

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true,
        }).then(function (clientList) {
            for (const client of clientList) {
                if ("focus" in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }

            return null;
        })
    );
});
