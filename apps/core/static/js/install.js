/*
 * Installér appen banner. Vises kun, når browseren tilbyder
 * installation (beforeinstallprompt, Android og desktop Chrome),
 * og huskes væk, hvis brugeren afviser.
 */
(function () {
  "use strict";

  var banner = document.getElementById("install-banner");
  if (!banner) return;

  var installBtn = document.getElementById("install-app");
  var dismissBtn = document.getElementById("install-dismiss");
  var deferredPrompt = null;

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
  }

  function dismissed() {
    try { return localStorage.getItem("paavejen-install-dismissed") === "1"; }
    catch (error) { return false; }
  }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    if (isStandalone() || dismissed()) return;
    deferredPrompt = event;
    banner.hidden = false;
  });

  installBtn.addEventListener("click", function () {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function () {
      deferredPrompt = null;
      banner.hidden = true;
    });
  });

  dismissBtn.addEventListener("click", function () {
    banner.hidden = true;
    try { localStorage.setItem("paavejen-install-dismissed", "1"); }
    catch (error) { /* privat browsing */ }
  });

  window.addEventListener("appinstalled", function () {
    banner.hidden = true;
  });

  // Registrér service workeren overalt, så installation og offline
  // virker, selv om brugeren aldrig besøger profilsiden.
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js");
  }
})();
