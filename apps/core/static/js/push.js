/*
 * Til og fravalg af push notifikationer på profilsiden.
 * Registrerer service workeren, henter VAPID nøglen og holder
 * abonnementet synkroniseret med serveren.
 */
(function () {
  "use strict";

  var section = document.getElementById("push-section");
  if (!section) return;

  var statusEl = document.getElementById("push-status");
  var enableBtn = document.getElementById("push-enable");
  var disableBtn = document.getElementById("push-disable");

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(body),
    });
  }

  function setState(subscribed, message) {
    enableBtn.hidden = subscribed;
    disableBtn.hidden = !subscribed;
    statusEl.textContent = message;
  }

  function urlBase64ToUint8Array(base64String) {
    var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    var raw = atob(base64);
    var output = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) output[i] = raw.charCodeAt(i);
    return output;
  }

  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    setState(false, "Din browser understøtter ikke push notifikationer. På iPhone skal PåVejen først føjes til hjemmeskærmen.");
    enableBtn.hidden = true;
    return;
  }

  navigator.serviceWorker.register("/sw.js").then(function (registration) {
    return registration.pushManager.getSubscription();
  }).then(function (subscription) {
    if (subscription) {
      setState(true, "Push notifikationer er slået til på denne enhed.");
    } else {
      setState(false, "Få besked med det samme ved nye matches, forespørgsler og beskeder.");
    }
  });

  enableBtn.addEventListener("click", function () {
    statusEl.textContent = "Slår til…";
    Notification.requestPermission().then(function (permission) {
      if (permission !== "granted") {
        setState(false, "Du har blokeret notifikationer i browseren.");
        return;
      }
      Promise.all([
        navigator.serviceWorker.ready,
        fetch("/notifikationer/vapid/").then(function (r) { return r.json(); }),
      ]).then(function (results) {
        var registration = results[0];
        var key = results[1].publicKey;
        return registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(key),
        });
      }).then(function (subscription) {
        return post("/notifikationer/subscribe/", subscription.toJSON());
      }).then(function () {
        setState(true, "Push notifikationer er slået til på denne enhed.");
      }).catch(function () {
        setState(false, "Noget gik galt. Prøv igen.");
      });
    });
  });

  disableBtn.addEventListener("click", function () {
    navigator.serviceWorker.ready.then(function (registration) {
      return registration.pushManager.getSubscription();
    }).then(function (subscription) {
      if (!subscription) return null;
      return post("/notifikationer/unsubscribe/", { endpoint: subscription.endpoint })
        .then(function () { return subscription.unsubscribe(); });
    }).then(function () {
      setState(false, "Push notifikationer er slået fra på denne enhed.");
    });
  });
})();
