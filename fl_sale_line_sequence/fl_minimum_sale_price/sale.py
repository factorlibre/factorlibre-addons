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

def get_minimum_pricelist_entry(cr, uid, product):
    cr.execute("""SELECT id from product_minimum_pricelist where id in 
            (SELECT minimum_pricelist_id from product_minimum_pricelist_rel
                where product_id = %d) order by priority asc""" % (product.id))
    minimum_pricelist_id = cr.fetchone()

    if not minimum_pricelist_id:
        if not product.categ_id:
            return False
        cr.execute("""SELECT id from product_minimum_pricelist where id in 
        (SELECT minimum_pricelist_id from category_minimum_pricelist_rel
            where category_id = %d) order by priority asc""" % (product.categ_id.id))
        minimum_pricelist_id = cr.fetchone()
        if not minimum_pricelist_id:
            return False
    return minimum_pricelist_id[0]

class sale_order(osv.osv):

    _inherit = 'sale.order'

    def _check_order_minimum_price(self, cr, uid, order):
        minimun_price = True
        for line in order.order_line:
            if line.product_id:
                line_price_unit = (line.price_unit * (1-(line.discount or 0.0)/100.0))
                minimum_pricelist_id = get_minimum_pricelist_entry(cr, uid, line.product_id)
                if minimum_pricelist_id:
                    pricelist = self.pool.get('product.minimum.pricelist').browse(cr, uid, minimum_pricelist_id)
                    minimum_price = line.product_id.standard_price * (1+(pricelist.minimum_percent or 0.0)/100)
                    if minimum_price > line_price_unit:
                        minimum_price = False
                        break
        self.write(cr, uid, [order.id], {'minimum_price': minimum_price})
        return minimum_price 

    _columns = {
        'minimum_price': fields.boolean("Minimum Price?", readonly=True),
        'force_price': fields.boolean('Force Price?'),
    }

    _defaults = {
        'minimum_price': True
    }

    def button_dummy(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(sale_order, self).button_dummy(cr, uid, ids, context=context)

        for o in self.browse(cr, uid, ids, context=context):
            self._check_order_minimum_price(cr, uid, o)
        return True

    def action_wait(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for o in self.browse(cr, uid, ids, context=context):
            if not self._check_order_minimum_price(cr, uid, o) and not o.force_price:
                raise osv.except_osv(_('Error !'),
                    _('You cannot confirm a sale order which has lines that not reach the minimum price.'))
        return super(sale_order, self).action_wait(cr, uid, ids, context=context)

sale_order()

class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'

    _columns = {
        'minimum_price': fields.boolean('Minimum Price?')
    }

    _defaults = {
        'minimum_price': True
    }

    def onchange_price_unit(self, cr, uid, ids, product, price_unit):
        res = {}
        if not product:
            return res
        product = self.pool.get('product.product').browse(cr, uid, product)
        minimum_pricelist_pool = self.pool.get('product.minimum.pricelist')
        minimum_pricelist_id = get_minimum_pricelist_entry(cr, uid, product)
        if not minimum_pricelist_id:
            return res
        pricelist = minimum_pricelist_pool.browse(cr, uid, minimum_pricelist_id)

        print "%s Pricelist %s Percent %s" % (minimum_pricelist_id, pricelist.name, pricelist.minimum_percent)
        minimum_price = product.standard_price * (1+(pricelist.minimum_percent or 0.0)/100.0)

        if minimum_price > price_unit :
            res = {
                'value': {'minimum_price': False},
                'warning': {
                    'title': _('Minimum price not reached'),
                    'message': _('Warning: The minimum price defined in the product is %s' \
                        % (minimum_price))
                }
            }
        else:
            res = {
                'value': {'minimum_price': True}
            }
        return res

sale_order_line()