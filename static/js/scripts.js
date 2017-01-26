$(function () {

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

  var opts1 = {
    serviceUrl: $('#company-autocomplete').data('url'),
    dataType: 'json',
    paramName: 'q',
    deferRequestBy: 100,
    nocache: true,
    minChars: 0,
    triggerSelectOnValidInput: false,
    onSelect: function (item) {
      $('.company-info').html(item.data);
      $('#company-autocomplete').autocomplete(opts1);
    }
  };

  var opts2 = {
    serviceUrl: $('#client-autocomplete').data('url'),
    dataType: 'json',
    paramName: 'q',
    deferRequestBy: 100,
    nocache: true,
    minChars: 0,
    triggerSelectOnValidInput: false,
    onSelect: function (item) {
      $('.client-info').html(item.data);
      $('#client-autocomplete').autocomplete(opts1);
    }
  };

  $('#company-autocomplete').autocomplete(opts1);
  $('#client-autocomplete').autocomplete(opts2);

  // Updates the invoice header when client's name is changed
  $('.company-info h2').on('keyup', '.name', function() {
    $('.invoice__branding h2').text($(this).val());
  });

  // Updates the client's data on each input change
  $('.client-info').on('change', 'input, textarea', function() {
    if (!$('.autocomplete-suggestions').is(':visible') && $('#client-form .name').val()) {
      var $form = $('#client-form');
      var $resp = null;

      $resp = $.post($form.attr('action'), $form.serialize());

      $resp.done(function(data) {
        $('#client-id').val(data.id);

      }).fail(function(data, state, xhr) {
        if (xhr == 'BAD REQUEST')
          console.log('Bad request.');

        else
          console.log('Server error.');
      });
    }
  });

  // Updates the company's data on each input change
  $('.company-info').on('change', 'input, textarea', function() {
    if (!$('.autocomplete-suggestions').is(':visible') && $('#company-autocomplete').val()) {
      var $form = $('#company-form');
      var $resp = null;

      $resp = $.post($form.attr('action'), $form.serialize());

      $resp.done(function(data) {
        $('#company-id').val(data.id);

      }).fail(function(data, state, xhr) {
        if (xhr == 'BAD REQUEST')
          console.log('Bad request.');

        else
          console.log('Server error.');
      });
    }
  });

  // Creates a tax and apdates the invoice price
  $('.company-info').on('click', '#create-tax .add-button', function() {
    if ($('#create-tax .name').val()) {
      var $objc = $('#create-tax');
      var $resp = null;
      var data = {};

      $objc.find('input').each(function() {
        data[$(this).attr('name')] = $(this).val();
      });

      $resp = $.post($objc.data('url'), {data: JSON.stringify(data)});

      $resp.done(function(data) {
        $('.tax-info').html(data.html);
        $('.invoice__amount').text('$ ' + data.json.total);

      }).fail(function(data, state, xhr) {
        if (xhr == 'BAD REQUEST') {
          console.log('Bad request.');

        } else {
          console.log('Server error.');
        }
      });
    }
  });

  // Updates invoice price when a tax is changed
  $('.company-info').on('blur', '.edit-tax input', function() {
    var $tr = $(this).parents('tr');

    if ($tr.find('.name').val()) {
      var $resp = null;
      var data = {};

      $tr.find('input').each(function () {
        var $inp = $(this);

        data[$inp.attr('name')] = $inp.val();
      });

      $resp = $.post($tr.data('url'), {data: JSON.stringify(data)});

      $resp.done(function(data) {
        $('.tax-info').html(data.html);
        $('.invoice__amount__input').val('$ ' + data.json.total);

      }).fail(function (data, state, xhr) {
        if (xhr == 'BAD REQUEST') {
          console.log('Bad request.');

        } else {
          console.log('Server error.');
        }
      });
    }
  });

  // Updates invoice data: number, services and descrption
  $('body').on('blur', '.edit-invoice-input', function() {
    var $resp = null;
    var data = {};

    $('.edit-invoice-input').each(function() {
      data[$(this).attr('name')] = $(this).val();

      if ($(this).hasClass('js-invoice-number')) {
        $('.js-invoice-number').val($(this).val());
      }
    });

    $resp = $.post($('.invoice').data('url'), {data: JSON.stringify(data)});

    $resp.fail(function (data, state, xhr) {
      if (xhr == 'BAD REQUEST')
        console.log('Bad request.');

      else
        console.log('Server error.');
    });
  });


  // Updates the invoice content with the data from the uploaded CSV file
  $('body').on('submit', '#upload-timesheet', function() {
    function valid_response(data) {
      $('.timesheet-info').html(data.html);
      $('.invoice__amount__input').val('$ ' + data.json.total);
    }

    var $form = $(this);
    var formData = new FormData(this);

    $.ajax({
      url: $form.attr('action'),
      type: 'POST',
      data: formData,
      cache: false,
      success: valid_response,
      contentType: false,
      processData: false
    });

    return false;
  });
});