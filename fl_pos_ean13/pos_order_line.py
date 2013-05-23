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
from tools.translate import _

class pos_order_line(osv.osv):
    _inherit = 'pos.order.line'

    _columns = {
        'ean13': fields.char('EAN13', size=128),
    }

    def onchange_ean13(self, cr, uid, ids, ean13):
        res = {'value': {}}

        if not ean13:
            return res
        product_ids = self.pool.get('product.product').search(cr, uid, [('ean13','=',ean13)])
        if product_ids:
            res['value']['product_id'] = product_ids[0]
        return res
pos_order_line()
