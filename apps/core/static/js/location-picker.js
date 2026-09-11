/*
 * Kortvælger til PåVejens formularer.
 *
 * Finder automatisk alle skjulte koordinatpar (<felt>_lat og <felt>_lng)
 * med et tilhørende tekstfelt (<felt>_name) og udstyrer dem med:
 * - adressesøgning via DAWA, Danmarks Adressers Web API, gratis og uden nøgle
 * - et Leaflet kort med en flytbar nål, der udfylder koordinaterne
 *
 * Koordinatfelterne forbliver skjulte for brugeren. Hvis JavaScript
 * fejler, falder serveren tilbage til at geokode stednavnet.
 */
(function () {
  "use strict";

  var DAWA = "https://api.dataforsyningen.dk";
  var DENMARK_CENTER = [56.0, 10.5];
  var DENMARK_ZOOM = 6;
  var PICKED_ZOOM = 14;

  function debounce(fn, ms) {
    var timer = null;
    return function () {
      var args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(null, args); }, ms);
    };
  }

  function fetchJson(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : []; })
      .catch(function () { return []; });
  }

  function searchSuggestions(query) {
    var cities = fetchJson(DAWA + "/postnumre/autocomplete?q=" + encodeURIComponent(query))
      .then(function (rows) {
        return rows.slice(0, 3).map(function (row) {
          return {
            label: row.postnummer.nr + " " + row.postnummer.navn,
            lat: row.postnummer.visueltcenter[1],
            lng: row.postnummer.visueltcenter[0],
          };
        });
      });
    var addresses = fetchJson(DAWA + "/adgangsadresser/autocomplete?q=" + encodeURIComponent(query) + "&per_side=5")
      .then(function (rows) {
        return rows.map(function (row) {
          return {
            label: row.tekst,
            lat: row.adgangsadresse.y,
            lng: row.adgangsadresse.x,
          };
        });
      });
    return Promise.all([cities, addresses]).then(function (parts) {
      return parts[0].concat(parts[1]).slice(0, 8);
    });
  }

  function reverseLookup(lat, lng) {
    return fetchJson(DAWA + "/adgangsadresser/reverse?x=" + lng + "&y=" + lat + "&struktur=mini")
      .then(function (data) { return data && data.betegnelse ? data.betegnelse : null; });
  }

  function initPicker(nameInput, latInput, lngInput) {
    var wrapper = document.createElement("div");
    wrapper.className = "location-picker";
    nameInput.parentNode.insertBefore(wrapper, nameInput.nextSibling);

    var dropdown = document.createElement("ul");
    dropdown.className = "location-suggestions";
    dropdown.hidden = true;
    wrapper.appendChild(dropdown);

    var mapDiv = document.createElement("div");
    mapDiv.className = "location-map";
    wrapper.appendChild(mapDiv);

    var map = L.map(mapDiv, { scrollWheelZoom: false });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a>",
    }).addTo(map);

    var marker = null;

    function setPoint(lat, lng, updateAddress) {
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
      if (marker === null) {
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        marker.on("dragend", function () {
          var pos = marker.getLatLng();
          setPoint(pos.lat, pos.lng, true);
        });
      } else {
        marker.setLatLng([lat, lng]);
      }
      if (updateAddress) {
        reverseLookup(lat, lng).then(function (label) {
          if (label) nameInput.value = label;
        });
      }
    }

    if (latInput.value && lngInput.value) {
      var lat = parseFloat(latInput.value);
      var lng = parseFloat(lngInput.value);
      map.setView([lat, lng], PICKED_ZOOM);
      setPoint(lat, lng, false);
    } else {
      map.setView(DENMARK_CENTER, DENMARK_ZOOM);
    }

    map.on("click", function (event) {
      setPoint(event.latlng.lat, event.latlng.lng, true);
    });

    function hideDropdown() {
      dropdown.hidden = true;
      dropdown.innerHTML = "";
    }

    function showSuggestions(items) {
      dropdown.innerHTML = "";
      if (items.length === 0) { hideDropdown(); return; }
      items.forEach(function (item) {
        var li = document.createElement("li");
        li.textContent = item.label;
        li.addEventListener("mousedown", function (event) {
          event.preventDefault();
          nameInput.value = item.label;
          setPoint(item.lat, item.lng, false);
          map.setView([item.lat, item.lng], PICKED_ZOOM);
          hideDropdown();
        });
        dropdown.appendChild(li);
      });
      dropdown.hidden = false;
    }

    var onType = debounce(function () {
      var query = nameInput.value.trim();
      // Koordinaterne nulstilles, når adressen ændres, så serveren
      // geokoder på ny, hvis brugeren ikke vælger et forslag.
      latInput.value = "";
      lngInput.value = "";
      if (query.length < 2) { hideDropdown(); return; }
      searchSuggestions(query).then(showSuggestions);
    }, 250);

    nameInput.setAttribute("autocomplete", "off");
    nameInput.addEventListener("input", onType);
    nameInput.addEventListener("blur", function () {
      setTimeout(hideDropdown, 200);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (typeof L === "undefined") return;
    var latInputs = document.querySelectorAll("input[type=hidden][name$='_lat']");
    latInputs.forEach(function (latInput) {
      var prefix = latInput.name.slice(0, -4);
      var lngInput = document.querySelector("input[type=hidden][name='" + prefix + "_lng']");
      var nameInput = document.querySelector("input[name='" + prefix + "_name']");
      if (lngInput && nameInput) {
        initPicker(nameInput, latInput, lngInput);
      }
    });
  });
})();
