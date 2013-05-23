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

class pos_add_product(osv.osv_memory):
    _name = 'pos.add.product'

    _columns = {
        'pos_order_id': fields.many2one('pos.order', 'Order Id'),
        'barcode': fields.char('Barcode', size=64, required=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(pos_add_product, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id', False):
            res.update({'pos_order_id': context['active_id']})
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        order = self.pool.get('pos.order').browse(cr, uid, context['active_id'], context=context)
        if order.state != 'draft':
            raise osv.except_osv(_('Error'),_('Can only add lines in orders with draft status'))


    def barcode_change(self, cr, uid, ids, barcode, pos_order_id):
        if not barcode:
            return {}
        product_pool = self.pool.get('product.product')
        line_pool = self.pool.get('pos.order.line')
        pos_order = self.pool.get('pos.order').browse(cr, uid, pos_order_id)
        product_ids = product_pool.search(cr, uid, [('ean13','=',barcode)])
        res = {'value': {'barcode': None}}
        if product_ids:
            onchange_prod = line_pool.onchange_product_id(cr, uid, [], 
                pos_order.pricelist_id and pos_order.pricelist_id.id, 
                product_ids[0], qty=1)
            line_vals = {
                'product_id': product_ids[0],
                'qty': 1,
                'price_unit': onchange_prod['value']['price_unit'],
                'order_id': pos_order.id,
                'tax_id': [(6,0, onchange_prod['value']['tax_id'])],
                'price_subtotal': onchange_prod['value']['price_subtotal'],
                'price_subtotal_incl': onchange_prod['value']['price_subtotal_incl']

            }
            pos_add_line_val = {
                'product_id': product_ids[0],
                'qty': 1,
                'price_unit': onchange_prod['value']['price_unit'],
            }
            line_pool.create(cr, uid, line_vals)
            #line_id = self.pool.get('pos.add.product.line').create(cr, uid, pos_add_line_val)
            #res['value'].update({'line_ids': [line_id]})
        return res

pos_add_product()