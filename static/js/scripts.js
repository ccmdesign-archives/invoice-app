$(function () {
  var subTotal = 0;
  var total = 0;

  if ($('.invoice__amount__real__input').val()) {
    subTotal = parseFloat($('.invoice__amount__real__input').val());
  }

  // Home
  // ----

  $('body').on('click', '.list td:first-of-type i', function () {
    function valid_response(data) {
      $('.list--opened tbody').html(data.open);
      $('.list--archived tbody').html(data.paid);

      $('.widget__primary-value.open').text(data.open.length);
      $('.widget__primary-value.paid').text(data.paid.length);
    }

    var $resp = null,
        data = {};

    data.paid = $(this).text() == 'check_box_outline_blank' ? true : false;

    $resp = $.post($(this).parents('tr').data('url'), {data: JSON.stringify(data)});

    $resp.done(valid_response).fail(function (data, state, xhr) {
      if (xhr == 'BAD REQUEST')
        console.log('Bad request.');

      else
        console.log('Server error.');
    });
  });

  // Invoice
  // -------

  // Client autocomplete
  var opts = {
    serviceUrl: $('#client-autocomplete').data('url'),
    dataType: 'json',
    paramName: 'q',
    deferRequestBy: 100,
    nocache: true,
    minChars: 0,
    triggerSelectOnValidInput: false,
    onSelect: function (item) {
      $('#js-client-id').val(item.data._id);
      $('#js-client-vendor-number').val(item.data.vendor_number);
      $('#js-client-contact').val(item.data.contact);
      $('#js-client-email').val(item.data.email);
      $('#js-client-phone').val(item.data.phone);
      $('#js-client-address').text(item.data.address);
    }
  };

  $('#client-autocomplete').autocomplete(opts);

  // Submits invoice form
  $('#js-save-invoice-button').click(function() {
    $('#js-invoice-form').submit();
  });

  // Updates the invoice content with the data from the uploaded CSV file
  $('body').on('click', '#upload-timesheet', function() {
    var $input = $(this).parent().find('input[type=file]');
    subTotal = 0;
    total = 0;

    if ($input[0].files.length) {
      var onComplete = function(results) {
        var chunk = 23;  // Number of rows that fit one page
        var slice;
        var $page;
        var $br;

        $('#js-dinamic-content').html('');

        for (var i = 1; i < results.data.length; i += chunk) {
          slice = results.data.slice(i, i + chunk);
          $page = $('.js-invoice.hidden').clone();
          $br = $('.js-page-break.hidden').clone();

          slice.forEach(function(row) {
            if (row.length === 14) {
              var $tr = '<tr>';

              $tr += '<td class="description">' + row[5];
              $tr += '<td class="start">' + row[9];
              $tr += '<td class="duration">' + row[11];
              $tr += '<td class="amount">' + row[13];

              subTotal += parseFloat(row[13]);

              $page.find('.timesheet tbody').append($tr);
            }
          });

          $('#js-dinamic-content').append($br.removeClass('hidden'));
          $('#js-dinamic-content').append($page.removeClass('hidden'));
        }

        if (subTotal) {
          updateFinalPrice();
        }
      };

      $input.parse({config: {complete: onComplete}});
    }

    return false;
  });

  // Updates the invoice header when company's name is changed
  $('body').on('keyup', '.company-info h2 .name', function() {
    $('.invoice__branding h2').text($(this).val());
  });

  // Updates invoice price when a tax is checked/unchecked
  $('.js-tax').change(function() {
    updateFinalPrice();
  });

  // Applies taxes when invoice value is manually changed
  $('.invoice__amount__input').change(function() {
    subTotal = parseFloat($(this).val());
    updateFinalPrice();
  });

  // Company
  // -------

  // Creates a tax row
  $('#js-add-tax').click(function() {
    var name = $('#js-new-tax-name').val();
    var number = $('#js-new-tax-number').val();
    var value = $('#js-new-tax-value').val();
    var $taxRow = $('<tr>');
    var $row = $(this).closest('tr');

    $taxRow.append($('<td>').append($('<input>').addClass('name base-field small').attr('name', 'tax_name').val(name)));
    $taxRow.append($('<td>').append($('<input>').addClass('base-field small').attr('name', 'tax_number').val(number)));
    $taxRow.append($('<td>').append($('<input>').addClass('base-field small').attr('name', 'tax_value').val(value)));
    $taxRow.append($('<td>').append($('<span>').addClass('tax-control js-delete-tax').append($('<i>').addClass('material-icons').text('close'))));

    $row.before($taxRow);
    $row.find('input').val('');
  });

  // Delete a tax row
  $('.add-gov-registry').on('click', '.js-delete-tax', function() {
    $(this).closest('tr').remove();
  });

  // Auxiliar functions
  // ------------------

  var updateFinalPrice = function() {
    var $inputs = $('.js-tax');
    var taxes = 0;

    $inputs.each(function(i, input) {
      if (input.checked) {
        taxes += parseFloat($(input).data('tax-value'));
      }
    });

    total = subTotal * (1 + taxes);

    if (subTotal && total) {
      $('.invoice__amount__input').val(total.toFixed(2));
      $('.invoice__amount__real__input').val(subTotal.toFixed(2));
    }
  }
});
