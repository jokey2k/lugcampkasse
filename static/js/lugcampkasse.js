(function() {
  var global = this;

  var lib = global.lugcampkasse = {
    urlRoot : '/',
    localbill : Array(),
    socket:'',

    connectSocket: function() {
        lib.socket = io.connect('http://' + document.domain + ':' + location.port);
    },

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

    subscribeNewCustomer : function(cashierCode) {
      lib.connectSocket();
      lib.socket.emit("new_customer_subscribe", cashierCode)
      lib.socket.on("cashier_new_customer", function(data) {
        window.location = "/" + data.code + "/new_bill";
      });
    },

    subscribeScannedVoucher : function(cashierCode) {
      lib.connectSocket();
      lib.socket.emit("scanned_voucher_subscribe", cashierCode)
      lib.socket.on("cashier_scanned_voucher", function(data) {
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
        lib.connectSocket();
        lib.socket.on("new_bill", function(data) {
          window.location.reload();
        });
      }
    );
  });
})();
