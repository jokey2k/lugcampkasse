(function() {
  var global = this;

  var jug = new Juggernaut();

  var lib = global.lugcampkasse = {
    urlRoot : '/',
    jug : jug,

    autoHideFlashes : function() {
      var flashes = $('p.flash:visible').hide();
      if (flashes.length) {
        flashes.slideDown('fast');
        window.setTimeout(function() {
          flashes.slideUp('slow');
        }, 5000);
      }
    },

    flash : function(message) {
      $('<p class=flash></p>')
        .append(message)
        .hide()
        .insertAfter('ul.nav')
        .slideDown('fast');
    },

    subscribeUpdatedBalance : function(userCode) {
      jug.subscribe('updated-balance:' + userCode, function(data) {
        $('span#balance').text(data.balance);
        $('span#liveupdated').text(' (' + data.updated_on + ')');
        $('.bills').hide();
      });
    },

    subscribeNewCustomer : function(cashierCode) {
      jug.subscribe('new-customer:' + cashierCode, function(data) {
        window.location = "/" + data.code;
      });
    },

    subscribeScannedVoucher : function(cashierCode) {
      jug.subscribe('scanned-voucher:' + cashierCode, function(data) {
        $('#vouchercodefield')[0].value = data.code;
        document.forms[0].submit();
      });
    }
  };


  $(function() {
    /* animate the server side flashes a bit */
    lib.autoHideFlashes();
  });
})();
