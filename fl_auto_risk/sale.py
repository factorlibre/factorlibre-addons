# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Hugo Santos (<http://factorlibre.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def onchange_partner_id(self, cr, uid, ids, part):
        result = super(sale_order,self).onchange_partner_id(cr, uid, ids, part)
        if part:
            partner = self.pool.get('res.partner').browse(cr, uid, part)
            if partner.company_credit_limit == 0.0:
                result['warning'] = {}
            if partner.company_credit_limit != 0.0 and partner.available_risk < 0.0:
                result['warning'] = {
                    'title': _('Credit Limit Exceeded'),
                    'message': _('Warning: Credit Limit Exceeded.\n\nThis partner has a credit limit of %(limit).2f and already has a debt of %(debt).2f.') % {
                        'limit': partner.credit_limit,
                        'debt': partner.total_debt,
                    }
                }
        return result

sale_order()