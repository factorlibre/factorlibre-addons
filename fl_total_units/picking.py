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

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _get_total_units(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            total_units = 0.0
            for line in pick.move_lines:
                if line.state in ['done', 'assigned', 'confirmed', 'waiting']:
                    total_units += line.product_qty
            res[pick.id] = total_units
        return res

    _columns = {
        'total_units': fields.function(_get_total_units, method=True, type='float',
            string="Total Units")
    }

stock_picking()