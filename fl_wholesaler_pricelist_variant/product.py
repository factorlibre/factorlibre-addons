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

from osv import osv

class product_product(osv.osv):
    _inherit = 'product.product'

    def update_wholesaler_pricelist_product(self, cr, uid, ids, context=None):
        wholesaler_pricelist_pool = self.pool.get('wholesaler.pricelist.config')
        pricelist_version_pool = self.pool.get('product.pricelist.version')
        pricelist_item_pool = self.pool.get('product.pricelist.item')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.product_tmpl_id.wholesaler_price and obj.price_extra:           
                wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
                if wholesaler_ids and wholesaler_ids[0]:
                    wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                    pricelist = wholesaler_list.pricelist_id
                    if pricelist.version_id and pricelist.version_id[0]:
                        item_values = {
                            'price_version_id': pricelist.version_id[0].id,
                            'name': "%s" % (obj.name),
                            'base': 1,
                            'product_id': obj.id,
                            'sequence': 4,
                            'min_quantity': 1,
                            'price_discount': -1,
                            'price_surcharge': obj.product_tmpl_id.wholesaler_price + obj.price_extra
                        }
                        item_ids = pricelist_item_pool.search(cr, uid, 
                            [('price_version_id','=', pricelist.version_id[0].id),
                             ('product_id','=',obj.id)])
                        if item_ids and item_ids[0]:
                            pricelist_item_pool.write(cr, uid, item_ids[0], item_values, context=context)
                        else:
                            pricelist_item_pool.create(cr, uid, item_values, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        wholesaler_pricelist_pool = self.pool.get('wholesaler.pricelist.config')
        pricelist_version_pool = self.pool.get('product.pricelist.version')
        pricelist_item_pool = self.pool.get('product.pricelist.item')

        res = super(product_product, self).create(cr, uid, vals, context=context)

        if vals.get('price_extra'):
            product_template = self.browse(cr, uid, res, context=context).product_tmpl_id
            if product_template.wholesaler_price and product_template.wholesaler_price > 0:
                wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
                if wholesaler_ids and wholesaler_ids[0]:
                    wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                    pricelist = wholesaler_list.pricelist_id
                    if pricelist.version_id and pricelist.version_id[0]:
                        item_values = {
                            'price_version_id': pricelist.version_id[0].id,
                            'name': product_template.name,
                            'base': 1,
                            'product_id': res,
                            'min_quantity': 1,
                            'price_discount': -1,
                            'price_surcharge': product_template.wholesaler_price + vals['price_extra'],
                            'sequence': 4
                        }
                        pricelist_item_pool.create(cr, uid, item_values)

        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if not isinstance(ids, list):
            ids = [ids]

        wholesaler_pricelist_pool = self.pool.get('wholesaler.pricelist.config')
        pricelist_version_pool = self.pool.get('product.pricelist.version')
        pricelist_item_pool = self.pool.get('product.pricelist.item')
        if vals.get('price_extra'):
            for obj in self.browse(cr, uid, ids, context=context):
                if obj.product_tmpl_id.wholesaler_price > 0:
                    wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
                    if wholesaler_ids and wholesaler_ids[0]:
                        wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                        pricelist = wholesaler_list.pricelist_id
                        if pricelist.version_id and pricelist.version_id[0]:
                            item_values = {
                                'price_version_id': pricelist.version_id[0].id,
                                'name': "%s" % (obj.name),
                                'base': 1,
                                'product_id': obj.id,
                                'min_quantity': 1,
                                'sequence': 4,
                                'price_discount': -1,
                                'price_surcharge': obj.product_tmpl_id.wholesaler_price + vals['price_extra']
                            }
                            item_ids = pricelist_item_pool.search(cr, uid, 
                                [('price_version_id','=', pricelist.version_id[0].id),
                                 ('product_id','=',obj.id)])
                            if item_ids and item_ids[0]:
                                pricelist_item_pool.write(cr, uid, item_ids[0], item_values, context=context)
                            else:
                                pricelist_item_pool.create(cr, uid, item_values, context=context)

        return super(product_product, self).write(cr, uid, ids, vals, context=context)



product_product()