$(document).ready(function(){function a(){$(".search").val(""),t.search()}$("a[href*=#]:not([href=#])").click(function(){var a=$(this.hash),e=this.hostname,t=location.hostname,s=this.pathname.replace(/^\//,""),o=location.pathname.replace(/^\//,"");return a.length||(a=$("[name="+this.hash.slice(1)+"]")),!a.length||e!==t&&s!==o||($("html, body").animate({scrollTop:a.offset().top},1e3),!1)}),$(".js-open-modal").click(function(){$(".js-target-modal").addClass("js-active"),$("#overlay").addClass("js-active"),$("body").addClass("js-body-modal-active")}),$(".js-close-modal").click(function(){$(".js-target-modal").removeClass("js-active"),$("#overlay").removeClass("js-active"),$("body").removeClass("js-body-modal-active")}),$(".js-close-sticky").click(function(){$(".js-target-sticky").removeClass("js-active")}),$(".js-trigger-search").click(function(a){a.preventDefault(),$(this).parent().addClass("js-active"),$("#overlay").addClass("js-active")}),$(".js-open-table-search").click(function(a){a.preventDefault(),$(this).parent().siblings(".table-sortable__search").toggleClass("table-sortable__search--active")}),$(".js-trigger-menu").click(function(a){$(this).next().addClass("js-active-menu"),$(".js-overlay").addClass("js-active")}),$("#overlay").click(function(){$(".js-active").removeClass("js-active"),$(".js-active-menu").removeClass("js-active-menu")}),$(".slider").slick({arrows:!0,draggable:!1,swipeToSlide:!0,autoplay:!0,autoplaySpeed:3e3,responsive:[{breakpoint:800,settings:{draggable:!0}}]}),$(window).scroll(function(){var a=$(window).scrollTop(),e=$(".table-sortable"),t=e.offset().top;a>=t?e.addClass("table-sortable--fixed"):e.removeClass("table-sortable--fixed")});var e={valueNames:["company__name","company__category","company__type","company__founded","company__location","company__last-update"]},t=new List("company_data",e);$(".search").keyup(function(){if(console.log(this),"company__name--input"==this.id){var a=$(this).val();console.log(this),t.search(a,["company__name"])}else if("company__location--input"==this.id){var a=$(this).val();t.search(a,["company__location"])}}),$(".js-open-table-search").on("click",function(a){$($(this).attr("data-target")).focus()});var s=$(".table-sortable__search").find("button[type='submit']");s.on("click",function(e){e.preventDefault(),$(this).parent().hasClass("table-sortable__search--active")&&($(this).parent().removeClass("table-sortable__search--active"),a())}),$("body").keyup(function(e){"27"==e.keyCode&&($(this).parent().find(".table-sortable__search").removeClass("table-sortable__search--active"),a())});var o=$(".table-sortable__control > i:contains('keyboard_arrow_down')");o.on("click",function(){"keyboard_arrow_down"==$(this).text()?$(this).text("keyboard_arrow_up"):$(this).text("keyboard_arrow_down")})});