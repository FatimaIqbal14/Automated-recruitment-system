/**
 * LinkedIn-Style Skill Selector Autocomplete Widget
 */

function initSkillsAutocomplete(originalInput) {
    if (!originalInput) return;

    // Hide original input
    originalInput.style.display = 'none';

    // State for selected skills
    let selectedSkills = [];
    if (originalInput.value) {
        selectedSkills = originalInput.value.split(',')
            .map(s => s.trim())
            .filter(s => s.length > 0);
    }

    // Create wrapper container
    const widgetContainer = document.createElement('div');
    widgetContainer.className = 'linkedin-skills-widget';

    // Create wrapper for tags + input field (matches LinkedIn input feel)
    const inputWrapper = document.createElement('div');
    inputWrapper.className = 'skills-input-wrapper';

    // Create tags container
    const tagsContainer = document.createElement('div');
    tagsContainer.className = 'skills-selected-container';

    // Create new search input field
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'skills-search-input';
    searchInput.placeholder = originalInput.placeholder || 'Type a skill (e.g. Python, React)';
    searchInput.autocomplete = 'off';

    // Create dropdown container
    const dropdown = document.createElement('div');
    dropdown.className = 'skills-dropdown';

    // Assemble elements
    inputWrapper.appendChild(tagsContainer);
    inputWrapper.appendChild(searchInput);
    widgetContainer.appendChild(inputWrapper);
    widgetContainer.appendChild(dropdown);

    // Insert widget before the hidden original input
    originalInput.parentNode.insertBefore(widgetContainer, originalInput);

    // Focus input when wrapper is clicked
    inputWrapper.addEventListener('click', () => {
        searchInput.focus();
    });

    // Helper: update original hidden input & update view tags
    function updateSkills() {
        originalInput.value = selectedSkills.join(', ');
        // Fire change event just in case
        originalInput.dispatchEvent(new Event('change'));
        renderTags();
    }

    // Helper: render tags in the DOM
    function renderTags() {
        tagsContainer.innerHTML = '';
        selectedSkills.forEach((skill, index) => {
            const chip = document.createElement('div');
            chip.className = 'skill-tag';
            chip.innerText = skill;

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'skill-remove';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeSkill(index);
            });

            chip.appendChild(removeBtn);
            tagsContainer.appendChild(chip);
        });

        // Update placeholder based on selected skills
        if (selectedSkills.length > 0) {
            searchInput.placeholder = '';
        } else {
            searchInput.placeholder = originalInput.placeholder || 'Type a skill (e.g. Python, React)';
        }
    }

    // Helper: add skill
    function addSkill(skillName) {
        const cleaned = skillName.trim();
        if (cleaned && !selectedSkills.some(s => s.toLowerCase() === cleaned.toLowerCase())) {
            selectedSkills.push(cleaned);
            updateSkills();
        }
        searchInput.value = '';
        hideDropdown();
    }

    // Helper: remove skill
    function removeSkill(index) {
        selectedSkills.splice(index, 1);
        updateSkills();
        searchInput.focus();
    }

    // Render initial tags
    renderTags();

    // Autocomplete View state
    let activeIndex = -1;
    let suggestions = [];
    let debounceTimer = null;

    // Fetch and search database
    function fetchSuggestions(query) {
        if (!query.trim()) {
            hideDropdown();
            return;
        }

        fetch(`/skills/autocomplete/?q=${encodeURIComponent(query)}`)
            .then(res => {
                if (!res.ok) throw new Error();
                return res.json();
            })
            .then(data => {
                suggestions = data;
                renderDropdown(query);
            })
            .catch(() => {
                // Fallback to custom suggestion only
                suggestions = [];
                renderDropdown(query);
            });
    }

    // Render suggestions dropdown
    function renderDropdown(query) {
        dropdown.innerHTML = '';
        activeIndex = -1;

        if (suggestions.length === 0) {
            // Show only "+ Add custom skill" option
            const customItem = document.createElement('div');
            customItem.className = 'skills-dropdown-item';
            customItem.innerHTML = `Add custom skill <strong>"${escapeHtml(query)}"</strong>`;
            customItem.addEventListener('click', () => addSkill(query));
            dropdown.appendChild(customItem);
        } else {
            // Render database matched skills
            suggestions.forEach((skill) => {
                const item = document.createElement('div');
                item.className = 'skills-dropdown-item';
                // Highlight the matching characters
                const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
                const highlightedName = skill.name.replace(regex, '<span class="accent">$1</span>');
                item.innerHTML = highlightedName;

                item.addEventListener('click', () => addSkill(skill.name));
                dropdown.appendChild(item);
            });

            // Also add option to add custom input if not exact match
            const exactMatch = suggestions.some(s => s.name.toLowerCase() === query.toLowerCase());
            if (!exactMatch) {
                const customItem = document.createElement('div');
                customItem.className = 'skills-dropdown-item';
                customItem.style.borderTop = '1px solid var(--clr-border)';
                customItem.innerHTML = `Add custom skill <strong>"${escapeHtml(query)}"</strong>`;
                customItem.addEventListener('click', () => addSkill(query));
                dropdown.appendChild(customItem);
            }
        }

        dropdown.classList.add('show');
    }

    function hideDropdown() {
        dropdown.classList.remove('show');
        dropdown.innerHTML = '';
        activeIndex = -1;
    }

    // Input event listener with debounce
    searchInput.addEventListener('input', (e) => {
        const val = searchInput.value;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchSuggestions(val);
        }, 150);
    });

    // Keyboard handlers
    searchInput.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.skills-dropdown-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (items.length > 0) {
                if (activeIndex >= 0) {
                    items[activeIndex].classList.remove('active');
                }
                activeIndex = (activeIndex + 1) % items.length;
                items[activeIndex].classList.add('active');
                items[activeIndex].scrollIntoView({ block: 'nearest' });
            }
        } 
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (items.length > 0) {
                if (activeIndex >= 0) {
                    items[activeIndex].classList.remove('active');
                }
                activeIndex = (activeIndex - 1 + items.length) % items.length;
                items[activeIndex].classList.add('active');
                items[activeIndex].scrollIntoView({ block: 'nearest' });
            }
        } 
        else if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault(); // Prevent standard form submit on Enter
            if (activeIndex >= 0 && items[activeIndex]) {
                items[activeIndex].click();
            } else if (searchInput.value.trim()) {
                // If there's only one suggestion, or user hit enter on typed text
                addSkill(searchInput.value);
            }
        } 
        else if (e.key === 'Escape') {
            hideDropdown();
        } 
        else if (e.key === 'Backspace' && searchInput.value === '') {
            if (selectedSkills.length > 0) {
                removeSkill(selectedSkills.length - 1);
            }
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!widgetContainer.contains(e.target)) {
            hideDropdown();
        }
    });

    // Prevent submitting the form when pressing Enter inside search input
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
        }
    });

    // HTML escape helpers
    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;')
                  .replace(/'/g, '&#039;');
    }

    // Escape regex characters
    function escapeRegex(string) {
        return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    }
}

// Auto-run if script is loaded and element is present
document.addEventListener('DOMContentLoaded', () => {
    const inputElement = document.getElementById('id_skills_text');
    if (inputElement) {
        initSkillsAutocomplete(inputElement);
    }
});
