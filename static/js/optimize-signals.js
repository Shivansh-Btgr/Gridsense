let simulationRunning = false;
let pollInterval = null;
let rewardChart = null;
let selectedScenario = 'cologne8'; // Default scenario

// Load scenarios and set initial selection
document.addEventListener('DOMContentLoaded', () => {
    loadScenarios();
    setupScenarioSelection();
    
    // Setup form submission
    const form = document.getElementById('simulationForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('Form submitted!');
            await runSimulation();
        });
    } else {
        console.error('Simulation form not found!');
    }
});

function loadScenarios() {
    fetch('/api/scenarios')
        .then(response => response.json())
        .then(data => {
            console.log('Available scenarios:', data.scenarios);
        })
        .catch(error => console.error('Error loading scenarios:', error));
}

function setupScenarioSelection() {
    const cards = document.querySelectorAll('.scenario-card');
    
    console.log('Found', cards.length, 'scenario cards');
    
    // Select first card by default
    if (cards.length > 0) {
        cards[0].classList.add('selected');
        selectedScenario = cards[0].dataset.scenario;
        console.log('Default selected scenario:', selectedScenario);
    } else {
        console.warn('No scenario cards found, using default cologne8');
    }
    
    // Add click handlers
    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove selection from all cards
            cards.forEach(c => c.classList.remove('selected'));
            // Select this card
            card.classList.add('selected');
            selectedScenario = card.dataset.scenario;
            console.log('Selected scenario:', selectedScenario);
        });
    });
}

async function generateGrid() {
    const rows = document.getElementById('gridRows').value;
    const cols = document.getElementById('gridCols').value;
    const name = document.getElementById('gridName').value;
    
    try {
        const response = await fetch('/api/generate-grid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rows, cols, name })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}\n\nNetwork ID: ${result.network_id}\n\nRefresh the page to see it in the scenario list.`);
            // Optionally reload scenarios without page refresh
            location.reload();
        } else {
            alert('❌ Error: ' + result.error);
        }
    } catch (error) {
        console.error('Grid generation error:', error);
        alert('❌ Failed to generate grid network');
    }
}

async function runSimulation() {
    console.log('runSimulation called');
    
    if (simulationRunning) {
        console.log('Simulation already running');
        return;
    }

    // Get form data
    const formData = {
        episodes: parseInt(document.getElementById('episodes').value),
        alpha: parseFloat(document.getElementById('alpha').value),
        gamma: parseFloat(document.getElementById('gamma').value),
        epsilon: parseFloat(document.getElementById('epsilon').value),
        lambda: parseFloat(document.getElementById('lambda').value),
        fourier_order: parseInt(document.getElementById('fourier_order').value),
        scenario: selectedScenario  // Include selected scenario
    };
    
    console.log('Form data:', formData);

    // Validate
    if (formData.episodes < 1 || formData.episodes > 200) {
        alert('Episodes must be between 1 and 200');
        return;
    }

    // Hide form and results, show progress
    document.querySelector('.config-section').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';

    simulationRunning = true;

    // Update progress display
    document.getElementById('totalEpisodes').textContent = formData.episodes;
    document.getElementById('currentEpisode').textContent = '0';
    document.getElementById('progressPercent').textContent = '0%';
    updateProgress(0, 'Initializing simulation...');

    try {
        // Start simulation
        const response = await fetch('/api/run-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Simulation failed');
        }

        const results = await response.json();

        if (results.success) {
            showResults(results);
        } else {
            throw new Error(results.error || 'Simulation failed');
        }

    } catch (error) {
        console.error('Error:', error);
        alert(`Simulation failed: ${error.message}`);
        resetSimulation();
    } finally {
        simulationRunning = false;
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
}

function updateProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
    document.getElementById('progressPercent').textContent = Math.round(percent) + '%';
}

function showResults(results) {
    // Hide progress, show results
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';

    // Update metrics
    document.getElementById('totalReward').textContent = results.total_reward.toFixed(2);
    document.getElementById('avgReward').textContent = results.avg_reward.toFixed(2);

    // Update traffic metrics with fallback
    if (results.metrics) {
        if (results.metrics.avg_system_wait_time !== undefined && results.metrics.avg_system_wait_time > 0) {
            document.getElementById('avgWaitTime').textContent = results.metrics.avg_system_wait_time.toFixed(2) + ' s';
        } else {
            document.getElementById('avgWaitTime').textContent = 'N/A';
        }
        
        if (results.metrics.avg_system_speed !== undefined && results.metrics.avg_system_speed > 0) {
            document.getElementById('avgSpeed').textContent = results.metrics.avg_system_speed.toFixed(2) + ' m/s';
        } else {
            document.getElementById('avgSpeed').textContent = 'N/A';
        }
        
        // Log metrics for debugging
        console.log('Metrics received:', results.metrics);
    } else {
        document.getElementById('avgWaitTime').textContent = 'N/A';
        document.getElementById('avgSpeed').textContent = 'N/A';
        console.warn('No metrics available in results');
    }

    // Create reward chart
    createRewardChart(results.episode_rewards || []);

    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function createRewardChart(episodeRewards) {
    const ctx = document.getElementById('rewardChart');
    if (!ctx) return;

    // Destroy existing chart
    if (rewardChart) {
        rewardChart.destroy();
    }

    // Prepare data
    const episodes = episodeRewards.map((_, i) => i + 1);

    rewardChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: episodes,
            datasets: [{
                label: 'Episode Reward',
                data: episodeRewards,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#b8b8d1'
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(26, 26, 46, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#b8b8d1',
                    borderColor: '#667eea',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Episode',
                        color: '#b8b8d1'
                    },
                    ticks: {
                        color: '#b8b8d1'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Reward',
                        color: '#b8b8d1'
                    },
                    ticks: {
                        color: '#b8b8d1'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    }
                }
            }
        }
    });
}

function resetSimulation() {
    simulationRunning = false;
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }

    document.querySelector('.config-section').style.display = 'grid';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';

    // Reset progress
    updateProgress(0, 'Initializing...');
    document.getElementById('currentEpisode').textContent = '0';
}

function resetForm() {
    document.getElementById('episodes').value = '50';
    document.getElementById('alpha').value = '0.00001';
    document.getElementById('gamma').value = '0.95';
    document.getElementById('epsilon').value = '0.05';
    document.getElementById('lambda').value = '0.1';
    document.getElementById('fourier_order').value = '2';
}

async function openSUMOGUI() {
    const confirmed = confirm(
        '🚦 SUMO GUI Simulation\n\n' +
        'This will:\n' +
        '✓ Run 3 quick training episodes\n' +
        '✓ Open SUMO GUI in a separate window on your desktop\n' +
        '✓ Show live traffic simulation with RL agents learning\n' +
        `✓ Using scenario: ${selectedScenario}\n\n` +
        'Continue?'
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch('/api/run-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                episodes: 3,
                alpha: 0.00001,
                gamma: 0.95,
                epsilon: 0.05,
                lambda: 0.1,
                scenario: selectedScenario,  // Use selected scenario
                fourier_order: 2,
                use_gui: true  // Enable GUI
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ SUMO GUI simulation completed!\n\nCheck the results below.');
            showResults(result);
        } else {
            alert('❌ Error: ' + (result.error || 'Failed to start GUI simulation'));
        }
        
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

// Page load animation
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.info-card, .config-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});
