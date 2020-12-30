# -*- coding: utf-8 -*-

import werkzeug
import odoo
from odoo.http import request
from odoo.tools.func import lazy_property


class OpenERPSession(odoo.http.OpenERPSession):

    def logout(self, keep_db=False, env=False):
        try:
            env = env or request.env
        except:
            pass

        if env and hasattr(env, 'registry') and env.registry.get('ir.session'):
            session = env['ir.session'].sudo().search([
                ('session_id', '=', self.sid),
                ('is_logged_in', '=', True),
            ])
            if session:
                session.session_logout()

        super(OpenERPSession, self).logout(keep_db=keep_db)


class Root(odoo.http.Root):

    @lazy_property
    def session_store(self):
        # Setup http sessions
        path = odoo.tools.config.session_dir
        return werkzeug.contrib.sessions.FilesystemSessionStore(path, session_class=OpenERPSession)


root = Root()
odoo.http.root.session_store = root.session_store