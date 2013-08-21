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



class wizz_stock_picking(osv.osv_memory):
    _name = 'wizz.stock.picking'


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
        res = super(wizz_stock_picking, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'stock.picking' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning'),
            _('Please select multiple stock pickings to optimize in the list view.'))
        return res    


    def remove_products_line(self, cr, uid, dic, picking):
        
        for line in picking.move_lines:
            if line.product_id.id in dic:
                cont=0
                for line_prod in dic[line.product_id.id]:
                    if line_prod['line_id'] == line.id:

                        if len(dic[line.product_id.id])==1:
                              del dic[line.product_id.id]
                        else:
                              del dic[line.product_id.id][cont]
                    cont=cont+1
        return dic


    
    

    def do_optimize(self, cr, uid, ids, context=None):
        """ To merge selected Inventories.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected 
        @param context: A standard dictionary 
        @return: 
        """ 
        picking_obj = self.pool.get('stock.picking')
        picking_line_obj = self.pool.get('stock.move')
        invent_lines = {}
        LOGGER = netsvc.Logger()
        
        if context is None:
            context = {}

        #Extract products_reserved
        products_reserved={}
        for picking in picking_obj.browse(cr, uid, context['active_ids'], context=context):
            if picking.partially_reserved:
                
                print picking.id
                for line in picking.move_lines:
                    key = (line.product_id.id)
                    if key in products_reserved:
                        products_reserved[key].append({'line_id': line.id, 'quantity': line.product_qty})

                    else:
                        products_reserved.setdefault(key, []).append({'line_id': line.id, 'quantity': line.product_qty})

      
        #search and compare with lines non avaliables

        order_picking=picking_obj.search(cr, uid, [('id','in',context['active_ids'])], order='complete_factor desc')


        for picking in picking_obj.browse(cr, uid, order_picking, context=context):

            
            if picking.state=='assigned' or picking.state=='confirmed':
 
                for line in picking.move_lines:

                    if line.state=='confirmed':

                        if line.product_id.id in products_reserved:
                            
                            cont=0
                            for line_prod in products_reserved[line.product_id.id]:

                                if line_prod['line_id'] == line.id:
                                    continue
            
                                if line_prod['quantity'] >= line.product_qty:
                                                               
                                    #Quit assign products

                                    picking_line_obj.cancel_assign(cr,uid,[line_prod['line_id']])
                                    line_stock= self.pool.get('stock.move').browse(cr,uid,line_prod['line_id'])
                                    picking_obj.write(cr,uid,line_stock.picking_id.id,{})

                                    if len(products_reserved[line.product_id.id])==1:
                                        del products_reserved[line.product_id.id]
                                    else:
                                        del products_reserved[line.product_id.id][cont]

                                    #assing product
                                    #picking_line_obj.action_assign(cr,uid,[line.id])
                                    

                                    #check and complete picking
                                    LOGGER.notifyChannel('Stock Picking', netsvc.LOG_INFO, "Optimize: %s." % (picking.name))
                                    confirmed=picking_obj.action_assign( cr, uid, [picking.id])
                                    finish=picking_obj.verify_assigned( cr, uid, [picking.id])
                                    
                                    if finish:
                                        self.pool.get('wizz.stock.picking').remove_products_line(cr, uid, products_reserved, picking)
                                        
                                    picking_obj.write(cr,uid,picking.id,{})

                                    cont=cont+1
            

        
        return {'type': 'ir.actions.act_window_close'}

wizz_stock_picking()



class wizz_picking_check_availability(osv.osv_memory):
    _name = 'wizz.picking.check.availability'


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
        res = super(wizz_picking_check_availability, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        if context.get('active_model','') == 'stock.picking' and len(context['active_ids']) < 2:
            raise osv.except_osv(_('Warning'),
            _('Please select multiple stock pickings to check availability in the list view.'))
        return res    

    

    def do_check_availability(self, cr, uid, ids, context=None):
        
        picking_obj = self.pool.get('stock.picking')
        picking_line_obj = self.pool.get('stock.move')
        LOGGER = netsvc.Logger()
        
        if context is None:
            context = {}

      
        #search and compare with lines non avaliables

        order_picking=picking_obj.search(cr, uid, [('id','in',context['active_ids'])], order='date')

        for picking_id in order_picking:

            picking=picking_obj.browse(cr,uid,picking_id)
            
            if picking.state in ['draft','auto','confirmed']:
                LOGGER.notifyChannel('Stock Picking', netsvc.LOG_INFO, "check availability: %s." % (picking.name))
                assign=picking_obj.action_assign(cr, uid, [picking_id])
                
        
        
        return {'type': 'ir.actions.act_window_close'}

wizz_picking_check_availability()

