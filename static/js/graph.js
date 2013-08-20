(function(window, $, undefined) {

  jQuery.fn.graphy = function(options, callback) {
    var that = this;

    return that.each(function() {
      var table = $(this)
        , target = $(table.attr('data-graph-target'))
        , data = []
        , ymax = 0
        , xmax = 0;

      table.find('tr').each(function() {
        var tr = $(this)
          , x = parseInt(tr.find('th').first().text(), 10)
          , total = 0;

        tr.find('td').each(function(i) {
          var y = parseInt(this.innerHTML, 10);

          total += y;

          if(typeof(data[i]) === 'undefined') {
            data[i] = [];
          }

          data[i].push([
            x
          , y
          ]);
        });

        ymax = Math.max(ymax, total);
        xmax = Math.max(xmax, x);

      });

      options = $.extend(options, {
        xaxis : {
            ticks: xmax/4
          , max: xmax
          }
        , yaxis: {
            max: ymax
        }
      }, true);

      callback.call(this, $.plot(target, data, options), data);
      table.hide();
    });
  };

}(window, jQuery));