// Signal Tuning JavaScript

let map = null;
let drawnItems = null;
let customBounds = null;
let networkData = null;
let selectedSignals = [];
let signalSettings = [];

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    
    // Toggle mode comparison parameters
    document.getElementById('enableModeComparison').addEventListener('change', function() {
        document.getElementById('modeComparisonParams').style.display = this.checked ? 'block' : 'none';
    });
});

// Initialize Leaflet map
function initializeMap() {
    map = L.map('map').setView([20.5937, 78.9629], 4);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
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
    
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        drawnItems.clearLayers();
        drawnItems.addLayer(layer);
        
        const bounds = layer.getBounds();
        customBounds = {
            north: bounds.getNorth(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            west: bounds.getWest()
        };
        
        displayBounds(customBounds);
        document.getElementById('loadNetworkBtn').disabled = false;
    });
    
    setTimeout(() => {
        map.invalidateSize();
    }, 100);
}

function displayBounds(bounds) {
    document.getElementById('boundsDisplay').style.display = 'block';
    document.getElementById('boundNorth').textContent = bounds.north.toFixed(4);
    document.getElementById('boundSouth').textContent = bounds.south.toFixed(4);
    document.getElementById('boundEast').textContent = bounds.east.toFixed(4);
    document.getElementById('boundWest').textContent = bounds.west.toFixed(4);
}

async function loadNetwork() {
    if (!customBounds) {
        showError('Please select an area on the map first');
        return;
    }
    
    showLoading(true, 'Loading Network...', 'Downloading OpenStreetMap data and analyzing intersections...');
    
    try {
        const response = await fetch('/api/signal/load-network', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(customBounds)
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load network');
        }
        
        networkData = data;
        displaySignalCandidates(data.signal_candidates);
        goToStep(2);
        
    } catch (error) {
        console.error('Network load error:', error);
        showError('Failed to load network: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displaySignalCandidates(candidates) {
    const grid = document.getElementById('signalNodesGrid');
    document.getElementById('signalCount').textContent = candidates.length;
    
    grid.innerHTML = '';
    
    if (candidates.length === 0) {
        grid.innerHTML = '<p>No suitable intersections found. Try selecting a larger urban area.</p>';
        return;
    }
    
    candidates.forEach((node, index) => {
        const card = document.createElement('div');
        card.className = 'signal-node-card';
        card.onclick = () => toggleSignalNode(index, card);
        
        card.innerHTML = `
            <h4>Intersection ${index + 1}</h4>
            <p><i class="fas fa-crossroads"></i> ${node.connections} connections</p>
            <p style="font-size: 0.85rem; color: #888;">
                Lat: ${node.y.toFixed(4)}, Lon: ${node.x.toFixed(4)}
            </p>
            <input type="checkbox" id="signal-${index}" style="margin-top: 0.5rem;">
            <label for="signal-${index}">Include this signal</label>
        `;
        
        grid.appendChild(card);
    });
}

function toggleSignalNode(index, cardElement) {
    const checkbox = document.getElementById(`signal-${index}`);
    checkbox.checked = !checkbox.checked;
    
    if (checkbox.checked) {
        cardElement.classList.add('selected');
        if (!selectedSignals.includes(index)) {
            selectedSignals.push(index);
        }
    } else {
        cardElement.classList.remove('selected');
        selectedSignals = selectedSignals.filter(i => i !== index);
    }
    
    document.getElementById('configureBtn').disabled = selectedSignals.length === 0;
}

function goToStep(step) {
    // Hide all step contents
    for (let i = 1; i <= 4; i++) {
        document.getElementById(`stepContent${i}`).style.display = 'none';
        document.getElementById(`step${i}`).classList.remove('active', 'completed');
    }
    
    // Show current step
    document.getElementById(`stepContent${step}`).style.display = 'block';
    document.getElementById(`step${step}`).classList.add('active');
    
    // Mark previous steps as completed
    for (let i = 1; i < step; i++) {
        document.getElementById(`step${i}`).classList.add('completed');
    }
}

function goToStep3() {
    if (selectedSignals.length === 0) {
        showError('Please select at least one intersection');
        return;
    }
    
    displaySignalConfig();
    goToStep(3);
}

function displaySignalConfig() {
    const grid = document.getElementById('signalConfigGrid');
    grid.innerHTML = '';
    
    signalSettings = [];
    
    selectedSignals.forEach((nodeIndex, i) => {
        const node = networkData.signal_candidates[nodeIndex];
        
        const configCard = document.createElement('div');
        configCard.className = 'signal-controls';
        
        configCard.innerHTML = `
            <h3>Intersection ${nodeIndex + 1}</h3>
            <p style="color: #888; font-size: 0.9rem;">
                ${node.connections} connections at Lat: ${node.y.toFixed(4)}, Lon: ${node.x.toFixed(4)}
            </p>
            
            <div class="signal-param">
                <label for="cycle-${i}">
                    <i class="fas fa-clock"></i> Cycle Time (seconds)
                    <small style="color: #888; display: block;">Total time for one complete signal cycle</small>
                </label>
                <input type="range" id="cycle-${i}" min="60" max="180" value="120" step="10"
                       oninput="document.getElementById('cycle-val-${i}').textContent = this.value">
                <span id="cycle-val-${i}">120</span> seconds
            </div>
            
            <div class="signal-param">
                <label for="green-${i}">
                    <i class="fas fa-circle" style="color: #4caf50;"></i> Green Time (seconds)
                    <small style="color: #888; display: block;">Duration of green light (red = cycle - green)</small>
                </label>
                <input type="range" id="green-${i}" min="20" max="120" value="60" step="5"
                       oninput="document.getElementById('green-val-${i}').textContent = this.value">
                <span id="green-val-${i}">60</span> seconds
            </div>
            
            <div class="signal-param">
                <label for="offset-${i}">
                    <i class="fas fa-adjust"></i> Offset (seconds)
                    <small style="color: #888; display: block;">Delay from cycle start (for coordination)</small>
                </label>
                <input type="range" id="offset-${i}" min="0" max="120" value="0" step="5"
                       oninput="document.getElementById('offset-val-${i}').textContent = this.value">
                <span id="offset-val-${i}">0</span> seconds
            </div>
        `;
        
        grid.appendChild(configCard);
        
        // Initialize settings
        signalSettings.push({
            node_id: node.id,
            cycle: 120,
            green_time: 60,
            offset: 0
        });
    });
}

function goToStep4() {
    // Update signal settings from inputs
    selectedSignals.forEach((nodeIndex, i) => {
        signalSettings[i].cycle = parseInt(document.getElementById(`cycle-${i}`).value);
        signalSettings[i].green_time = parseInt(document.getElementById(`green-${i}`).value);
        signalSettings[i].offset = parseInt(document.getElementById(`offset-${i}`).value);
    });
    
    goToStep(4);
}

async function runSimulation() {
    const duration = parseInt(document.getElementById('simDuration').value);
    const demand = parseInt(document.getElementById('simDemand').value);
    const enableModeComparison = document.getElementById('enableModeComparison').checked;
    
    if (enableModeComparison) {
        // Run mode comparison
        await runModeComparison();
    } else {
        // Run single simulation
        await runStandardSimulation();
    }
}

async function runStandardSimulation() {
    const duration = parseInt(document.getElementById('simDuration').value);
    const demand = parseInt(document.getElementById('simDemand').value);
    
    showLoading(true, 'Running Simulation...', 'This may take 2-5 minutes. Simulating traffic with your signal settings...');
    
    try {
        const response = await fetch('/api/signal/run-optimization', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                signal_settings: signalSettings,
                duration: duration,
                demand: demand
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Simulation failed');
        }
        
        displayResults(data.results);
        
    } catch (error) {
        console.error('Simulation error:', error);
        showError('Simulation failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

async function runModeComparison() {
    const duration = parseInt(document.getElementById('simDuration').value);
    const demand = parseInt(document.getElementById('simDemand').value);
    const ridesharePercent = parseInt(document.getElementById('ridesharePercent').value);
    const numTaxis = parseInt(document.getElementById('numTaxis').value);
    
    showLoading(true, 'Running Mode Comparison...', 
        `Comparing private cars vs rideshare. This will run 2 scenarios and may take 5-10 minutes...`);
    
    try {
        const response = await fetch('/api/signal/run-mode-comparison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                signal_settings: signalSettings,
                duration: duration,
                demand: demand,
                rideshare_percent: ridesharePercent,
                num_taxis: numTaxis
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Mode comparison failed');
        }
        
        displayModeComparisonResults(data.results);
        
    } catch (error) {
        console.error('Mode comparison error:', error);
        showError('Mode comparison failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(results) {
    document.getElementById('resultsSection').style.display = 'block';
    
    document.getElementById('statTrips').textContent = results.total_trips || '-';
    document.getElementById('statAvgSpeed').textContent = 
        results.average_speed ? results.average_speed.toFixed(2) : '-';
    document.getElementById('statAvgTime').textContent = 
        results.average_travel_time ? results.average_travel_time.toFixed(1) : '-';
    
    // Display visualizations in order
    const vizGrid = document.getElementById('visualizationsGrid');
    vizGrid.innerHTML = '';
    
    if (results.visualizations && Object.keys(results.visualizations).length > 0) {
        // Display in the order they appear in the object
        Object.entries(results.visualizations).forEach(([name, path]) => {
            const vizCard = document.createElement('div');
            vizCard.style.marginBottom = '3rem';
            
            vizCard.innerHTML = `
                <h3 style="margin-bottom: 1rem; color: var(--primary-color);">
                    <i class="fas fa-chart-area"></i> ${name}
                </h3>
                <div style="background: #1a1a2e; padding: 1.5rem; border-radius: 12px; border: 2px solid rgba(138, 43, 226, 0.3);">
                    <img src="/api/uxsim/download-animation/${path}" 
                         alt="${name}" 
                         style="max-width: 100%; border-radius: 8px; display: block;"
                         onerror="this.parentElement.innerHTML='<p style=\\'text-align:center;color:#888;\\'>Visualization not available</p>'">
                </div>
                ${name === 'Time-Space Diagram' ? 
                    '<p style="margin-top: 1rem; color: #888; font-size: 0.9rem;"><i class="fas fa-info-circle"></i> Shows vehicle trajectories over time and space. Each line represents a vehicle\'s journey along the road.</p>' : 
                    '<p style="margin-top: 1rem; color: #888; font-size: 0.9rem;"><i class="fas fa-info-circle"></i> Final network state showing node colors (traffic load) and link thickness (capacity).</p>'
                }
            `;
            
            vizGrid.appendChild(vizCard);
        });
    } else {
        vizGrid.innerHTML = '<p style="text-align: center; color: #888;">No visualizations available</p>';
    }
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function displayModeComparisonResults(results) {
    document.getElementById('resultsSection').style.display = 'block';
    
    const vizGrid = document.getElementById('visualizationsGrid');
    vizGrid.innerHTML = '';
    
    // Create comparison header
    const header = document.createElement('div');
    header.style.marginBottom = '2rem';
    header.innerHTML = `
        <h2 style="text-align: center; margin-bottom: 1rem;">
            🚗 vs 🚕 Transportation Mode Comparison
        </h2>
    `;
    vizGrid.appendChild(header);
    
    // Create side-by-side comparison
    const comparisonGrid = document.createElement('div');
    comparisonGrid.style.display = 'grid';
    comparisonGrid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(400px, 1fr))';
    comparisonGrid.style.gap = '2rem';
    comparisonGrid.style.marginBottom = '3rem';
    
    // Display each scenario
    Object.entries(results.scenarios).forEach(([key, scenario]) => {
        const card = document.createElement('div');
        card.style.background = 'var(--card-bg)';
        card.style.padding = '2rem';
        card.style.borderRadius = '12px';
        card.style.border = '2px solid rgba(138, 43, 226, 0.3)';
        
        const icon = key === 'private_only' ? '🚙' : '🚕';
        const isWinner = results.comparison.winner === key;
        
        card.innerHTML = `
            <h3 style="margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
                <span>${icon} ${scenario.mode_name}</span>
                ${isWinner ? '<span style="background: #4caf50; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem;">🏆 Winner</span>' : ''}
            </h3>
            
            <div style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-size: 0.8rem; color: #888;">Avg Speed</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">${scenario.average_speed.toFixed(2)} m/s</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8rem; color: #888;">Avg Travel Time</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">${scenario.average_travel_time.toFixed(1)} s</div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.8rem; color: #888;">Total Trips</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">${scenario.total_trips}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8rem; color: #888;">Vehicles</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">${scenario.total_vehicles}</div>
                    </div>
                </div>
            </div>
            
            ${scenario.rideshare_trips > 0 ? `
                <div style="background: rgba(138, 43, 226, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                    <div style="font-weight: bold; margin-bottom: 0.5rem;">🚕 Rideshare Stats</div>
                    <div style="font-size: 0.9rem;">
                        <div>Private Cars: ${scenario.private_cars}</div>
                        <div>Rideshare Trips: ${scenario.rideshare_trips}</div>
                        <div>Available Taxis: ${scenario.num_taxis}</div>
                        ${scenario.taxi_stats.waiting_time ? `<div>Avg Wait Time: ${scenario.taxi_stats.waiting_time.toFixed(1)}s</div>` : ''}
                    </div>
                </div>
            ` : ''}
            
            <img src="/api/uxsim/download-animation/${scenario.visualization}" 
                 alt="${scenario.mode_name}" 
                 style="max-width: 100%; border-radius: 8px; margin-top: 1rem;"
                 onerror="this.style.display='none'">
        `;
        
        comparisonGrid.appendChild(card);
    });
    
    vizGrid.appendChild(comparisonGrid);
    
    // Show comparison metrics
    if (results.comparison.metrics) {
        const metrics = results.comparison.metrics;
        const metricsCard = document.createElement('div');
        metricsCard.style.background = 'linear-gradient(135deg, rgba(138, 43, 226, 0.2), rgba(255, 20, 147, 0.2))';
        metricsCard.style.padding = '2rem';
        metricsCard.style.borderRadius = '12px';
        metricsCard.style.marginTop = '2rem';
        
        const formatChange = (value, higherIsBetter = true) => {
            const color = (higherIsBetter ? value > 0 : value < 0) ? '#4caf50' : '#f44336';
            const arrow = value > 0 ? '↑' : '↓';
            return `<span style="color: ${color}; font-weight: bold;">${arrow} ${Math.abs(value).toFixed(1)}%</span>`;
        };
        
        metricsCard.innerHTML = `
            <h3 style="text-align: center; margin-bottom: 1.5rem;">📊 Impact Analysis</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                <div style="text-align: center;">
                    <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Speed Change</div>
                    <div style="font-size: 1.5rem;">${formatChange(metrics.speed_improvement, true)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Travel Time</div>
                    <div style="font-size: 1.5rem;">${formatChange(metrics.time_reduction, true)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Vehicles on Road</div>
                    <div style="font-size: 1.5rem;">${formatChange(metrics.vehicle_reduction, true)}</div>
                </div>
            </div>
        `;
        
        vizGrid.appendChild(metricsCard);
    }
    
    // Update main stats with winner
    const winner = results.scenarios[results.comparison.winner];
    document.getElementById('statTrips').textContent = winner.total_trips || '-';
    document.getElementById('statAvgSpeed').textContent = winner.average_speed.toFixed(2);
    document.getElementById('statAvgTime').textContent = winner.average_travel_time.toFixed(1);
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function showLoading(show, text = 'Processing...', subtext = '') {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
    
    if (show) {
        document.getElementById('loadingText').textContent = text;
        document.getElementById('loadingSubtext').textContent = subtext;
    }
}

function showError(message) {
    alert(message);
}
