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

class product_minimum_pricelist(osv.osv):

    _name = 'product.minimum.pricelist'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'minimum_percent': fields.float('Minimum %'),
        'product_ids': fields.many2many('product.product', 'product_minimum_pricelist_rel', 
            'minimum_pricelist_id', 'product_id'),
        'product_category_ids': fields.many2many('product.category', 'category_minimum_pricelist_rel',
            'minimum_pricelist_id', 'category_id'),
        'priority': fields.integer('Sequence'),
    }

    _order = 'priority asc'

product_minimum_pricelist()