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

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'wholesaler_price': fields.float('Wholesaler Price'),
    }

    def update_wholesaler_pricelist(self, cr, uid, ids, context=None):
        wholesaler_pricelist_pool = self.pool.get('wholesaler.pricelist.config')
        pricelist_version_pool = self.pool.get('product.pricelist.version')
        pricelist_item_pool = self.pool.get('product.pricelist.item')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.wholesaler_price:           
                wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
                if wholesaler_ids and wholesaler_ids[0]:
                    wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                    pricelist = wholesaler_list.pricelist_id
                    if pricelist.version_id and pricelist.version_id[0]:
                        item_values = {
                            'price_version_id': pricelist.version_id[0].id,
                            'name': "%s" % (obj.name),
                            'base': 1,
                            'product_tmpl_id': obj.id,
                            'min_quantity': 1,
                            'price_discount': -1,
                            'price_surcharge': obj.wholesaler_price
                        }
                        item_ids = pricelist_item_pool.search(cr, uid, 
                            [('price_version_id','=', pricelist.version_id[0].id),
                             ('product_tmpl_id','=',obj.id)])
                        if item_ids and item_ids[0]:
                            pricelist_item_pool.write(cr, uid, item_ids[0], item_values, context=context)
                        else:
                            pricelist_item_pool.create(cr, uid, item_values, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res = super(product_template, self).create(cr, uid, vals, context=context)

        wholesaler_pricelist_pool = self.pool.get('wholesaler.pricelist.config')
        pricelist_version_pool = self.pool.get('product.pricelist.version')
        pricelist_item_pool = self.pool.get('product.pricelist.item')
        tmpl = self.browse(cr, uid, res, context=context)
        
        if 'wholesaler_price' in vals and vals['wholesaler_price'] > 0:           
            wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
            if wholesaler_ids and wholesaler_ids[0]:
                wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                pricelist = wholesaler_list.pricelist_id
                if pricelist.version_id and pricelist.version_id[0]:
                    item_values = {
                        'price_version_id': pricelist.version_id[0].id,
                        'name': tmpl.name,
                        'base': 1,
                        'product_tmpl_id': tmpl.id,
                        'min_quantity': 1,
                        'price_discount': -1,
                        'price_surcharge': vals['wholesaler_price']
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
        for obj in self.browse(cr, uid, ids, context=context):
            if 'wholesaler_price' in vals:           
                wholesaler_ids = wholesaler_pricelist_pool.search(cr, uid, [])
                if wholesaler_ids and wholesaler_ids[0]:
                    wholesaler_list = wholesaler_pricelist_pool.browse(cr, uid, wholesaler_ids[0])
                    pricelist = wholesaler_list.pricelist_id
                    if pricelist.version_id and pricelist.version_id[0]:
                        item_values = {
                            'price_version_id': pricelist.version_id[0].id,
                            'name': "%s" % (obj.name),
                            'base': 1,
                            'product_tmpl_id': obj.id,
                            'min_quantity': 1,
                            'price_discount': -1,
                            'price_surcharge': vals['wholesaler_price']
                        }
                        item_ids = pricelist_item_pool.search(cr, uid, 
                            [('price_version_id','=', pricelist.version_id[0].id),
                             ('product_tmpl_id','=',obj.id)])
                        if item_ids and item_ids[0]:
                            pricelist_item_pool.write(cr, uid, item_ids[0], item_values, context=context)
                        else:
                            pricelist_item_pool.create(cr, uid, item_values, context=context)

        return super(product_template, self).write(cr, uid, ids, vals, context=context)

product_template()