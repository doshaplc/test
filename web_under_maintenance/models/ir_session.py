# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import root

class IrSession(models.Model):
    _name = 'ir.session'
    _description = 'User Sessions'

    user_id = fields.Many2one('res.users', string='User', ondelete='cascade')
    session_id = fields.Char(string='Session ID')
    login_date = fields.Datetime(string='Login Date', default=fields.Datetime.now())
    logout_date = fields.Datetime(string='Logout Date')
    is_logged_in = fields.Boolean(string='Is logged in?')

    @api.multi
    def session_logout(self):
        # Objects
        now = fields.datetime.now()
        session_obj = self.env['ir.session'].sudo()
        cr = self.env.cr

        # autocommit: our single update request will be performed atomically.
        # (In this way, there is no opportunity to have two transactions
        # interleaving their cr.execute()..cr.commit() calls and have one
        # of them rolled back due to a concurrent access.)
        cr.autocommit(True)

        # Update sessions info.
        for session in self:
            s = session_obj.browse(session.id)
            s.write({
                'is_logged_in': False,
                'logout_date': now,
            })

        cr.commit()
        return True

    @api.multi
    def close_sessions(self):
        for session in self:
            session_eng = root.session_store.get(session.session_id)
            session_eng.logout(env=self.env)