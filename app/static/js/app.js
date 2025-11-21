document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('resultsSection');
    const resourceName = document.getElementById('resourceName');
    const resourceType = document.getElementById('resourceType');
    const floorplanName = document.getElementById('floorplanName');
    const floorplanImage = document.getElementById('floorplanImage');
    const cursor = document.getElementById('cursor');

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
                displayResults(data);
            })
            .catch(error => {
                showError(error.message || 'An error occurred while searching');
            });
    }

    function displayResults(data) {
        const resource = data.resource;
        const floorplan = data.floorplan;

        if (!resource || !floorplan) {
            showError('Invalid data received from server');
            return;
        }

        // Update resource information
        resourceName.textContent = resource.name;
        resourceType.textContent = `Type: ${resource.type}`;

        // Update floorplan information
        floorplanName.textContent = `Location: ${floorplan.name}`;

        // Set floorplan image and wait for it to load
        floorplanImage.onload = function() {
            // Position the cursor at the resource coordinates
            positionCursor(resource.x_coordinate, resource.y_coordinate);

            // Show results with animation
            resultsSection.classList.add('show');
        };

        floorplanImage.onerror = function() {
            showError('Failed to load floorplan image');
        };

        floorplanImage.src = `/static/floorplans/${floorplan.image_filename}`;
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
});
