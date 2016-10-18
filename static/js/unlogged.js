$(function() {
    $('.company-info h2').on('keyup', '.name', function() {
        $('.invoice__branding h2').text($(this).val());
    });

    $('.company-info').on('click', '#create-tax .add-button', function() {
        return;
    });
});
