# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
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
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import netsvc
from operator import itemgetter
from itertools import groupby


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    
    

    def _calculate_factor(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for picking in self.browse(cr, uid, ids, context=context):
            #complete factor
            cont=0
            assigned=0
            complete_factor=0
            
            if picking.state in ["confirmed"] or picking.state in ["assigned"]:
                for line in picking.move_lines:
                    if line.state == 'assigned':
                        assigned=assigned+1
                    cont=cont+1
                complete_factor=assigned*100/cont
                
                res[picking.id] = complete_factor
            else:
                res[picking.id] = 0
        
        return res


    _columns ={
               
               'partially_reserved':fields.boolean('Partially reserved'),
               'complete_factor':fields.function(_calculate_factor, string='Complete Factor', method=True, type='float'),
               #'complete_factor':fields.float('Complete Factor'),

               
               }
    

    
    def verify_assigned(self, cr, uid, ids):
       
        ok = True
        for pick in self.browse(cr, uid, ids):
            for move in pick.move_lines:
                if (move.state != 'assigned'):
                    return False
                
        return ok
    
    
    def write(self, cr, uid, ids, values, context=None):
        if context is None:
            context = {}
        if not type(ids) is list:
            ids = [ids]

        for picking in self.browse(cr, uid, ids, context=context):

            if picking.state in ["confirmed"] or picking.state in ["assigned"]:
                
                not_assigned=False
                partially_reserved=False
                values['partially_reserved']=False
                for line in picking.move_lines:
                    if line.state == 'assigned':
                        partially_reserved=True
                    else:
                        
                        not_assigned=True
                
                if not_assigned==True and partially_reserved==True:
                     values['partially_reserved']=True

            if picking.state in ["done"]:
                values['partially_reserved']=False

            #complete factor
            cont=0
            assigned=0
            for line in picking.move_lines:
                 if line.state == 'assigned':
                     assigned=assigned+1
                 cont=cont+1
            #values['complete_factor']=assigned*100/cont

                
                 
        return super(stock_picking, self).write(cr, uid, ids, values, context=context)
     
     
    

    #Metodo sobreescrito que permite comprobar disponibilidad sin error de 'No stock' en el caso de picking con movimientos cancelados y reservados.
    def action_assign(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            cancel_move_ids = [x.id for x in pick.move_lines if x.state == 'cancel']            
            all_move_ids = [x.id for x in pick.move_lines]
            assigned_move_ids = [x.id for x in pick.move_lines if x.state == 'assigned']            
            if not move_ids and len(cancel_move_ids)+len(assigned_move_ids)!=len(all_move_ids):
                raise osv.except_osv(_('Warning !'),_('Not enough stock, unable to reserve the products.'))
            if not move_ids and len(cancel_move_ids)+len(assigned_move_ids)==len(all_move_ids) and len(assigned_move_ids):
                self.pool.get('stock.picking').write(cr, uid, [pick.id], {'state': 'assigned'})
            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
        return True

stock_picking()
    
    
