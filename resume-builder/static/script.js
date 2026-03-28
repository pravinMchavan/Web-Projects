/**
 * 1. FUNCTION TO ADD NEW INPUTS
 * Adds a new input or textarea to the list when the "+" button is clicked.
 */
function addItem(containerId, name) {
    const container = document.getElementById(containerId);
    
    // Create a new input or textarea
    const input = (name === 'experience') ? document.createElement('textarea') : document.createElement('input');
    
    input.name = name + '[]'; // Matches Flask's getlist()
    input.placeholder = "Add more...";
    input.className = "dynamic-input";
    
    // Crucial: Tell the new input to update the preview when typed in
    input.oninput = updateLive; 
    
    container.appendChild(input);
}

/**
 * 2. IMAGE PREVIEW HANDLER
 * Shows the uploaded photo in the resume sidebar immediately.
 */
function previewImage(event) {
    const reader = new FileReader();
    reader.onload = function() {
        const output = document.getElementById('rt-photo');
        output.src = reader.result;
        output.style.display = "block"; // Make the image visible
    }
    if (event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
}

/**
 * 3. THE LIVE SYNC ENGINE
 * This function runs every time you type in an input field.
 */
function updateLive() {
    // A. Sync Simple Text Fields
    // Uses the ID from HTML input -> ID in the preview
    const syncText = (inputId, outputId, fallback) => {
        const val = document.getElementById(inputId).value;
        document.getElementById(outputId).innerText = val || fallback;
    };

    syncText('in-name', 'rt-name', 'YOUR NAME');
    syncText('in-email', 'rt-email', 'email@example.com');
    syncText('in-phone', 'rt-phone', '0000 000 000');
    syncText('in-desc', 'rt-desc', 'Your professional summary will appear here...');

    // B. Sync Dynamic Lists (Education, Projects, Skills, etc.)
    const syncList = (inputName, outputId) => {
        // Get all inputs with the same name (e.g., all education[] inputs)
        const inputs = document.getElementsByName(inputName + '[]');
        const outputList = document.getElementById('rt-' + outputId);
        
        // Clear the current list in the preview
        outputList.innerHTML = '';

        // Loop through inputs and add them to the preview as <li> items
        inputs.forEach(input => {
            if (input.value.trim() !== "") {
                const li = document.createElement('li');
                li.innerText = input.value;
                outputList.appendChild(li);
            }
        });
    };

    // Run the list sync for every category
    syncList('education', 'education');
    syncList('projects', 'projects');
    syncList('experience', 'experience');
    syncList('skills', 'skills');
    syncList('languages', 'languages');
}

// Ensure the preview is updated once on page load
window.onload = updateLive;
