# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
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

    def _get_total_units(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            total_units = 0
            for line in order.order_line:
                if line.product_id and line.product_id.type == 'service':
                    continue
                total_units += line.product_uom_qty
            res[order.id] = total_units
        return res

    _columns = {
        'total_units': fields.function(_get_total_units, method=True, type='float',
            string='Total Units')
    }

sale_order()