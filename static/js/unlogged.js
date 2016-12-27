$(function() {
  $('.company-info h2').on('keyup', '.name', function() {
    $('.invoice__branding h2').text($(this).val());
  });

  $('body').on('submit', '#upload-timesheet', function (e) {
    var $input = $(this).children('input[type=file]');

    if ($input[0].files.length) {
      var onComplete = function(results, file) {
        var chunk = 25;  // Number of rows that fit one page
        var total = 0;
        var slice;
        var $page;
        var $br;

        for (var i = 0; i < results.data.length; i += chunk) {
          slice = results.data.slice(i, i + chunk);
          $page = $('.js-invoice.hidden').clone();
          $br = $('.js-page-break.hidden').clone();

          slice.forEach(function(row, index) {
            if (index && row.length === 14) {
              var $tr = '<tr>';

              $tr += '<td class="description">' + row[5];
              $tr += '<td class="start">' + row[9];
              $tr += '<td class="duration">' + row[11];
              $tr += '<td class="amount">' + row[13];

              total += parseFloat(row[13]);
              console.log(total)

              $page.find('.timesheet tbody').append($tr);
            }
          });

          $('#js-dinamic-content').append($br.removeClass('hidden'));
          $('#js-dinamic-content').append($page.removeClass('hidden'));
        }

        if (total) {
          $('.invoice__amount').text('$ ' + total.toFixed(2));
        }

        $input.val('');
      };

      $input.parse({config: {complete: onComplete}});
    }

    return false;
  });
});
