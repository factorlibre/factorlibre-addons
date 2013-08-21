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

    
    
    
    
    def do_reset_state(self, cr, uid, ids, context=None):
        
        
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        
        for pick in self.browse(cr, uid, ids, context=context):
            
            for move in pick.move_lines:
                move_obj.write(cr, uid, [move.id], {'state': 'draft'})
  
            self.pool.get('stock.picking').write(cr, uid, [pick.id], {'state': 'draft'})
            wf_service.trg_delete(uid, 'stock.picking', pick.id, cr)
            wf_service.trg_create(uid, 'stock.picking', pick.id, cr)
            
            

        return True
    
    
    

stock_picking()
    
    

