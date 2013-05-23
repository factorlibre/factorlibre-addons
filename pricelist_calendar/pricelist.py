# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Factor Libre.
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

from _common import rounding
import time
from tools.translate import _
import decimal_precision as dp

class product_pricelist(osv.osv):
    _inherit = 'product.pricelist'

    def price_get_calendar(self, cr, uid, pricelist_id, product_id, qty, partner=None, \
      time_slot=None, context=None):
        if context is None:
            context = {}
        
        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst

        date = time.strftime('%Y-%m-%d')
        if 'date' in context:
            date = context['date']

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_template_obj = self.pool.get('product.template')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        if not time_slot:
            res = super(product_pricelist, self).price_get(cr, uid, ids, prod_id, qty, partner=partner, context=context)
            return res

        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', '=', pricelist_id),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if not len(pricelist_version_ids):
            raise osv.except_osv(_('Warning !'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])
        
        results = {}

        price = False
        tmpl_id = product.product_tmpl_id and product.product_tmpl_id.id or False
        categ_id = product.categ_id and product.categ_id.id or False
        categ_ids = _create_parent_category_list(categ_id, [categ_id])

        if categ_ids:
            categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
        else:
            categ_where = '(categ_id IS NULL)'

        cr.execute(
            'SELECT i.*, pl.currency_id '
            'FROM product_pricelist_item AS i, '
                'product_pricelist_version AS v, product_pricelist AS pl '
                #', attendance_pricelist_rel as att '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                'AND (product_id IS NULL OR product_id = %s) '
                'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                'AND price_version_id = %s '
                'AND (min_quantity IS NULL OR min_quantity <= %s) '
                'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                #'AND att.item_id = i.id '
                'AND i.time_slot = %s '
            'ORDER BY sequence', (tmpl_id, product_id, pricelist_version_ids[0], qty, time_slot))

        res1 = cr.dictfetchall()
        uom_price_already_computed = False
        for res in res1:
            if res:
                if res['base'] == -1:
                    if not res['base_pricelist_id']:
                        price = 0.0
                    else:
                        price_tmp = self.price_get(cr, uid,
                                [res['base_pricelist_id']], product_id,
                                qty, context=context)[res['base_pricelist_id']]
                        ptype_src = self.browse(cr, uid, res['base_pricelist_id']).currency_id.id
                        uom_price_already_computed = True
                        price = currency_obj.compute(cr, uid, ptype_src, res['currency_id'], price_tmp, round=False)
                elif res['base'] == -2:
                    # this section could be improved by moving the queries outside the loop:
                    where = []
                    if partner:
                        where = [('name', '=', partner) ]
                    sinfo = supplierinfo_obj.search(cr, uid,
                            [('product_id', '=', tmpl_id)] + where)
                    price = 0.0
                    if sinfo:
                        qty_in_product_uom = qty
                        product_default_uom = product_template_obj.read(cr, uid, [tmpl_id], ['uom_id'])[0]['uom_id'][0]
                        supplier = supplierinfo_obj.browse(cr, uid, sinfo, context=context)[0]
                        seller_uom = supplier.product_uom and supplier.product_uom.id or False
                        if seller_uom and product_default_uom and product_default_uom != seller_uom:
                            uom_price_already_computed = True
                            qty_in_product_uom = product_uom_obj._compute_qty(cr, uid, product_default_uom, qty, to_uom_id=seller_uom)
                        cr.execute('SELECT * ' \
                                'FROM pricelist_partnerinfo ' \
                                'WHERE suppinfo_id IN %s' \
                                    'AND min_quantity <= %s ' \
                                'ORDER BY min_quantity DESC LIMIT 1', (tuple(sinfo),qty_in_product_uom,))
                        res2 = cr.dictfetchone()
                        if res2:
                            price = res2['price']
                else:
                    price_type = price_type_obj.browse(cr, uid, int(res['base']))
                    uom_price_already_computed = True
                    price = currency_obj.compute(cr, uid,
                            price_type.currency_id.id, res['currency_id'],
                            product_obj.price_get(cr, uid, [product_id],
                            price_type.field, context=context)[product_id], round=False, context=context)

                if price is not False:
                    price_limit = price
                    price = price * (1.0+(res['price_discount'] or 0.0))
                    price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                    price += (res['price_surcharge'] or 0.0)
                    if res['price_min_margin']:
                        price = max(price, price_limit+res['price_min_margin'])
                    if res['price_max_margin']:
                        price = min(price, price_limit+res['price_max_margin'])
                    break

            else:
                # False means no valid line found ! But we may not raise an
                # exception here because it breaks the search
                price = False

        if price:
            results['item_id'] = res['id']
            if 'uom' in context and not uom_price_already_computed:
                uom = product.uos_id or product.uom_id
                price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

        if results.get(product_id):
            results[product_id][pricelist_id] = price
        else:
            results[product_id] = {pricelist_id: price}
            
        res = results[product_id][pricelist_id]
        return res

product_pricelist()

class product_pricelist_item(osv.osv):
    _inherit = 'product.pricelist.item'

    time_slots = (
        ('ordinary','Ordinary'),
        ('nocturnal','Nocturnal'),
        ('extra','Extra'),
        ('festive','Festive')
    )

    _columns = {
        'calendar_attendance_ids': fields.many2many('resource.calendar.attendance', 'attendance_pricelist_rel',
            'item_id', 'attendance_id', 'Calendar'),
        'time_slot': fields.selection(time_slots, 'Time Slot'),
    }

product_pricelist_item()