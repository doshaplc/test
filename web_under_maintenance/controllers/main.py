# -*- coding: utf-8 -*-

import werkzeug.utils
import odoo
from odoo import http, fields, _
from odoo.exceptions import AccessError
from odoo.addons.web_settings_dashboard.controllers.main import WebSettingsDashboard as WSD
from odoo.addons.web.controllers.main import ensure_db, Session, Home
from odoo.http import request
from odoo.tools import SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

try:
    import simplejson
except ImportError as ex:
    _logger.warning("Can't import 'simplejson' python package. Please, run 'pip install simplejson'")


class SessionMixin(object):

    def check_session(self, db, login, password):
        # Objects
        uid = db and login and password and request.session.authenticate(db, login, password)
        sid = request.httprequest.session.sid
        ir_param_obj = request.env['ir.config_parameter'].sudo()
        # Check maintenance mode and always bypass administrator user
        is_under_maintenance = bool(int(ir_param_obj.get_param('under_maintenance')))
        if uid != SUPERUSER_ID and is_under_maintenance:
            return False
        # Save session if maintenance mode not activated
        self.save_session(uid, sid)
        return True

    def save_session(self, uid, sid):
        # Objects
        now = fields.datetime.now()
        session_obj = request.env['ir.session'].sudo()
        cr = request.env.cr

        # autocommit: our single update request will be performed atomically.
        # (In this way, there is no opportunity to have two transactions
        # interleaving their cr.execute()..cr.commit() calls and have one
        # of them rolled back due to a concurrent access.)
        cr.autocommit(True)

        # Check if session already exists
        sessions = session_obj.search([
            ('session_id', '=', sid),
            ('user_id', '=', uid),
            ('is_logged_in', '=', True),
        ])

        # Create session
        if not sessions:
            values = {
                'user_id': uid,
                'is_logged_in': True,
                'session_id': sid,
                'login_date': now,
            }
            session_obj.create(values)
            cr.commit()


class WebSettingsDashboard(WSD):

    @http.route('/web_settings_dashboard/data', type='json', auth='user')
    def web_settings_dashboard_data(self, **kw):
        result = super(WebSettingsDashboard, self).web_settings_dashboard_data(**kw)
        ir_param = request.env['ir.config_parameter'].sudo()
        if 'share' in result:
            result["share"]["under_maintenance"] = bool(eval(ir_param.get_param('under_maintenance')))
            result["share"]["show_under_maintenance"] = True if request.uid == SUPERUSER_ID else False
        return result


class WebUnderMaintenance(http.Controller):

    @http.route(['/ajax/session/'], type='http', auth="public", website=True)
    def web_check_session(self, *args, **kwargs):
        json_result = []
        # Double check session
        ir_session_obj = request.env['ir.session'].sudo()
        session_history = ir_session_obj.search([
            ('session_id', '=', request.session.sid),
            ('user_id', '=', request.session.uid),
        ])
        if session_history and not session_history.is_logged_in:
            request.session.logout()
        # Check current user's session
        if request.session.uid is None:
            json_result.append({'result': 'true'})
        else:
            json_result.append({'result': 'false'})
        content = simplejson.dumps(json_result)
        return request.make_response(content, [('Content-Type', 'application/json;charset=utf-8')])

    @http.route('/web_under_maintenance/toggle', type='http', auth='user')
    def web_under_maintenance(self, *args, **kwargs):
        # Validation
        ensure_db()
        if request.env.uid != SUPERUSER_ID:
            raise AccessError(_("Access Denied"))
        # Objects
        redirect = request.params and 'redirect' in request.params and request.params['redirect'] or '/web'
        ir_param = request.env['ir.config_parameter'].sudo()
        session_obj = request.env['ir.session'].sudo()
        # Toggle mode
        under_maintenance = 0 if bool(eval(ir_param.get_param('under_maintenance'))) else 1
        ir_param.set_param('under_maintenance', under_maintenance)
        if under_maintenance:
            sessions = session_obj.search([
                ('user_id', '!=', SUPERUSER_ID),
                ('is_logged_in', '=', True),
            ])
            if sessions:
                sessions.close_sessions()
        # Reload
        return werkzeug.utils.redirect(redirect, 303)


class WebSession(Session, SessionMixin):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        old_uid = request.uid
        result = self.check_session(db, login, password)
        if not result:
            password = None
            request.uid = old_uid
        return super(WebSession, self).authenticate(db, login, password, base_location=base_location)


class WebHome(Home, SessionMixin):

    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, *args, **kw):
        ensure_db()
        request.params['login_success'] = False

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            # Objects
            old_uid = request.uid
            db = request.session.db
            login = request.params.get('login', None)
            password = request.params.get('password', None)
            # Check maintenance mode
            result = self.check_session(db, login, password)
            if result:
                request.params['login_success'] = True
            else:
                request.uid = old_uid
                values['error'] = _('Sorry, system is under maintenance! Please, try again later.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        if request.params['login_success']:
            return http.redirect_with_hash('/web')

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)