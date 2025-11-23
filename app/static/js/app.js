document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const errorMessage = document.getElementById('errorMessage');
    const multipleResultsSection = document.getElementById('multipleResultsSection');
    const resultsList = document.getElementById('resultsList');
    const resultsSection = document.getElementById('resultsSection');
    const resourceName = document.getElementById('resourceName');
    const resourceType = document.getElementById('resourceType');
    const floorplanName = document.getElementById('floorplanName');
    const floorplanImage = document.getElementById('floorplanImage');
    const cursor = document.getElementById('cursor');

    // XSS protection: HTML escape function
    function escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Handle search on button click
    searchButton.addEventListener('click', performSearch);

    // Handle search on Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    function performSearch() {
        const query = searchInput.value.trim();

        if (!query) {
            showError('Please enter a search term');
            return;
        }

        // Clear previous results
        hideError();
        hideResults();
        hideMultipleResults();

        // Perform API search
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Resource not found');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.count === 1) {
                    // Single result - show directly
                    displaySingleResult(data.results[0]);
                } else {
                    // Multiple results - show selection
                    displayMultipleResults(data);
                }
            })
            .catch(error => {
                showError(error.message || 'An error occurred while searching');
            });
    }

    function displayMultipleResults(data) {
        const count = data.count;
        const results = data.results;

        // Update count text
        const countText = multipleResultsSection.querySelector('.results-count');
        countText.textContent = `Found ${count} matching resource${count !== 1 ? 's' : ''}. Click on one to view its location:`;

        // Build results list with XSS protection
        resultsList.innerHTML = results.map((result, index) => {
            const resource = result.resource;
            const floorplan = result.floorplan;

            return `
                <div class="result-card" onclick="selectResult(${index})">
                    <h3>${escapeHtml(resource.name)}</h3>
                    <div class="result-meta">
                        <span class="type">Type: ${escapeHtml(resource.type)}</span>
                        <span>Location: ${escapeHtml(floorplan ? floorplan.name : 'Unknown')}</span>
                        <span>Coordinates: (${escapeHtml(resource.x_coordinate)}, ${escapeHtml(resource.y_coordinate)})</span>
                    </div>
                </div>
            `;
        }).join('');

        // Store results for later selection
        window.searchResults = results;

        // Show multiple results section
        multipleResultsSection.classList.add('show');
    }

    window.selectResult = function(index) {
        const result = window.searchResults[index];
        hideMultipleResults();
        displaySingleResult(result);
    };

    function displaySingleResult(data) {
        const resource = data.resource;
        const floorplan = data.floorplan;

        if (!resource || !floorplan) {
            showError('Invalid data received from server');
            return;
        }

        // Update resource information (using textContent for XSS protection)
        resourceName.textContent = resource.name;
        resourceType.textContent = `Type: ${resource.type}`;

        // Update floorplan information (using textContent for XSS protection)
        floorplanName.textContent = `Location: ${floorplan.name}`;

        // Set floorplan image and wait for it to load
        // Note: floorplan.image_filename comes from server and should already be sanitized
        floorplanImage.onload = function() {
            // Position the cursor at the resource coordinates
            positionCursor(resource.x_coordinate, resource.y_coordinate);

            // Show results with animation
            resultsSection.classList.add('show');
        };

        floorplanImage.onerror = function() {
            showError('Failed to load floorplan image');
        };

        // Sanitize filename to prevent directory traversal
        const sanitizedFilename = floorplan.image_filename.replace(/[^a-zA-Z0-9._-]/g, '_');
        floorplanImage.src = `/static/floorplans/${sanitizedFilename}`;
    }

    function positionCursor(x, y) {
        // Position the cursor at the given coordinates
        cursor.style.left = `${x}px`;
        cursor.style.top = `${y}px`;
        cursor.style.display = 'block';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add('show');
        hideResults();
    }

    function hideError() {
        errorMessage.classList.remove('show');
    }

    function hideResults() {
        resultsSection.classList.remove('show');
        cursor.style.display = 'none';
    }

    function hideMultipleResults() {
        multipleResultsSection.classList.remove('show');
    }
});
