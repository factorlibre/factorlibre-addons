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

class stock_move(osv.osv):
    _inherit = 'stock.move'

    _columns = {
        'ean13': fields.char('EAN13', size=128),
    }

    def onchange_ean13(self, cr, uid, ids, ean13, loc_id=False,
                       loc_dest_id=False, address_id=False):
        res = {}
        if not ean13:
            return {}
        product_ids = self.pool.get('product.product').search(cr, uid, [
                ('ean13','=',ean13)
            ])

        if product_ids:
            res = self.onchange_product_id(cr, uid, ids, prod_id=product_ids[0],
                loc_id=loc_id, loc_dest_id=loc_dest_id, address_id=address_id)
            if res.get('value', {}):
                res['value']['product_id'] = product_ids[0]
            
        return res

    _defaults = {
        'location_id': False,
        'location_dest_id': False
    }

stock_move()