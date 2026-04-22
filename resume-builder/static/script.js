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

function applyTemplate() {
    const selected = document.getElementById('in-template').value;
    const canvas = document.getElementById('resume-canvas');
    canvas.classList.remove('template-modern', 'template-classic', 'template-compact');
    canvas.classList.add(`template-${selected}`);
}

function collectResumeData() {
    const getList = (name) => {
        return Array.from(document.getElementsByName(name + '[]'))
            .map((item) => item.value.trim())
            .filter(Boolean);
    };

    return {
        name: (document.getElementById('in-name').value || '').trim(),
        description: (document.getElementById('in-desc').value || '').trim(),
        education: getList('education'),
        skills: getList('skills'),
        projects: getList('projects'),
        experience: getList('experience')
    };
}

function escapeHtml(value) {
    return value
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function decodeHtml(value) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = value;
    return textarea.value;
}

function useSummary(text) {
    const desc = document.getElementById('in-desc');
    desc.value = decodeHtml(text);
    updateLive();
}

function closePanel(panelId) {
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.innerHTML = '';
    }
}

function animateScoreCircle(circleEl, labelEl, targetScore) {
    let current = 0;
    const finalScore = Math.max(0, Math.min(100, Number(targetScore) || 0));
    const duration = 850;
    const frameDelay = 16;
    const step = Math.max(1, Math.ceil(finalScore / (duration / frameDelay)));

    const timer = setInterval(() => {
        current = Math.min(finalScore, current + step);
        circleEl.style.setProperty('--score', current);
        labelEl.textContent = `${current}%`;

        if (current >= finalScore) {
            clearInterval(timer);
        }
    }, frameDelay);
}

function generateSummarySuggestions() {
    const data = collectResumeData();
    const box = document.getElementById('summary-suggestions');

    const uniq = (items) => {
        const seen = new Set();
        return items.filter((item) => {
            const key = String(item || '').trim().toLowerCase();
            if (!key || seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    };

    const pluralize = (count, one, many = `${one}s`) => (count === 1 ? one : many);

    const normalizeText = (text) => {
        return String(text || '')
            .replace(/\b(iot)\b/gi, 'IoT')
            .replace(/\bporject\b/gi, 'project')
            .replace(/\benginner\b/gi, 'Engineer')
            .replace(/\s+/g, ' ')
            .trim();
    };

    const skills = uniq((data.skills || []).map(normalizeText));
    const primarySkill = skills[0] || '';

    const roleHint = primarySkill ? `${primarySkill}-focused` : 'detail-oriented';
    const secondarySkills = skills.filter((s) => s.toLowerCase() !== primarySkill.toLowerCase()).slice(0, 3);
    const skillLine = secondarySkills.length
        ? `with strengths in ${secondarySkills.join(', ')}`
        : (primarySkill ? `with strengths in ${primarySkill}` : 'with strong problem-solving and communication skills');

    const projects = uniq((data.projects || []).map(normalizeText));
    const projectCount = projects.length;
    const projectLine = projectCount
        ? (projectCount === 1
            ? `Built 1 project: ${projects[0]}.`
            : `Built ${projectCount} ${pluralize(projectCount, 'project')}, including ${projects[0]}.`)
        : 'Built practical academic and self-driven projects.';

    const experience = uniq((data.experience || []).map(normalizeText));
    const headlineRole = experience.length
        ? (experience[0].length <= 48 ? experience[0] : '')
        : '';
    const roleLine = headlineRole
        ? `${headlineRole} with a ${roleHint} background.`
        : `I’m a ${roleHint} candidate.`;

    const expLine = experience.length
        ? `Hands-on experience includes ${experience[0]}.`
        : 'I’m actively seeking opportunities to apply these skills in real-world work.';

    const education = uniq((data.education || []).map(normalizeText));
    const eduLine = education.length ? `Education: ${education[0]}.` : 'Strong academic foundation in computer applications.';

    const skillSentence = skills.length
        ? `Skilled in ${skills.slice(0, 4).join(', ')}.`
        : 'Skilled in problem-solving, communication, and building practical projects.';

    const suggestions = [
        `${roleLine} ${skillSentence} ${projectLine}`,
        `I bring hands-on experience ${skillLine}. ${expLine}`,
        `${skillSentence} ${eduLine} ${projectLine}`
    ];

    box.innerHTML = suggestions.map((text) => {
        const safe = escapeHtml(text);
        return `<div class="ai-item"><p>${safe}</p><button type="button" class="btn-use" data-summary="${safe}" onclick="useSummary(this.dataset.summary)">Use This</button></div>`;
    }).join('');

    box.innerHTML = `
        <div class="ai-panel-header">
            <strong>Summary Suggestions</strong>
            <button type="button" class="btn-close-panel" onclick="closePanel('summary-suggestions')">Close</button>
        </div>
        ${box.innerHTML}
    `;
}

async function analyzeResume() {
    const panel = document.getElementById('analysis-result');
    panel.innerHTML = `
        <div class="ai-panel-header">
            <strong>Resume Analysis</strong>
            <button type="button" class="btn-close-panel" onclick="closePanel('analysis-result')">Close</button>
        </div>
        <div class="ai-item"><p>Analyzing resume...</p></div>
    `;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(collectResumeData())
        });

        const result = await response.json();
        if (!response.ok || result.error) {
            throw new Error(result.error || 'Analysis failed');
        }

        const section = result.section_scores || {};
        const suggestions = (result.suggestions || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('');

        panel.innerHTML = `
            <div class="ai-panel-header">
                <strong>Resume Analysis</strong>
                <button type="button" class="btn-close-panel" onclick="closePanel('analysis-result')">Close</button>
            </div>
            <div class="ai-item">
                <div class="score-wrap">
                    <div class="score-circle" id="analysis-score-circle" style="--score:0;">
                        <span id="analysis-score-label">0%</span>
                    </div>
                    <p><strong>AI Resume Score:</strong> ${result.overall_score}/100</p>
                </div>
                <p>Summary: ${section.summary || 0}/20 | Skills: ${section.skills || 0}/20 | Projects: ${section.projects || 0}/20 | Experience: ${section.experience || 0}/20 | Education: ${section.education || 0}/20</p>
                <ul>${suggestions}</ul>
            </div>
        `;

        const circle = document.getElementById('analysis-score-circle');
        const label = document.getElementById('analysis-score-label');
        if (circle && label) {
            animateScoreCircle(circle, label, result.overall_score);
        }
    } catch (error) {
        panel.innerHTML = `
            <div class="ai-panel-header">
                <strong>Resume Analysis</strong>
                <button type="button" class="btn-close-panel" onclick="closePanel('analysis-result')">Close</button>
            </div>
            <div class="ai-item"><p>${escapeHtml(error.message || 'Unable to analyze now.')}</p></div>
        `;
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
window.onload = function () {
    applyTemplate();
    updateLive();
};
