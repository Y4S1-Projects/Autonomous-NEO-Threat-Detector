/**
 * AstroGuard Dashboard Application — What-If Simulator
 * Handles parsing simulation history, fetching world cities, and enabling interactive 
 * click-to-impact simulations.
 */

let map;
let layersControl;
let timeDimension;

// Active Overlay layers
let blastZonesLayer;
let markerLayer;
let affectedCitiesLayer;
let animationLayer;
let minimapControl;

// Datasets
let simulations = [];
let citiesData = [];
let currentSimulation = null; // Currently selected baseline simulation

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    fetchData();
});

function initMap() {
    // 1. Initialize map container
    map = L.map('map', {
        zoomControl: true,
        timeDimension: true,
        timeDimensionOptions: {
            timeInterval: "2026-01-01T00:00:00/2026-01-01T00:00:09",
            period: "PT1S",
            currentTime: new Date("2026-01-01T00:00:00").getTime()
        },
        timeDimensionControl: true,
        timeDimensionControlOptions: {
            autoPlay: true,
            loopButton: true,
            timeSliderDragUpdate: true,
            playerOptions: { transitionTime: 1000, loop: true }
        }
    }).setView([20, 0], 2);

    // 2. Add Base layers
    const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    });

    // Layer switcher
    layersControl = L.control.layers({
        "Carto Dark": darkLayer,
        "Street Map": streetLayer
    }, {}, { position: 'topright' }).addTo(map);

    // 2.5 NASA SEDAC Population Web Map Service (WMS)
    // Providing a raster overlay so users can visually aim for high-density "hot zones"
    const sedacWmsUrl = "https://sedac.ciesin.columbia.edu/geoserver/wms";
    const popDensityLayer = L.tileLayer.wms(sedacWmsUrl, {
        layers: 'gpw-v4:gpw-v4-population-density-rev11_2020',
        format: 'image/png',
        transparent: true,
        opacity: 0.5,
        attribution: 'NASA SEDAC Population Density'
    }).addTo(map); // Default active so users see it immediately

    layersControl.addOverlay(popDensityLayer, "🔥 NASA Global Population Heatmap");

    // MiniMap
    minimapControl = new L.Control.MiniMap(
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'),
        { toggleDisplay: true, position: 'bottomright' }
    ).addTo(map);

    // Layer groups for dynamic data
    blastZonesLayer = L.layerGroup().addTo(map);
    markerLayer = L.layerGroup().addTo(map);
    affectedCitiesLayer = L.layerGroup().addTo(map);
    
    layersControl.addOverlay(blastZonesLayer, "Static Blast Zones");
    layersControl.addOverlay(markerLayer, "Ground Zero Array");
    layersControl.addOverlay(affectedCitiesLayer, "Affected Cities");

    // 3. Register Click Listener for What-If Simulator
    map.on('click', handleMapClick);
}

function fetchData() {
    // Fetch History & Cities concurrently
    Promise.all([
        fetch('simulation_history.json').then(r => r.json()),
        fetch('cities.json').then(r => r.json())
    ])
    .then(([simData, cityData]) => {
        if (Array.isArray(simData) && simData.length > 0) {
            simulations = simData;
            citiesData = cityData;
            populateDropdown();
            // Load the most recent simulation to seed baseline energy
            selectSimulationMode(simData.length - 1);
        }
    })
    .catch(err => {
        console.error("Initialization failed:", err);
        document.getElementById('cors-error').style.display = 'block';
    });
}

function populateDropdown() {
    const dateSelector = document.getElementById('date-selector');
    const asteroidSelector = document.getElementById('asteroid-selector');
    
    dateSelector.innerHTML = '';
    asteroidSelector.innerHTML = '';

    // Group simulations by Date (YYYY-MM-DD string prefix of timestamp)
    const dateGroups = {};
    simulations.forEach((sim, index) => {
        // e.g., "2026-04-15" from "2026-04-15T09:32:00.000Z"
        const dStr = typeof sim.timestamp === 'string' ? sim.timestamp.split('T')[0] : 'Unknown Date';
        if (!dateGroups[dStr]) dateGroups[dStr] = [];
        dateGroups[dStr].push({ sim, originalIndex: index });
    });

    const uniqueDates = Object.keys(dateGroups).sort().reverse(); // Newest first

    if (uniqueDates.length === 0) {
        dateSelector.innerHTML = '<option>No data</option>';
        return;
    }

    // Populate Date Selector
    uniqueDates.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.innerText = `Sim Date: ${d}`;
        dateSelector.appendChild(opt);
    });

    dateSelector.disabled = false;
    asteroidSelector.disabled = false;

    // Handle Date Change -> Populate Asteroids
    const updateAsteroids = () => {
        asteroidSelector.innerHTML = '';
        const selectedDate = dateSelector.value;
        const targets = dateGroups[selectedDate] || [];
        
        targets.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.originalIndex;
            const targetName = t.sim.asteroid_name || 'Hypothetical';
            opt.innerText = `Target: ${targetName} — Yield: ${t.sim.threat_level}`;
            asteroidSelector.appendChild(opt);
        });

        // Auto-select first asteroid for that date
        if (targets.length > 0) {
            selectSimulationMode(targets[0].originalIndex);
        }
    };

    dateSelector.addEventListener('change', updateAsteroids);
    
    asteroidSelector.addEventListener('change', (e) => {
        selectSimulationMode(parseInt(e.target.value));
    });

    // Initialize first date
    updateAsteroids();
}

function selectSimulationMode(index) {
    currentSimulation = simulations[index];
    if (!currentSimulation) return;

    // Update Absolute Energy Metric
    document.getElementById('ui-absolute-threat').innerText = currentSimulation.threat_level + " - YIELD AIRBURST";
    
    // In a pristine mode change, we can either re-render the historical coordinate or just wait for click.
    // Let's re-render the historical coordinate to show something on load.
    simulateImpact(currentSimulation.impact_lat, currentSimulation.impact_lon);
}

// ── HAversine & Population Engine ────────────────────────────────────────────────

function haversineDistance(lat1, lon1, lat2, lon2) {
    const toRad = x => (x * Math.PI) / 180;
    const R = 6371; // km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function calculatePopulation(lat, lon, radius_km) {
    let affected = 0;
    let citiesInRange = [];

    citiesData.forEach(city => {
        const c_lat = parseFloat(city.lat);
        const c_lon = parseFloat(city.lon);
        const c_pop = parseInt(city.population);
        
        const dist = haversineDistance(lat, lon, c_lat, c_lon);
        if (dist <= radius_km) {
            affected += c_pop;
            citiesInRange.push({
                name: city.city,
                country: city.country,
                population: c_pop,
                distance_km: dist.toFixed(1),
                lat: c_lat,
                lon: c_lon
            });
        }
    });

    citiesInRange.sort((a, b) => a.distance_km - b.distance_km);

    return {
        total_affected: affected,
        cities_count: citiesInRange.length,
        cities_in_range: citiesInRange
    };
}

// ── Interactive Logic ────────────────────────────────────────────────────────────

function handleMapClick(e) {
    if (!currentSimulation) return;
    simulateImpact(e.latlng.lat, e.latlng.lng);
}

function simulateImpact(lat, lon) {
    // 1. Calculate population for clicking location
    const popData = calculatePopulation(lat, lon, currentSimulation.radius_km);
    
    // 2. Assess Relative Human Impact
    let relativeImpact = "NEGLIGIBLE";
    let relColor = "#4CAF50"; // Green
    
    if (popData.total_affected > 0) { relativeImpact = "MINOR"; relColor = "#FFC107"; } // Amber
    if (popData.total_affected > 100000) { relativeImpact = "SEVERE"; relColor = "#FF5722"; } // Orange
    if (popData.total_affected > 1000000) { relativeImpact = "CATASTROPHIC"; relColor = "#FF1744"; } // Red

    // Update Metric 2 HUD
    const relHtml = document.getElementById('ui-relative-impact');
    relHtml.innerText = relativeImpact;
    relHtml.style.color = relColor;
    
    // Update Document styling slightly to match severity
    document.querySelector('.border-relative').style.borderLeftColor = relColor;

    // 3. Clear Canvas
    blastZonesLayer.clearLayers();
    markerLayer.clearLayers();
    affectedCitiesLayer.clearLayers();
    if (animationLayer) {
        map.removeLayer(animationLayer);
        layersControl.removeLayer(animationLayer);
    }

    // 4. Draw Radial Blast Zones
    const radiusMeters = currentSimulation.radius_km * 1000.0;
    
    L.circle([lat, lon], {
        radius: radiusMeters,
        color: currentSimulation.style.stroke_color,
        weight: 2,
        fillColor: currentSimulation.style.fill_color,
        fillOpacity: 0.1,
        dashArray: "10 6"
    }).addTo(blastZonesLayer);

    L.circle([lat, lon], {
        radius: radiusMeters * 0.7,
        color: currentSimulation.style.stroke_color,
        weight: 2,
        fillColor: currentSimulation.style.fill_color,
        fillOpacity: 0.3
    }).addTo(blastZonesLayer);

    L.circle([lat, lon], {
        radius: radiusMeters * 0.3,
        color: currentSimulation.style.stroke_color,
        weight: 3,
        fillColor: currentSimulation.style.fill_color,
        fillOpacity: 0.7
    }).addTo(blastZonesLayer);

    // 5. Build Timed GeoJSON Animation
    const geojsonData = buildAnimationGeoJSON(lat, lon, currentSimulation);
    const baseGeoJsonLayer = L.geoJson(geojsonData, {
        style: feature => feature.properties.style
    });

    animationLayer = L.timeDimension.layer.geoJson(baseGeoJsonLayer, {
        updateTimeDimension: true,
        duration: 'PT1S',
        addlastPoint: true
    }).addTo(map);
    layersControl.addOverlay(animationLayer, "Temporal Blast Wave");

    // 6. Draw Popup capabilities
    const popupHtml = `
        <div style="font-family:'Segoe UI',Roboto,Arial,sans-serif;background:#1a1a2e;color:#ECEFF1;
                    border-radius:10px;padding:16px;min-width:320px;">
            <div style="text-align:center;margin-bottom:12px;">
                <h3 style="margin:4px 0;color:${relColor};font-size:18px;letter-spacing:1px;">
                    IMPACT: ${relativeImpact}
                </h3>
            </div>
            <hr style="border:none;border-top:1px solid #37474F;margin:8px 0;">
            <table style="width:100%;font-size:13px;">
                <tr><td style="color:#90A4AE;">Absolute Yield</td><td style="font-weight:bold;">${currentSimulation.threat_level}</td></tr>
                <tr><td style="color:#90A4AE;">Blast Radius</td><td style="font-weight:bold;">${currentSimulation.radius_km.toLocaleString()} km</td></tr>
                <tr><td style="color:#90A4AE;">Affected Pop.</td><td style="font-weight:bold;color:${relColor};">${popData.total_affected.toLocaleString()}</td></tr>
            </table>
        </div>`;

    L.circleMarker([lat, lon], {
        radius: 8, color: '#fff', fillColor: currentSimulation.style.fill_color, fillOpacity: 1, weight: 2
    }).bindPopup(popupHtml).addTo(markerLayer).openPopup();

    // 7. Draw Affected Cities
    popData.cities_in_range.slice(0, 15).forEach(c => {
        L.circleMarker([c.lat, c.lon], {
            radius: Math.max(3, Math.min(12, c.population / 1000000)),
            color: '#FF8A80',
            fillColor: '#FF5252',
            fillOpacity: 0.8,
        }).bindTooltip(`${c.name}: ${c.population.toLocaleString()} pax`).addTo(affectedCitiesLayer);
    });

    // 8. Update Side HUD
    const hud = document.getElementById('ui-hud');
    if (popData.total_affected > 0) {
        document.getElementById('hud-total').innerText = popData.total_affected.toLocaleString();
        document.getElementById('hud-cities-count').innerText = `${popData.cities_count} cities within blast radius`;
        
        const citiesList = document.getElementById('hud-cities-list');
        citiesList.innerHTML = '';
        popData.cities_in_range.slice(0, 3).forEach(c => {
            citiesList.innerHTML += `<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:11px;">
                                        <span style="color:#B0BEC5;">${c.name}</span>
                                        <span style="color:#FF8A80;">${c.distance_km} km</span>
                                     </div>`;
        });
        hud.style.display = 'block';
    } else {
        hud.style.display = 'none';
    }

    // Optional: Smoothly fly to click if it was far away, otherwise let user explore
    // map.flyTo([lat, lon], map.getZoom(), {duration: 0.5});
}

function buildAnimationGeoJSON(lat, lon, sim) {
    const features = [];
    const numFrames = 10;
    const baseTime = new Date("2026-01-01T00:00:00Z").getTime();

    for (let i = 0; i < numFrames; i++) {
        const fraction = 0.05 + (0.95 * (i / Math.max(numFrames - 1, 1)));
        const currentRadius = sim.radius_km * fraction;

        const numPoints = 64;
        const circleCoords = [];
        for (let j = 0; j <= numPoints; j++) {
            const angle = 2 * Math.PI * j / numPoints;
            const dlat = (currentRadius / 111.32) * Math.cos(angle);
            const dlon = (currentRadius / (111.32 * Math.cos(lat * Math.PI / 180))) * Math.sin(angle);
            circleCoords.push([lon + dlon, lat + dlat]);
        }

        features.push({
            type: "Feature",
            geometry: { type: "Polygon", coordinates: [circleCoords] },
            properties: {
                time: new Date(baseTime + (i * 1000)).toISOString(),
                style: {
                    color: sim.style.stroke_color,
                    fillColor: sim.style.fill_color,
                    fillOpacity: Math.max(0.05, sim.style.fill_opacity * (1 - fraction * 0.7)),
                    weight: 2
                }
            }
        });
    }
    return { type: "FeatureCollection", features: features };
}
