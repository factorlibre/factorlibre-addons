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
    
    
    def do_split(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        #wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            state_confirmed=False
            state_assigned=False
            
            for move in pick.move_lines:
                if move.state == 'confirmed':
                    state_confirmed=True
                if move.state == 'assigned':
                    state_assigned=True
 
            
            if state_assigned==True and state_confirmed==True:
                
                    new_picking = self.copy(cr, uid, pick.id,
                            {
                                'name': sequence_obj.get(cr, uid, 'stock.picking.%s'%(pick.type)),
                                'move_lines' : [],
                                'state':'draft',
                            })
                    
                    
                    if new_picking:
                        for move in pick.move_lines:
                            if move.state == 'assigned':
                                move_obj.write(cr, uid, move.id, {'picking_id': new_picking})
                     
                        self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                        #self.action_move(cr, uid, [new_picking])
                        self.draft_force_assign(cr, uid, [new_picking])
                    
            else:
                raise osv.except_osv(_('Warning'),
            _('Stock picking must contains lines in Waiting Availability and Available.'))
                

        return res
    
    
     
    def action_split(self, cr, uid, ids, context=None):
        if context is None: context = {}
        context = dict(context, active_ids=ids, active_model=self._name)
        split_id = self.pool.get("split.picking").create(cr, uid, {}, context=context)
        return {
            'name':_("Products to Process"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'split.picking',
            'res_id': split_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context,
        }
    
    
stock_picking()
    
    

