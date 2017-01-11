$(function() {
  var subTotal = 0;
  var total = 0;

  // Updates the invoice header when client's name is changed
  $('.company-info h2').on('keyup', '.name', function() {
    $('.invoice__branding h2').text($(this).val());
  });

  // Updates invoice number
  $('body').on('blur', '.js-invoice-number', function() {
    $('.js-invoice-number').text($(this).text());
  });

  // Adds a new tax entry and updates the total price
  $('.tax-info .add-button').click(function() {
    var $row = $(this).closest('tr');

    if ($row.find('.js-tax-value').val()) {
      var $table = $row.parent();
      var $tax = $row.clone();

      $row.find('input').val('');

      $tax.find('.add-button').remove();
      $table.prepend($tax);

      if (subTotal) {
        updateFinalPrice();
      }
    }
  });

  // Updates total price when a tax values is changed
  $('.tax-info').on('change', '.js-tax-value', function() {
    // If the row has the "add-button" let the button click handle the update
    if (!$(this).closest('tr').find('.add-button').length) {
      if (subTotal) {
        updateFinalPrice();
      }
    }
  });

  // Updates the invoice content with the data from the uploaded CSV file
  $('body').on('submit', '#upload-timesheet', function() {
    var $input = $(this).children('input[type=file]');

    if ($input[0].files.length) {
      var onComplete = function(results) {
        var chunk = 23;  // Number of rows that fit one page
        var slice;
        var $page;
        var $br;

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

        $input.val('');
      };

      $input.parse({config: {complete: onComplete}});
    }

    return false;
  });

  // Auxiliar functions
  // ------------------

  var updateFinalPrice = function() {
    var $inputs = $('.js-tax-value');
    var taxes = 0;

    $inputs.each(function(i, input) {
      if (input.value) {
        taxes += parseInt(input.value);
      }
    });

    total = subTotal * (1 + taxes / 100);

    $('.invoice__amount input').val('$ ' + total.toFixed(2));
  }
});
