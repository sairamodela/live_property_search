
        let dataTable;
                
                $(document).ready(function() {
                    // Initialize DataTable
                    dataTable = $('#resultsTable').DataTable({
                        pageLength: 25,
                        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                        order: [[5, 'asc']], // Sort by price
                        columnDefs: [
                            {
                                targets: 5, // Price column
                                render: function(data, type, row) {
                                    if (type === 'display' && data) {
                                        return '$' + parseFloat(data).toLocaleString();
                                    }
                                    return data;
                                }
                            },
                            {
                                targets: 9, // Living space column
                                render: function(data, type, row) {
                                                                if (type === 'display' && data) {
                                        return parseFloat(data).toLocaleString() + ' sq ft';
                                    }
                                    return data;
                                }
                            }
                        ]
                    });
                    
                    // Handle form submission
                    $('#searchForm').on('submit', function(e) {
                        e.preventDefault();
                        performSearch();
                    });
                    
                    // Handle reset button
                    $('#searchForm').on('reset', function() {
                        setTimeout(function() {
                            $('#resultsSection').hide();
                            $('#statistics').hide();
                            dataTable.clear().draw();
                        }, 100);
                    });
                    
                    // Focus on search input on page load
                    $('#searchInput').focus();
                });
                
                function performSearch() {
                    // Get search value
                    const searchValue = $('#searchInput').val().trim();
                    
                    if (!searchValue && !$('#advancedFilters').hasClass('show')) {
                        alert('Please enter a search term or use advanced filters.');
                        return;
                    }
                    
                    // Show loading
                    $('.loading').show();
                    $('#resultsSection').hide();
                    $('#statistics').hide();
                    
                    // Get form data
                    const formData = {
                        search: searchValue,
                        min_price: $('#min_price').val(),
                        max_price: $('#max_price').val(),
                        min_bedrooms: $('#min_bedrooms').val(),
                        property_type: $('#property_type').val()
                    };
                    
                    // Make API call
                    $.ajax({
                        url: '/api/search',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify(formData),
                        success: function(response) {
                            $('.loading').hide();
                            
                            if (response.success) {
                                displayResults(response.data);
                                
                                // Display statistics if we have results
                                if (response.data.length > 0) {
                                    displayStatistics(response.data);
                                }
                            } else {
                                alert('Error: ' + response.error);
                            }
                        },
                        error: function(xhr, status, error) {
                            $('.loading').hide();
                            alert('Error searching properties: ' + error);
                        }
                    });
                }
                
                function displayResults(data) {
                    // Clear existing data
                    dataTable.clear();
                    
                    if (data.length === 0) {
                        $('#resultsSection').show();
                        dataTable.draw();
                        alert('No properties found matching your search criteria.');
                        return;
                    }
                    
                    // Add data to table
                    data.forEach(function(property) {
                        const row = [
                            property.property_id || '',
                            property.address || '',
                            property.city || '',
                            property.state || '',
                            property.postcode || '',
                            property.price || 0,
                            property.bedroom_number || 0,
                            property.bathroom_number || 0,
                            property.property_type || '',
                            property.living_space || 0,
                            `<button class="btn btn-sm btn-info" onclick="viewProperty('${property.property_id}')">
                                <i class="bi bi-eye"></i> View
                            </button>`
                        ];
                        dataTable.row.add(row);
                    });
                    
                    dataTable.draw();
                    $('#resultsSection').show();
                }
                
                function displayStatistics(properties) {
                    // Calculate statistics
                    const prices = properties.map(p => p.price).filter(p => p != null && p > 0);
                    const bedrooms = properties.map(p => p.bedroom_number).filter(b => b != null);
                    
                    if (prices.length > 0) {
                        const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
                        const minPrice = Math.min(...prices);
                        const maxPrice = Math.max(...prices);
                        
                        $('#avgPrice').text(Math.round(avgPrice).toLocaleString());
                        $('#priceRange').text(minPrice.toLocaleString() + ' - $' + maxPrice.toLocaleString());
                    } else {
                        $('#avgPrice').text('N/A');
                        $('#priceRange').text('N/A');
                    }
                    
                    if (bedrooms.length > 0) {
                        const avgBedrooms = bedrooms.reduce((a, b) => a + b, 0) / bedrooms.length;
                        $('#avgBedrooms').text(avgBedrooms.toFixed(1));
                    } else {
                        $('#avgBedrooms').text('N/A');
                    }
                    
                    $('#totalProperties').text(properties.length);
                    $('#statistics').show();
                }
                
                function viewProperty(propertyId) {
                    // Show loading in modal
                    $('#propertyDetails').html('<div class="text-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>');
                    $('#propertyModal').modal('show');
                    
                    // Fetch property details
                    $.ajax({
                        url: `/api/property/${propertyId}`,
                        method: 'GET',
                        success: function(response) {
                            if (response.success && response.data) {
                                displayPropertyDetails(response.data);
                            } else {
                                $('#propertyDetails').html('<div class="alert alert-danger">Error loading property details.</div>');
                            }
                        },
                        error: function(xhr, status, error) {
                            $('#propertyDetails').html('<div class="alert alert-danger">Error fetching property details: ' + error + '</div>');
                        }
                    });
                }
                
                function displayPropertyDetails(property) {
                    let html = '<div class="row">';
                    
                    // Basic Information
                    html += '<div class="col-md-6">';
                    html += '<h6 class="text-primary mb-3"><i class="bi bi-info-circle"></i> Basic Information</h6>';
                    html += '<table class="table table-sm">';
                    html += `<tr><td><strong>Property ID:</strong></td><td>${property.property_id || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Address:</strong></td><td>${property.address || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Street Name:</strong></td><td>${property.street_name || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>City:</strong></td><td>${property.city || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>State:</strong></td><td>${property.state || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Postcode:</strong></td><td>${property.postcode || 'N/A'}</td></tr>`;
                    html += '</table>';
                    html += '</div>';
                    
                    // Property Details
                    html += '<div class="col-md-6">';
                    html += '<h6 class="text-primary mb-3"><i class="bi bi-house"></i> Property Details</h6>';
                    html += '<table class="table table-sm">';
                    html += `<tr><td><strong>Price:</strong></td><td class="text-success fw-bold">$${property.price ? property.price.toLocaleString() : 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Bedrooms:</strong></td><td>${property.bedroom_number || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Bathrooms:</strong></td><td>${property.bathroom_number || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Property Type:</strong></td><td>${property.property_type || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Status:</strong></td><td>${property.property_status || 'N/A'}</td></tr>`;
                    html += '</table>';
                    html += '</div>';
                    
                    // Additional Information
                    html += '<div class="col-12 mt-3">';
                    html += '<h6 class="text-primary mb-3"><i class="bi bi-rulers"></i> Additional Information</h6>';
                    html += '<table class="table table-sm">';
                    html += `<tr><td width="200"><strong>Living Space:</strong></td><td>${property.living_space ? property.living_space.toLocaleString() + ' sq ft' : 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Land Space:</strong></td><td>${property.land_space ? property.land_space.toLocaleString() + ' ' + (property.land_space_unit || 'sq ft') : 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Price per Unit:</strong></td><td>${property.price_per_unit ? '$' + property.price_per_unit.toLocaleString() : 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Agency:</strong></td><td>${property.agency_name || 'N/A'}</td></tr>`;
                    html += `<tr><td><strong>Owned by Zillow:</strong></td><td>${property.is_owned_by_zillow ? 'Yes' : 'No'}</td></tr>`;
                    html += `<tr><td><strong>Run Date:</strong></td><td>${property.RunDate || 'N/A'}</td></tr>`;
                    html += '</table>';
                    html += '</div>';
                    
                    // Location Information (if coordinates available)
                    if (property.latitude && property.longitude) {
                        html += '<div class="col-12 mt-3">';
                        html += '<h6 class="text-primary mb-3"><i class="bi bi-geo-alt"></i> Location</h6>';
                        html += '<table class="table table-sm">';
                        html += `<tr><td width="200"><strong>Coordinates:</strong></td><td>${property.latitude}, ${property.longitude}</td></tr>`;
                        html += '</table>';
                        html += '</div>';
                    }
                    
                    // Property URL
                    if (property.property_url) {
                        html += '<div class="col-12 mt-3 text-center">';
                        html += `<a href="${property.property_url}" target="_blank" class="btn btn-primary">
                            <i class="bi bi-box-arrow-up-right"></i> View on Original Site
                        </a>`;
                        html += '</div>';
                    }
                    
                    html += '</div>';
                    
                    $('#propertyDetails').html(html);
                }
                
                // Add enter key support for search
                $('#searchInput').on('keypress', function(e) {
                    if (e.which === 13) {
                        e.preventDefault();
                        $('#searchForm').submit();
                    }
                });
            