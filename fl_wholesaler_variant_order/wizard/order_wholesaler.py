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
from datetime import datetime

class order_wholesaler(osv.osv_memory):
    _name = 'order.wholesaler'

    _rec_name = 'tmpl_id'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'tmpl_id': fields.many2one('product.template', 'Product Template', required=True),
        'wholesaler_line_ids': fields.one2many('order.wholesaler.line', 'wholesaler_id', 'Lines'),
        'location_id': fields.many2one('stock.location', 'Source Location'),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location')
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(order_wholesaler, self).default_get(cr, uid, fields, context=context)
        order_obj = self.pool.get(context['active_model'])
        for order in order_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if context.get('active_model','') == 'stock.picking':
                break
            partner = order.partner_id and order.partner_id.id
            res.update({'partner_id': partner})
             
        return res

    def get_variant(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        order_pool = self.pool.get(context['active_model'])
        purchase_line_pool = self.pool.get('purchase.order.line')
        sale_line_pool = self.pool.get('sale.order.line')
        order = order_pool.browse(cr, uid, context['active_id'], context=context)
        for obj in self.browse(cr, uid, ids, context=context):
            if not obj.tmpl_id:
                continue
            line_pool = self.pool.get('order.wholesaler.line')
            line_pool.unlink(cr, uid, line_pool.search(cr, uid, []))
            product_pool = self.pool.get('product.product')
            prod_ids = product_pool.search(cr, uid, [('product_tmpl_id','=',obj.tmpl_id.id)])
            for product in product_pool.browse(cr, uid, prod_ids, context=context):
                price_unit = product.list_price
                if context.get('active_model','') == 'sale.order':
                    prod_change_sale = sale_line_pool.product_id_change(cr, uid, [], order.pricelist_id.id, 
                        product.id, qty=1, uom=False, qty_uos=0, uos=False, name='', partner_id=order.partner_id.id,
                        date_order=datetime.today().strftime('%Y-%m-%d'), context=context)
                    price_unit = prod_change_sale.get('value',{}).get('price_unit', product.list_price)
                    discount = prod_change_sale.get('value',{}).get('discount',0.0)
                    if discount:
                        price_unit = price_unit - (price_unit * discount / 100.0)

                if context.get('active_model','') == 'purchase.order':
                    prod_change_purchase = purchase_line_pool.onchange_product_id(cr, uid, ids, order.pricelist_id.id, 
                        product.id, 1, product.uom_id.id, order.partner_id.id, 
                        date_order=datetime.today().strftime('%Y-%m-%d'), context=context)

                    price_unit = prod_change_purchase.get('value',{}).get('price_unit', product.standard_price) 
                line_id = line_pool.create(cr, uid, {
                    'product_id': product.id,
                    'wholesaler_id': obj.id,
                    'qty': 0,
                    'price_unit': price_unit
                    })
        return True

    def create_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        order_pool = self.pool.get(context['active_model'])
        account_tax = self.pool.get('account.tax')

        if context.get('active_model', '') == 'stock.picking':
            order_line_pool = self.pool.get('stock.move')
        else:
            order_line_pool = self.pool.get("%s.line" % context['active_model'])
        order = order_pool.browse(cr, uid, context['active_id'], context=context)

        for obj in self.browse(cr, uid, ids, context=context):
            fpos = False
            if context.get('active_model','') in ['sale.order','purchase.order']:
                fpos = order.fiscal_position
                if not fpos:
                    fpos = obj.partner_id and obj.partner_id.property_account_position or False
            for line in obj.wholesaler_line_ids:
                if not line.qty:
                    continue
                values = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name_get()[0][1],
                    'product_uom': line.product_id.uom_id.id,
                }
                if context.get('active_model','') == 'sale.order':
                    taxes = account_tax.browse(cr, uid, map(lambda x: x.id, line.product_id.taxes_id))
                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
                    values.update({
                        'order_id': context['active_id'],
                        'product_uom_qty': line.qty,
                        'price_unit': line.price_unit,
                        'tax_id': [(6,0, tax_ids)]
                    })
                elif context.get('active_model', '') == 'purchase.order':
                    taxes = account_tax.browse(cr, uid, map(lambda x: x.id, line.product_id.supplier_taxes_id))
                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
                    values.update({
                        'order_id': context['active_id'],
                        'product_qty': line.qty,
                        'date_planned': order.date_order,
                        'price_unit': line.price_unit,
                        'taxes_id': [(6, 0, tax_ids)]
                    })
                elif context.get('active_model', '') == 'stock.picking':
                    values.update({
                        'picking_id': context['active_id'],
                        'product_qty': line.qty,
                        'location_id': obj.location_id and obj.location_id.id,
                        'location_dest_id': obj.location_dest_id and obj.location_dest_id.id
                    })
                   
                order_line_pool.create(cr, uid, values)
        line_pool = self.pool.get('order.wholesaler.line')
        line_pool.unlink(cr, uid, line_pool.search(cr, uid, []))
        return {'type' : 'ir.actions.act_window_close'}

order_wholesaler()

class order_wholesaler_line(osv.osv_memory):
    _name = 'order.wholesaler.line'

    _rec_name = 'product_id'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'qty': fields.float('Qty'),
        'price_unit': fields.float('Price Unit'),
        'wholesaler_id': fields.many2one('order.wholesaler', 'wholesaler') 
    }

order_wholesaler_line()