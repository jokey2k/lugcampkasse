(function() {
  var global = this;

  var jug = new Juggernaut({secure:false});

  var lib = global.lugcampkasse = {
    urlRoot : '/',
    jug : jug,
    localbill : Array(),

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
        window.location = "/" + data.code + "/new_bill";
      });
    },

    subscribeScannedVoucher : function(cashierCode) {
      jug.subscribe('scanned-voucher:' + cashierCode, function(data) {
        $('#vouchercodefield')[0].value = data.code;
        document.forms[0].submit();
      });
    },

    addToBill : function(itemid, itemname, itemprice) {
      // note to self: do not program after 18h of being awake
      // XXX need to optimize later
      lib.localbill.push([itemid, itemname, itemprice]);
      billhtml = $('ul#billed');
      billsum = 0
      billhtml[0].innerHTML = "";
      billitems = Array();
      for (var i = 0; i < lib.localbill.length; i++) {
        itemcost = lib.localbill[i][2] / 100;
        billhtml.append($('<li></li>').text(lib.localbill[i][1] + " (" + itemcost.toFixed(2) + " EUR)"));
        billsum += lib.localbill[i][2];
        billitems.push(lib.localbill[i][0]);
      }
      billsum = billsum / 100;
      $('span#summe').text(billsum.toFixed(2));
      $('input#bill_ids')[0].value = billitems;
    }
  };

  $(function() {
    /* animate the server side flashes a bit */
    lib.autoHideFlashes();

    $('#data').graphy(
      { colors: ['#dd0000', '#dddd00'], yaxis: { label: ' asd' }, xaxis: {mode: "time"}, series: {stack: true, lines: { show: true, fill: true}} },
      function(plot, plotData) {
        jug.subscribe('new-bill', function(data) {
          window.location.reload();
        })
      }
    );
  });
})();
