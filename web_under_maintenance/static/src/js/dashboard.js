odoo.define('web_under_maintenance.DashboardShare', function (require) {
    "use strict";

    var DashboardShare = require('web_settings_dashboard').DashboardShare;

    return DashboardShare.include({

        init: function (parent, data) {
            this._super.apply(this, arguments);
            var redirect_url = window.location.pathname;
            this.redirect_url = redirect_url.concat(window.location.hash);
        }

    });

});