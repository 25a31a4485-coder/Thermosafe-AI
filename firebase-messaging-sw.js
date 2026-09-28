// firebase-messaging-sw.js
// SIH26162 ThermoSafe AI - Firebase Cloud Messaging Service Worker

try {
  importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

  const defaultConfig = {
    apiKey: "AIzaSyDemoPlaceholderOnly",
    projectId: "thermosafe-ai",
    messagingSenderId: "1234567890"
  };

  if (typeof firebase !== 'undefined') {
    firebase.initializeApp(defaultConfig);
    const messaging = firebase.messaging();

    messaging.onBackgroundMessage((payload) => {
      console.log('[firebase-messaging-sw.js] Received background message:', payload);
      const notificationTitle = payload.notification?.title || payload.data?.title || 'ThermoSafe AI Thermal Alert';
      const notificationOptions = {
        body: payload.notification?.body || payload.data?.body || 'Thermal anomaly detected.',
        icon: '/vite.svg',
        badge: '/vite.svg',
        data: payload.data || {},
        tag: payload.data?.event_id || 'thermosafe-alert',
        renotify: true,
        requireInteraction: payload.data?.severity === 'Critical' || payload.data?.severity === 'High',
        actions: [
          { action: 'view', title: 'View on Map' },
          { action: 'ack', title: 'Acknowledge' }
        ]
      };

      self.registration.showNotification(notificationTitle, notificationOptions);
    });
  }
} catch (e) {
  console.log('[firebase-messaging-sw.js] Firebase scripts could not load or offline, falling back to native push listener.');
}

// Fallback native push event listener
self.addEventListener('push', (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (err) {
      data = { title: 'ThermoSafe AI Alert', body: event.data.text() };
    }
  }

  const title = data.title || data.notification?.title || 'ThermoSafe AI Thermal Alert';
  const options = {
    body: data.body || data.notification?.body || 'Thermal anomaly detected.',
    icon: '/vite.svg',
    badge: '/vite.svg',
    data: data.data || data,
    tag: data.event_id || 'thermosafe-alert',
    renotify: true,
    requireInteraction: true,
    actions: [
      { action: 'view', title: 'View on Map' },
      { action: 'ack', title: 'Acknowledge' }
    ]
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// Notification click event handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  let targetUrl = '/';
  if (data.event_id) {
    targetUrl = `/?event=${encodeURIComponent(data.event_id)}#map`;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url && 'focus' in client) {
          if (client.navigate) {
            client.navigate(targetUrl);
          }
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
