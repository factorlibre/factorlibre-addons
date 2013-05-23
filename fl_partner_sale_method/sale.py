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

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def onchange_partner_id(self, cr, uid, ids, part):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
        if not part:
            return res
        partner = self.pool.get('res.partner').browse(cr, uid, part)
        if partner.order_policy:
            res['value']['order_policy'] = partner.order_policy        
        return res
sale_order