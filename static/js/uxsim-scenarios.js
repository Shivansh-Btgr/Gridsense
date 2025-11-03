// UXsim Scenarios JavaScript

let currentMode = 'preset';
let selectedPreset = null;
let customBounds = null;
let map = null;
let drawnItems = null;
let presetsData = {};

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    loadPresets();
    initializeMap();
});

// Load preset locations
async function loadPresets() {
    try {
        const response = await fetch('/api/uxsim/presets');
        const data = await response.json();
        
        if (data.presets) {
            presetsData = data.presets;
            displayPresets(data.presets);
        }
    } catch (error) {
        console.error('Error loading presets:', error);
        showError('Failed to load preset locations');
    }
}

// Display preset cards
function displayPresets(presets) {
    const grid = document.getElementById('presetsGrid');
    grid.innerHTML = '';
    
    const icons = {
        'Japan': '🗾',
        'India': '🇮🇳',
        'United Kingdom': '🇬🇧',
        'USA': '🇺🇸'
    };
    
    for (const [key, preset] of Object.entries(presets)) {
        const card = document.createElement('div');
        card.className = 'preset-card';
        card.onclick = () => selectPreset(key);
        
        card.innerHTML = `
            <div class="preset-header">
                <span class="preset-icon">${icons[preset.country] || '🌍'}</span>
                <h3>${preset.name}</h3>
            </div>
            <div class="preset-meta">
                <span><i class="fas fa-map"></i> ${preset.area_km2} km²</span>
                <span><i class="fas fa-globe"></i> ${preset.country}</span>
            </div>
            <p>${preset.description}</p>
        `;
        
        grid.appendChild(card);
    }
}

// Select preset location
function selectPreset(key) {
    selectedPreset = key;
    customBounds = null;
    
    // Update UI
    document.querySelectorAll('.preset-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
}

// Switch between preset and custom mode
function switchMode(mode) {
    currentMode = mode;
    
    // Update buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    // Show/hide sections
    if (mode === 'preset') {
        document.getElementById('presetSection').style.display = 'block';
        document.getElementById('mapSection').classList.remove('active');
        customBounds = null;
    } else {
        document.getElementById('presetSection').style.display = 'none';
        document.getElementById('mapSection').classList.add('active');
        selectedPreset = null;
        
        // Fix map sizing after making it visible
        setTimeout(() => {
            if (map) {
                map.invalidateSize();
            }
        }, 100);
    }
}

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map').setView([20.5937, 78.9629], 4); // Center on India
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Initialize drawable layer
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
    // Drawing controls
    const drawControl = new L.Control.Draw({
        draw: {
            polygon: false,
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: {
                shapeOptions: {
                    color: '#8a2be2',
                    weight: 2
                }
            }
        },
        edit: {
            featureGroup: drawnItems,
            remove: true
        }
    });
    map.addControl(drawControl);
    
    // Handle rectangle drawn
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        
        // Clear previous rectangles
        drawnItems.clearLayers();
        drawnItems.addLayer(layer);
        
        // Get bounds
        const bounds = layer.getBounds();
        customBounds = {
            north: bounds.getNorth(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            west: bounds.getWest()
        };
        
        // Display bounds
        displayBounds(customBounds);
        
        // Validate bounds
        validateBounds(customBounds);
    });
}

// Display selected bounds
function displayBounds(bounds) {
    document.getElementById('boundsDisplay').style.display = 'block';
    document.getElementById('boundNorth').textContent = bounds.north.toFixed(4);
    document.getElementById('boundSouth').textContent = bounds.south.toFixed(4);
    document.getElementById('boundEast').textContent = bounds.east.toFixed(4);
    document.getElementById('boundWest').textContent = bounds.west.toFixed(4);
}

// Validate custom bounds
async function validateBounds(bounds) {
    try {
        const response = await fetch('/api/uxsim/validate-bounds', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bounds)
        });
        
        const data = await response.json();
        
        if (!data.valid) {
            showError(data.message);
            customBounds = null;
        }
    } catch (error) {
        console.error('Validation error:', error);
    }
}

// Run simulation
async function runSimulation() {
    // Validate selection
    if (currentMode === 'preset' && !selectedPreset) {
        showError('Please select a preset location');
        return;
    }
    
    if (currentMode === 'custom' && !customBounds) {
        showError('Please draw a rectangle on the map to select an area');
        return;
    }
    
    // Get parameters
    const duration = parseInt(document.getElementById('duration').value);
    const demand = parseInt(document.getElementById('demand').value);
    const roadFilter = document.getElementById('roadFilter').value;
    
    // Show loading
    showLoading(true);
    
    try {
        const requestBody = {
            scenario_key: currentMode === 'preset' ? selectedPreset : null,
            custom_bounds: currentMode === 'custom' ? customBounds : null,
            duration: duration,
            demand: demand,
            custom_filter: roadFilter
        };
        
        const response = await fetch('/api/uxsim/run-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.results);
        } else {
            throw new Error(data.error || 'Simulation failed');
        }
    } catch (error) {
        console.error('Simulation error:', error);
        showError('Simulation failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Display simulation results
function displayResults(results) {
    // Update stats
    document.getElementById('statNodes').textContent = results.nodes || '-';
    document.getElementById('statLinks').textContent = results.links || '-';
    document.getElementById('statTrips').textContent = results.total_trips || '-';
    document.getElementById('statSpeed').textContent = results.average_speed ? 
        (results.average_speed * 3.6).toFixed(1) : '-';
    
    // Display animations
    const animationGrid = document.getElementById('animationGrid');
    animationGrid.innerHTML = '';
    
    if (results.animations) {
        // Network animation
        if (results.animations.network) {
            addAnimation('Network Animation', results.animations.network, 'Traffic flow over time');
        }
        
        // Fancy animation
        if (results.animations.fancy) {
            addAnimation('Vehicle Traces', results.animations.fancy, 'Individual vehicle paths');
        }
    }
    
    // Show results section
    document.getElementById('resultsSection').classList.add('show');
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Add animation to grid
function addAnimation(title, path, description) {
    const grid = document.getElementById('animationGrid');
    const item = document.createElement('div');
    item.className = 'animation-item';
    
    const filename = path.split('/').pop();
    
    item.innerHTML = `
        <img src="/api/uxsim/download-animation/${path}" alt="${title}" 
             onerror="this.src='https://via.placeholder.com/400x400?text=Loading...'" />
        <h4>${title}</h4>
        <p>${description}</p>
        <button class="btn btn-secondary download-btn" onclick="downloadAnimation('${path}')">
            <i class="fas fa-download"></i> Download
        </button>
    `;
    
    grid.appendChild(item);
}

// Download animation
function downloadAnimation(path) {
    window.location.href = `/api/uxsim/download-animation/${path}`;
}

// Reset simulation
function resetSimulation() {
    document.getElementById('resultsSection').classList.remove('show');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

// Show error message
function showError(message) {
    alert('⚠️ ' + message);
}
