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

class stock_inventory_line(osv.osv):
    _inherit = 'stock.inventory.line'

    _columns = {
        'original_qty': fields.float('Original Stock', readonly=True),
    }

    _defaults = {
        'original_qty': 0.0
    }

    def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        res = super(stock_inventory_line, self).on_change_product_id(cr, uid, ids, location_id, 
            product, uom=uom, to_date=to_date)
        if res.get('value', {}).get('product_qty', 0):
            res['value']['original_qty'] = res['value']['product_qty']
        else:
            res['value']['original_qty']=0
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('product_id'):
            product_vals = self.on_change_product_id(cr, uid, [], [],vals.get('product_id'))
            vals['original_qty'] = product_vals['value'].get('original_qty')

        return super(stock_inventory_line, self).create(cr, uid, vals, context=context)


    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('product_id'):
            product_vals = self.on_change_product_id(cr, uid, [], [],vals.get('product_id'))
            vals['original_qty'] = product_vals['value'].get('original_qty')
        return super(stock_inventory_line, self).write(cr, uid, ids, vals, context=context)

stock_inventory_line()
