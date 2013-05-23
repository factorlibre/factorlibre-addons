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

class product_template(osv.osv):
    _inherit = 'product.template'

    def _get_tmpl(self, cr, uid, ids, context=None):
        result = {}
        for s_info in self.pool.get('product.supplierinfo').browse(cr, uid, ids, context=context):
            result[s_info.product_id.id] = True
        return result.keys()

    def _get_main_product_supplier(self, cr, uid, product, context=None):
        """Determines the main (best) product supplier for ``product``, 
        returning the corresponding ``supplierinfo`` record, or False
        if none were found. The default strategy is to select the
        supplier with the highest priority (i.e. smallest sequence).

        :param browse_record product: product to supply
        :rtype: product.supplierinfo browse_record or False
        """
        sellers = [(seller_info.sequence, seller_info)
                       for seller_info in product.seller_ids or []
                       if seller_info and isinstance(seller_info.sequence, (int, long))]
        return sellers and sellers[0][1] or False

    def _calc_seller(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        for product in self.browse(cr, uid, ids, context=context):
            main_supplier = self._get_main_product_supplier(cr, uid, product, context=context)
            result[product.id] = main_supplier and main_supplier.name.id or False
        return result

    def _get_product_suppliers(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = str([sup.name and sup.name.id for sup in obj.seller_ids])
        return res

    _columns = {
        'seller_id': fields.function(_calc_seller, type='many2one', relation="res.partner", string='Main Supplier', help="Main Supplier who has highest priority in Supplier List.",
            store = {
                'product.supplierinfo': (_get_tmpl, ['name'], 10),
        })
    }

product_template()