/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2025 Heikki Toivonen
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

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

    // Helper function to get headers with CSRF token
    function getHeaders(includeContentType = true) {
        const headers = {
            'X-CSRFToken': csrfToken
        };
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        return headers;
    }

    // State
    let currentFloorplan = null;
    let floorplans = [];
    let resources = [];
    let clickCoordinates = { x: null, y: null };

    // DOM Elements
    const floorplanForm = document.getElementById('floorplanForm');
    const resourceForm = document.getElementById('resourceForm');
    const floorplansList = document.getElementById('floorplansList');
    const resourcesList = document.getElementById('resourcesList');
    const floorplanViewer = document.getElementById('floorplanViewer');
    const resourceFloorplanSelect = document.getElementById('resourceFloorplan');
    const coordXDisplay = document.getElementById('coordX');
    const coordYDisplay = document.getElementById('coordY');
    const resourceXInput = document.getElementById('resourceX');
    const resourceYInput = document.getElementById('resourceY');
    const editingResourceId = document.getElementById('editingResourceId');
    const resourceFormTitle = document.getElementById('resourceFormTitle');
    const resourceSubmitBtn = document.getElementById('resourceSubmitBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');

    // Initialize
    loadFloorplans();
    loadResources();

    // Event Listeners
    floorplanForm.addEventListener('submit', handleFloorplanUpload);
    resourceForm.addEventListener('submit', handleResourceCreate);
    cancelEditBtn.addEventListener('click', cancelEdit);
    document.getElementById('resourceType').addEventListener('change', handleResourceTypeChange);

    // Load all floorplans
    function loadFloorplans() {
        fetch('/api/floorplans')
            .then(response => response.json())
            .then(data => {
                floorplans = data;
                renderFloorplansList();
                populateFloorplanSelect();
            })
            .catch(error => {
                showToast('Error loading floorplans', 'error');
                console.error(error);
            });
    }

    // Load all resources
    function loadResources() {
        fetch('/api/resources')
            .then(response => response.json())
            .then(data => {
                resources = data;
                renderResourcesList();
                if (currentFloorplan) {
                    renderFloorplanWithResources();
                }
            })
            .catch(error => {
                showToast('Error loading resources', 'error');
                console.error(error);
            });
    }

    // Render floorplans list
    function renderFloorplansList() {
        if (floorplans.length === 0) {
            floorplansList.innerHTML = '<p class="loading">No floorplans yet</p>';
            return;
        }

        floorplansList.innerHTML = floorplans.map(fp => `
            <div class="list-item" data-id="${escapeHtml(fp.id)}">
                <div class="list-item-info">
                    <strong>${escapeHtml(fp.name)}</strong>
                    <small>${escapeHtml(fp.image_filename)}</small>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-edit" onclick="viewFloorplan(${escapeHtml(fp.id)})">View</button>
                    <button class="btn btn-danger" onclick="deleteFloorplan(${escapeHtml(fp.id)})">Delete</button>
                </div>
            </div>
        `).join('');
    }

    // Render resources list
    function renderResourcesList() {
        if (resources.length === 0) {
            resourcesList.innerHTML = '<p class="loading">No resources yet</p>';
            return;
        }

        resourcesList.innerHTML = resources.map(res => {
            const floorplan = floorplans.find(fp => fp.id === res.floorplan_id);
            return `
                <div class="list-item" data-id="${escapeHtml(res.id)}">
                    <div class="list-item-info">
                        <strong>${escapeHtml(res.name)}</strong>
                        <small>${escapeHtml(res.type)} | ${escapeHtml(floorplan ? floorplan.name : 'Unknown')} | (${escapeHtml(res.x_coordinate)}, ${escapeHtml(res.y_coordinate)})</small>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-edit" onclick="editResource(${escapeHtml(res.id)})">Edit</button>
                        <button class="btn btn-danger" onclick="deleteResource(${escapeHtml(res.id)})">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Populate floorplan select dropdown
    function populateFloorplanSelect() {
        const options = floorplans.map(fp =>
            `<option value="${escapeHtml(fp.id)}">${escapeHtml(fp.name)}</option>`
        ).join('');
        resourceFloorplanSelect.innerHTML = '<option value="">-- Select a floorplan --</option>' + options;

        // Auto-select current floorplan if viewing one
        if (currentFloorplan) {
            resourceFloorplanSelect.value = currentFloorplan.id;
        }
    }

    // Handle floorplan upload
    function handleFloorplanUpload(e) {
        e.preventDefault();

        const formData = new FormData(floorplanForm);

        fetch('/api/floorplans', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Upload failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                showToast('Floorplan uploaded successfully!', 'success');
                floorplanForm.reset();
                loadFloorplans();
            })
            .catch(error => {
                showToast(error.message, 'error');
            });
    }

    // Handle resource type change to show/hide metadata fields
    function handleResourceTypeChange(e) {
        const resourceType = e.target.value;

        // Hide all metadata fields
        document.querySelectorAll('.metadata-fields').forEach(el => {
            el.style.display = 'none';
        });

        // Show relevant metadata fields based on type
        if (resourceType === 'room') {
            document.getElementById('roomFields').style.display = 'block';
        } else if (resourceType === 'printer') {
            document.getElementById('printerFields').style.display = 'block';
        } else if (resourceType === 'person') {
            document.getElementById('personFields').style.display = 'block';
        } else if (resourceType === 'bathroom') {
            document.getElementById('bathroomFields').style.display = 'block';
        }
    }

    // Handle resource creation/update
    function handleResourceCreate(e) {
        e.preventDefault();

        if (!clickCoordinates.x || !clickCoordinates.y) {
            showToast('Please click on the floorplan to set coordinates', 'error');
            return;
        }

        const formData = new FormData(resourceForm);
        const resourceType = formData.get('type');
        const data = {
            name: formData.get('name'),
            type: resourceType,
            x_coordinate: clickCoordinates.x,
            y_coordinate: clickCoordinates.y,
            floorplan_id: parseInt(formData.get('floorplan_id'))
        };

        // Add type-specific metadata
        if (resourceType === 'room') {
            data.room_number = formData.get('room_number');
            data.room_type = formData.get('room_type');
            const capacity = formData.get('capacity');
            data.capacity = capacity ? parseInt(capacity) : null;
        } else if (resourceType === 'printer') {
            data.printer_name = formData.get('printer_name');
            data.color_type = formData.get('color_type');
            data.printer_model = formData.get('printer_model');
        } else if (resourceType === 'person') {
            data.email = formData.get('email');
            data.title = formData.get('title');
        } else if (resourceType === 'bathroom') {
            data.gender_type = formData.get('gender_type');
        }

        const resourceId = editingResourceId.value;
        const isEditing = resourceId !== '';
        const url = isEditing ? `/api/resources/${resourceId}` : '/api/resources';
        const method = isEditing ? 'PUT' : 'POST';

        fetch(url, {
            method: method,
            headers: getHeaders(),
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || (isEditing ? 'Update failed' : 'Creation failed'));
                    });
                }
                return response.json();
            })
            .then(data => {
                showToast(isEditing ? 'Resource updated successfully!' : 'Resource created successfully!', 'success');
                cancelEdit();
                loadResources();
            })
            .catch(error => {
                showToast(error.message, 'error');
            });
    }

    // Edit resource
    window.editResource = function(resourceId) {
        const resource = resources.find(r => r.id === resourceId);
        if (!resource) return;

        // Populate form
        document.getElementById('resourceName').value = resource.name;
        document.getElementById('resourceType').value = resource.type;
        document.getElementById('resourceFloorplan').value = resource.floorplan_id;
        editingResourceId.value = resourceId;

        // Show appropriate metadata fields and populate them
        handleResourceTypeChange({ target: { value: resource.type } });

        // Populate type-specific metadata
        if (resource.type === 'room') {
            if (resource.room_number) document.getElementById('roomNumber').value = resource.room_number;
            if (resource.room_type) document.getElementById('roomType').value = resource.room_type;
            if (resource.capacity) document.getElementById('capacity').value = resource.capacity;
        } else if (resource.type === 'printer') {
            if (resource.printer_name) document.getElementById('printerName').value = resource.printer_name;
            if (resource.color_type) document.getElementById('colorType').value = resource.color_type;
            if (resource.printer_model) document.getElementById('printerModel').value = resource.printer_model;
        } else if (resource.type === 'person') {
            if (resource.email) document.getElementById('email').value = resource.email;
            if (resource.title) document.getElementById('title').value = resource.title;
        } else if (resource.type === 'bathroom') {
            if (resource.gender_type) document.getElementById('genderType').value = resource.gender_type;
        }

        // Set coordinates
        clickCoordinates = { x: resource.x_coordinate, y: resource.y_coordinate };
        resourceXInput.value = resource.x_coordinate;
        resourceYInput.value = resource.y_coordinate;
        coordXDisplay.textContent = resource.x_coordinate;
        coordYDisplay.textContent = resource.y_coordinate;

        // Update UI
        resourceFormTitle.textContent = 'Edit Resource';
        resourceSubmitBtn.textContent = 'Update Resource';
        cancelEditBtn.style.display = 'inline-block';

        // Load the floorplan to show current position
        viewFloorplan(resource.floorplan_id);

        // Scroll to form
        resourceForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    // Cancel edit mode
    function cancelEdit() {
        resourceForm.reset();
        editingResourceId.value = '';
        clickCoordinates = { x: null, y: null };
        coordXDisplay.textContent = '--';
        coordYDisplay.textContent = '--';
        resourceXInput.value = '';
        resourceYInput.value = '';
        resourceFormTitle.textContent = 'Create Resource';
        resourceSubmitBtn.textContent = 'Create Resource';
        cancelEditBtn.style.display = 'none';
    }

    // View floorplan
    window.viewFloorplan = function(floorplanId) {
        currentFloorplan = floorplans.find(fp => fp.id === floorplanId);
        if (!currentFloorplan) return;

        resourceFloorplanSelect.value = floorplanId;
        renderFloorplanWithResources();
    };

    // Render floorplan with resources
    function renderFloorplanWithResources() {
        if (!currentFloorplan) return;

        // Filter resources based on edit mode
        let floorplanResources;
        const editingId = editingResourceId.value;

        if (editingId) {
            // In edit mode: show only the resource being edited
            floorplanResources = resources.filter(r => r.id === parseInt(editingId));
        } else {
            // Not editing: show all resources on this floorplan
            floorplanResources = resources.filter(r => r.floorplan_id === currentFloorplan.id);
        }

        // Sanitize filename to prevent directory traversal
        const sanitizedFilename = currentFloorplan.image_filename.replace(/[^a-zA-Z0-9._-]/g, '_');

        floorplanViewer.innerHTML = `
            <h3 style="margin-bottom: 15px; color: #555;">${escapeHtml(currentFloorplan.name)}</h3>
            <div class="floorplan-image-container" id="floorplanContainer">
                <img src="/static/floorplans/${sanitizedFilename}"
                     alt="${escapeHtml(currentFloorplan.name)}"
                     id="floorplanImg"
                     style="display: block;">
                ${floorplanResources.map(res => `
                    <div class="resource-marker"
                         style="left: ${escapeHtml(res.x_coordinate)}px; top: ${escapeHtml(res.y_coordinate)}px;"
                         title="${escapeHtml(res.name)} (${escapeHtml(res.type)})"
                         data-resource-id="${escapeHtml(res.id)}">
                    </div>
                `).join('')}
            </div>
        `;

        // Wait for image to load, then add click handler
        const img = document.getElementById('floorplanImg');
        const container = document.getElementById('floorplanContainer');

        // Remove any existing click handlers to avoid duplicates
        const newContainer = container.cloneNode(true);
        container.parentNode.replaceChild(newContainer, container);

        const finalImg = document.getElementById('floorplanImg');
        const finalContainer = document.getElementById('floorplanContainer');

        // Add click handler after image loads
        if (finalImg.complete) {
            setupClickHandler(finalContainer, finalImg);
        } else {
            finalImg.onload = function() {
                setupClickHandler(finalContainer, finalImg);
            };
        }
    }

    // Setup click handler for floorplan
    function setupClickHandler(container, img) {
        container.addEventListener('click', function(e) {
            // Don't process clicks on markers
            if (e.target.classList.contains('resource-marker')) {
                return;
            }

            // Get the image bounds
            const rect = img.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);

            // Make sure click is within image bounds
            if (x < 0 || y < 0 || x > img.width || y > img.height) {
                return;
            }

            clickCoordinates = { x, y };
            resourceXInput.value = x;
            resourceYInput.value = y;
            coordXDisplay.textContent = x;
            coordYDisplay.textContent = y;

            // Show temporary marker
            const existingTemp = container.querySelector('.temp-marker');
            if (existingTemp) {
                existingTemp.remove();
            }

            const tempMarker = document.createElement('div');
            tempMarker.className = 'temp-marker';
            tempMarker.style.left = `${x}px`;
            tempMarker.style.top = `${y}px`;
            container.appendChild(tempMarker);

            showToast(`Coordinates set: (${x}, ${y})`, 'success');
        });
    }

    // Delete floorplan
    window.deleteFloorplan = function(floorplanId) {
        if (!confirm('Are you sure you want to delete this floorplan? All associated resources will also be deleted.')) {
            return;
        }

        fetch(`/api/floorplans/${floorplanId}`, {
            method: 'DELETE',
            headers: getHeaders(false)
        })
            .then(response => {
                if (response.ok) {
                    showToast('Floorplan deleted successfully!', 'success');
                    if (currentFloorplan && currentFloorplan.id === floorplanId) {
                        currentFloorplan = null;
                        floorplanViewer.innerHTML = '<p class="placeholder">Select a floorplan to view and place resources</p>';
                    }
                    loadFloorplans();
                    loadResources();
                } else {
                    throw new Error('Delete failed');
                }
            })
            .catch(error => {
                showToast('Error deleting floorplan', 'error');
            });
    };

    // Delete resource
    window.deleteResource = function(resourceId) {
        if (!confirm('Are you sure you want to delete this resource?')) {
            return;
        }

        fetch(`/api/resources/${resourceId}`, {
            method: 'DELETE',
            headers: getHeaders(false)
        })
            .then(response => {
                if (response.ok) {
                    showToast('Resource deleted successfully!', 'success');
                    loadResources();
                } else {
                    throw new Error('Delete failed');
                }
            })
            .catch(error => {
                showToast('Error deleting resource', 'error');
            });
    };

    // Show toast notification
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Auto-load floorplan when selecting in resource form
    resourceFloorplanSelect.addEventListener('change', function() {
        const floorplanId = parseInt(this.value);
        if (floorplanId) {
            viewFloorplan(floorplanId);
        }
    });
});
