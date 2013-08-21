# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 (<http://www.factorlibre.com>).
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
import netsvc


class wizz_product_supplier(osv.osv_memory):
    _name = 'wizz.product.supplier'

    _columns={
             'replace':fields.boolean('Replace?',help="Defaults add supplier to product but this field is checked, replace the suppliers"),
             'supplier_id':fields.many2one('res.partner','Supplier',domain=[('supplier','=',True)])
             }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', 
                        context=None, toolbar=False, submenu=False):
        """ 
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary 
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(wizz_product_supplier, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'product.product' and len(context['active_ids']) < 1:
            raise osv.except_osv(_('Warning'),
            _('Please select one or more products to assign supplier in the list view.'))
        return res    



    def do_assign(self, cr, uid, ids, context=None):
        """ To merge selected Inventories.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected 
        @param context: A standard dictionary 
        @return: 
        """ 
        product_obj = self.pool.get('product.product')
        supplier_obj = self.pool.get('res.partner')
        product_supplier = self.pool.get('product.supplierinfo')
        

        logger = netsvc.Logger()
        

        if context is None:
            context = {}

        wizz_supplier_prod=self.pool.get('wizz.product.supplier').browse(cr,uid,ids[0])

        for product in product_obj.browse(cr, uid, context['active_ids'], context=context):
            #logger.notifyChannel("warning", netsvc.LOG_WARNING,"entro")
            #replace
            if wizz_supplier_prod.replace:
               supplier_rel=product_supplier.search(cr,uid,[('product_id','=',product.product_tmpl_id.id)])
               if supplier_rel:
                   
                   product_supplier.unlink(cr,uid,supplier_rel)
                   
               create=product_supplier.create(cr,uid,{
                                               'name':wizz_supplier_prod.supplier_id.id,
                                               'product_id':product.product_tmpl_id.id,
                                               'min_qty':0,
                                               })
            else:
               create=product_supplier.create(cr,uid,{
                                               'name':wizz_supplier_prod.supplier_id.id,
                                               'product_id':product.product_tmpl_id.id,
                                               'min_qty':0,
                                               }) 
            

            #logger.notifyChannel("warning", netsvc.LOG_WARNING,create)
            #logger.notifyChannel("warning", netsvc.LOG_WARNING,product.id)
        return {'type': 'ir.actions.act_window_close'}

wizz_product_supplier()
