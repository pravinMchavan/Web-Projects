/**
 * 1. FUNCTION TO ADD NEW INPUTS
 * Adds a new input or textarea to the list when the "+" button is clicked.
 */
function addItem(containerId, name) {
    const container = document.getElementById(containerId);

    const fieldBlock = document.createElement('div');
    fieldBlock.className = 'field-block';

    // Create a new input or textarea
    const input = (name === 'experience') ? document.createElement('textarea') : document.createElement('input');
    const nextIndex = container.querySelectorAll(`[name="${name}[]"]`).length;
    const inputId = `${name}-${nextIndex}`;

    input.id = inputId;
    input.name = name + '[]'; // Matches Flask's getlist()
    input.placeholder = "Add more...";
    input.className = "dynamic-input";

    // Crucial: Tell the new input to update the preview when typed in
    input.oninput = updateLive;

    const options = document.createElement('div');
    options.className = 'field-options';
    options.setAttribute('data-input-id', inputId);

    const defaultSize = (name === 'skills' || name === 'languages') ? 13 : 14;
    options.innerHTML = `
        <label>Font Size <input type="number" min="10" max="48" value="${defaultSize}" class="font-size-input" oninput="updateLive()"></label>
        <label class="bold-toggle"><input type="checkbox" class="font-bold-input" oninput="updateLive()"> Bold</label>
    `;

    fieldBlock.appendChild(input);
    fieldBlock.appendChild(options);
    container.appendChild(fieldBlock);
    updateLive();
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
    const getFieldStyle = (inputEl) => {
        if (!inputEl || !inputEl.id) {
            return {};
        }

        const options = document.querySelector(`.field-options[data-input-id="${inputEl.id}"]`);
        if (!options) {
            return {};
        }

        const sizeInput = options.querySelector('.font-size-input');
        const boldInput = options.querySelector('.font-bold-input');

        return {
            fontSize: sizeInput && sizeInput.value ? `${sizeInput.value}px` : "",
            fontWeight: boldInput && boldInput.checked ? "700" : "400"
        };
    };

    const applyFieldStyle = (targetEl, style) => {
        if (!targetEl) {
            return;
        }
        targetEl.style.fontSize = style.fontSize || "";
        targetEl.style.fontWeight = style.fontWeight || "400";
    };

    // A. Sync Simple Text Fields
    // Uses the ID from HTML input -> ID in the preview
    const syncText = (inputId, outputId, fallback) => {
        const inputEl = document.getElementById(inputId);
        const outputEl = document.getElementById(outputId);
        const val = inputEl.value;
        outputEl.innerText = val || fallback;
        applyFieldStyle(outputEl, getFieldStyle(inputEl));
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
                applyFieldStyle(li, getFieldStyle(input));
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
