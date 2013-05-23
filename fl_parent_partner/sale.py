# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    #    Copyright (C) 2012 Factor Libre.
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

    _columns = {
        'parent_partner_id': fields.related('partner_id', 'parent_id', 
            type='many2one', relation='res.partner', string='Parent Partner', 
            store=True, readonly=True),
    }

    def onchange_partner_id(self, cr, uid, ids, part):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
        part = self.pool.get('res.partner').browse(cr, uid, part)
        if part.parent_id:
            res['value'].update({'parent_partner_id': part.parent_id.id})
        return res

sale_order()