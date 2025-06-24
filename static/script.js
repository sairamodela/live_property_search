let dataTable;
$(document).ready(function () {
  dataTable = $('#resultsTable').DataTable({
    pageLength: 25,
    order: [[5, 'asc']],
    columnDefs: [
      {
        targets: 5,
        render: function (data, type) {
          if (type === 'display' && data) {
            return '$' + parseFloat(data).toLocaleString();
          }
          return data;
        }
      },
      {
        targets: 9,
        render: function (data, type) {
          if (type === 'display' && data) {
            return parseFloat(data).toLocaleString() + ' sq ft';
          }
          return data;
        }
      }
    ]
  });

  $('#searchForm').on('submit', function (e) {
    e.preventDefault();
    performSearch();
  });

  $('#searchForm').on('reset', function () {
    setTimeout(() => {
      $('#resultsSection').hide();
      dataTable.clear().draw();
    }, 100);
  });

  $('#searchInput').focus();
});

function performSearch() {
  const searchValue = $('#searchInput').val().trim();
  if (!searchValue && !$('#advancedFilters').hasClass('show')) {
    alert('Please enter a search term or use advanced filters.');
    return;
  }

  $('#resultsSection').hide();
  $('.loading').show();
  const $buttons = $('#searchForm').find('button');
  $buttons.prop('disabled', true);

  const formData = {
    search: searchValue,
    min_price: $('#min_price').val(),
    max_price: $('#max_price').val(),
    min_bedrooms: $('#min_bedrooms').val(),
    property_type: $('#property_type').val()
  };

  $.ajax({
    url: '/api/search',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify(formData),
    success: function (response) {
      if (response.success) {
        displayResults(response.data);
      } else {
        alert('Error: ' + response.error);
      }
    },
    error: function (xhr, status, error) {
      alert('Error searching properties: ' + error);
    },
    complete: function () {
      $('.loading').hide();
      $buttons.prop('disabled', false);
    }
  });
}

function displayResults(data) {
  dataTable.clear();

  if (data.length === 0) {
    $('#resultsSection').show();
    $('#resultsBody').html('<tr><td colspan="11" class="text-center">No properties found matching your criteria.</td></tr>');
    return;
  }

  data.forEach(function (property) {
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
      `<button class="btn btn-sm btn-info" onclick="viewProperty('${property.property_id}')"><i class="bi bi-eye"></i> View</button>`
    ];
    dataTable.row.add(row);
  });

  dataTable.draw();
  $('#resultsSection').show();
}

function viewProperty(propertyId) {
  $('#propertyDetails').html('<div class="text-center p-4"><div class="spinner-border text-primary"></div></div>');
  $('#propertyModal').modal('show');

  $.ajax({
    url: `/api/property/${propertyId}`,
    method: 'GET',
    success: function (response) {
      if (response.success && response.data) {
        displayPropertyDetails(response.data);
      } else {
        $('#propertyDetails').html('<div class="alert alert-danger">Error loading property details.</div>');
      }
    },
    error: function (xhr, status, error) {
      $('#propertyDetails').html('<div class="alert alert-danger">Error fetching property details: ' + error + '</div>');
    }
  });
}