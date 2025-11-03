let selectedFile = null;
let outputFilename = null;

// File input change handler
document.getElementById('videoInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and drop functionality
const uploadCard = document.querySelector('.upload-card');

uploadCard.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = '#667eea';
    uploadCard.style.background = 'rgba(102, 126, 234, 0.05)';
});

uploadCard.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = '';
    uploadCard.style.background = '';
});

uploadCard.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = '';
    uploadCard.style.background = '';
    
    const file = e.dataTransfer.files[0];
    if (file && isValidFileType(file)) {
        document.getElementById('videoInput').files = e.dataTransfer.files;
        handleFileSelect(file);
    } else {
        showError('Invalid file format. Please upload a video file (MP4, AVI, MOV, or MKV).');
    }
});

function isValidFileType(file) {
    const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/x-matroska'];
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv'];
    return validTypes.includes(file.type) || validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
}

function handleFileSelect(file) {
    if (!isValidFileType(file)) {
        showError('Invalid file format. Please upload a video file (MP4, AVI, MOV, or MKV).');
        return;
    }

    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
        showError('File size exceeds 500MB limit. Please choose a smaller file.');
        return;
    }

    selectedFile = file;
    
    // Show file details
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('selectedFile').style.display = 'block';
    document.getElementById('processBtn').style.display = 'inline-flex';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function removeFile() {
    selectedFile = null;
    document.getElementById('videoInput').value = '';
    document.getElementById('selectedFile').style.display = 'none';
    document.getElementById('processBtn').style.display = 'none';
}

async function processVideo() {
    if (!selectedFile) return;

    // Hide upload section and show progress
    document.querySelector('.upload-card').style.display = 'none';
    document.getElementById('progressSection').style.display = 'block';

    const formData = new FormData();
    formData.append('video', selectedFile);

    try {
        // Simulate progress steps
        updateProgress(0, 'Uploading video...');
        setStepActive('step1');

        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 50; // First 50% for upload
                updateProgress(percentComplete, 'Uploading video...');
            }
        });

        xhr.addEventListener('load', async () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                
                if (response.success) {
                    // Simulate processing steps
                    setStepCompleted('step1');
                    setStepActive('step2');
                    updateProgress(60, 'Analyzing frames with AI...');
                    
                    await sleep(1000);
                    setStepCompleted('step2');
                    setStepActive('step3');
                    updateProgress(80, 'Labeling objects...');
                    
                    await sleep(1000);
                    setStepCompleted('step3');
                    setStepActive('step4');
                    updateProgress(100, 'Processing complete!');
                    
                    await sleep(500);
                    setStepCompleted('step4');
                    
                    // Show success
                    outputFilename = response.output_file;
                    showSuccess(response.message);
                } else {
                    showError(response.error || 'Processing failed');
                }
            } else {
                const error = JSON.parse(xhr.responseText);
                showError(error.error || 'An error occurred during processing');
            }
        });

        xhr.addEventListener('error', () => {
            showError('Network error. Please check your connection and try again.');
        });

        xhr.open('POST', '/api/process-video');
        xhr.send(formData);

        // Simulate initial upload
        updateProgress(10, 'Uploading video...');

    } catch (error) {
        console.error('Error:', error);
        showError('An unexpected error occurred. Please try again.');
    }
}

function updateProgress(percent, text) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = text;
}

function setStepActive(stepId) {
    const step = document.getElementById(stepId);
    step.classList.add('active');
    step.classList.remove('completed');
}

function setStepCompleted(stepId) {
    const step = document.getElementById(stepId);
    step.classList.remove('active');
    step.classList.add('completed');
}

function showSuccess(message) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultMessage').textContent = message;
    document.getElementById('resultSection').style.display = 'block';
}

function showError(message) {
    document.getElementById('progressSection').style.display = 'none';
    document.querySelector('.upload-card').style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
    
    // Hide error after 5 seconds
    setTimeout(() => {
        document.getElementById('errorSection').style.display = 'none';
    }, 5000);
}

function downloadVideo() {
    if (outputFilename) {
        window.location.href = `/api/download-video/${outputFilename}`;
    }
}

function resetForm() {
    selectedFile = null;
    outputFilename = null;
    document.getElementById('videoInput').value = '';
    document.getElementById('selectedFile').style.display = 'none';
    document.getElementById('processBtn').style.display = 'none';
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.querySelector('.upload-card').style.display = 'block';
    
    // Reset progress
    updateProgress(0, 'Uploading video...');
    
    // Reset steps
    ['step1', 'step2', 'step3', 'step4'].forEach(stepId => {
        const step = document.getElementById(stepId);
        step.classList.remove('active', 'completed');
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Add animation on page load
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.info-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateX(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, index * 100);
    });
});
