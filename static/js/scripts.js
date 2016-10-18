$(function() {
    $('.client-info').on('change', 'input', function() {
        function valid_response(data, state, xhr) {
            $('.client-info').html(data);
        }

        if (!$('.autocomplete-suggestions').is(':visible') && $('#client-form .name').val()) {
            var $form = $('#client-form'),
                $resp = null;

            $resp = $.post($form.attr('action'), $form.serialize());

            $resp.done(valid_response).fail(function(data, state, xhr) {
                if (xhr == 'BAD REQUEST')
                    console.log('Bad request.');

                else
                    console.log('Server error.');
            });
        }
    });

    $('.company-info').on('change', '#company-form input', function() {
        function valid_response(data, state, xhr) {
            $('.company-info').html(data);

            $('.invoice__branding h2').text($('#company-form h2 input').val());
        }

        if (!$('.autocomplete-suggestions').is(':visible') && $('#company-autocomplete').val()) {
            var $form = $('#company-form'),
                $resp = null;

            $resp = $.post($form.attr('action'), $form.serialize());

            $resp.done(valid_response).fail(function(data, state, xhr) {
                if (xhr == 'BAD REQUEST')
                    console.log('Bad request.');

                else
                    console.log('Server error.');
            });
        }
    });

    $('.company-info').on('click', '#create-tax .add-button', function() {
        function valid_response(data, state, xhr) {
            $('.tax-info').html(data);
        }

        if ($('#create-tax .name').val()) {
            var $objc = $('#create-tax'),
                $resp = null,
                data = {};

            $objc.find('input').each(function() {
                var $inp = $(this);

                data[$inp.attr('name')] = $inp.val();
            });

            $resp = $.post($objc.data('url'), {data: JSON.stringify(data)});

            $resp.done(valid_response).fail(function(data, state, xhr) {
                if (xhr == 'BAD REQUEST')
                    console.log('Bad request.');

                else
                    console.log('Server error.');
            });
        }
    });

    $('.company-info').on('blur', '.edit-tax input', function() {
        function valid_response(data, state, xhr) {
            $('.tax-info').html(data);
        }

        var $tr = $(this).parents('tr');

        if ($tr.find('.name').val()) {
            var $resp = null,
                data = {};

            $tr.find('input').each(function() {
                var $inp = $(this);

                data[$inp.attr('name')] = $inp.val();
            });

            $resp = $.post($tr.data('url'), {data: JSON.stringify(data)});

            $resp.done(valid_response).fail(function(data, state, xhr) {
                if (xhr == 'BAD REQUEST')
                    console.log('Bad request.');

                else
                    console.log('Server error.');
            });
        }
    });

    $('body').on('blur', '.edit-invoice-input', function() {
        function valid_response(data, state, xhr) {
        }

        var $resp = null,
            data = {};

        $('.edit-invoice-input').each(function() {
            var $inp = $(this);

            data[$inp.attr('name')] = $inp.val();
        });

        $resp = $.post($('.invoice').data('url'), {data: JSON.stringify(data)});

        $resp.done(valid_response).fail(function(data, state, xhr) {
            if (xhr == 'BAD REQUEST')
                console.log('Bad request.');

            else
                console.log('Server error.');
        });
    });

    $('body').on('click', '.list td:first-of-type i', function() {
        function valid_response(data, state, xhr) {
            $('.list--opened tbody').html(data.open);
            $('.list--archived tbody').html(data.paid);

            $('.widget__primary-value.open').text(data.open.length);
            $('.widget__primary-value.paid').text(data.paid.length);
        }

        var $resp = null,
            data = {};

        data.paid = $(this).text() == 'check_box_outline_blank' ? true : false;

        $resp = $.post($(this).parents('tr').data('url'), {data: JSON.stringify(data)});

        $resp.done(valid_response).fail(function(data, state, xhr) {
            if (xhr == 'BAD REQUEST')
                console.log('Bad request.');

            else
                console.log('Server error.');
        });
    });

    var opts1 = {
        serviceUrl: $('#company-autocomplete').data('url'),
        dataType: 'json',
        paramName: 'q',
        deferRequestBy: 500,
        nocache: true,
        minChars: 3,
        triggerSelectOnValidInput: false,
        onSelect: function(item) {
            $('.company-info').html(item.data);
            $('#company-autocomplete').autocomplete(opts1);
        }
    };

    $('#company-autocomplete').autocomplete(opts1);

    var opts2 = {
        serviceUrl: $('#client-autocomplete').data('url'),
        dataType: 'json',
        paramName: 'q',
        deferRequestBy: 500,
        nocache: true,
        minChars: 3,
        triggerSelectOnValidInput: false,
        onSelect: function(item) {
            $('.client-info').html(item.data);
            $('#client-autocomplete').autocomplete(opts1);
        }
    };

    $('#client-autocomplete').autocomplete(opts2);
});
