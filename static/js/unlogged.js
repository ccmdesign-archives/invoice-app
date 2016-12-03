$(function() {
    $('.company-info h2').on('keyup', '.name', function() {
        $('.invoice__branding h2').text($(this).val());
    });

    $('.company-info').on('click', '#create-tax .add-button', function() {
        return;
    });

    $('.controls__button i').click(function () { export1(); });


    $('body').on('submit', '#upload-timesheet', function (e) {
        var $inp = $(this).children('input[type=file]');

        e.preventDefault();

        if ($inp[0].files.length) {
            $inp.parse({
                config: {
                    complete: function(results, file) {
                        var total = 0;

                        results.data.forEach(function (row, idx) {
                            if (idx && row.length == 14) {
                                var html = '<tr>';

                                html += '<td class="description">' + row[5] + '</td>';
                                html += '<td class="start">' + row[11] + '</td>';
                                html += '<td class="duration">' + row[1] + '</td>';
                                html += '<td class="amount">' + row[13] + '</td>';

                                html += '</tr>';
                                total += parseFloat(row[13]);

                                $('.timesheet tbody').append(html);
                            }
                        });

                        if (total) {
                            $('.invoice__amount').text(total);
                        }

                        $('.page-break, .invoice').removeClass('hidden');
                    }
                }
            });
        }

        return false;
    });
});

function export1() {
    $('body').animate({ scrollTop: 0 }, 'slow', function () {
        var pdf = new jsPDF('p', 'cm', [29, 21]);

        pdf.addHTML($('.invoice').eq(0)[0], 0, 0, function () {
            if ($('.timesheet').length) {
                pdf.addPage();
                pdf.setPage(2);

                pdf.addHTML($('.invoice').eq(1)[0], 0, 0, function () {
                    pdf.save('invoice' + $('.edit-invoice-input').val() + '.pdf');
                });

            } else {
                pdf.save('invoice' + $('.edit-invoice-input').val() + '.pdf');
            }
        });
    });
}

function export2() {
    $('body').animate({ scrollTop: 0 }, 'slow', function () {
        var pdf = new jsPDF('p', 'cm', [29, 21]);

        html2canvas($('.invoice').eq(0)[0], {
            onrendered: function (canvas) {
                pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 21, 29);

                if ($('.timesheet').length) {
                    html2canvas($('.invoice').eq(1)[0], {
                        onrendered: function (canvas) {
                            pdf.addPage();
                            pdf.setPage(2);

                            pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, 0, 21, 29);
                            pdf.save('invoice' + $('.edit-invoice-input').val() + '.pdf');
                        }
                    });

                } else {
                    pdf.save('invoice' + $('.edit-invoice-input').val() + '.pdf');
                }
            }
        });
    });
}

function export3() {
    function page1(img) {
        pdf = new jsPDF('p', 'px', [img.height, img.width]);

        pdf.addImage(img, 0, 0, img.width, img.height);

        if ($('.timesheet').length) {
            elem2page($('.invoice').eq(1)[0], page2);
        }
    }

    function page2(img) {
        pdf.addPage();
        pdf.setPage(2);
        pdf.addImage(img, 0, 0, img.width, img.height);

        pdf.save('invoice' + $('.edit-invoice-input').val() + '.pdf');
    }

    function elem2page(html, callback) {
        html2canvas(html, {
            onrendered: function (canvas) {
                canvas.toBlob(function blobToImg(blob) {
                    var img = new Image();
                    var urlCreator = window.URL || window.webkitURL;

                    img.src = urlCreator.createObjectURL(blob);
                    img.onload = function () { callback(img); };
                });
            }
        });
    }

    var pdf = null;

    $('body').animate({ scrollTop: 0 }, 'slow', function () {
        elem2page($('.invoice').eq(0)[0], page1);
    });
}
