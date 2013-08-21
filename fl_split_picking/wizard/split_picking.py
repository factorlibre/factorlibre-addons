# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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

from osv import fields, osv
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time



class split_picking(osv.osv_memory):
    _name = "split.picking"
    _inherit = 'stock.partial.picking'
    
    _columns = {
        'date': fields.datetime('Date'),
        'move_ids' : fields.one2many('split.picking.line', 'wizard_id', 'Moves'),

        # picking_id is not used for move processing, so we remove the required attribute
        # from the inherited column, and ignore it
        'picking_id': fields.many2one('stock.picking', 'Picking'),
     }

    
    
    def _split_move_for(self, cr, uid, move):
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' :  move.product_qty,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
        }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move
    
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = {}
        picking_ids = context.get('active_ids', [])
        if not picking_ids or (not context.get('active_model') == 'stock.picking') \
            or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            moves = [self._split_move_for(cr, uid, m) for m in picking.move_lines if m.state not in ('done','cancel')]
            res.update(move_ids=moves)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res
    
    
    

    def do_split(self, cr, uid, ids, context=None):
        self.pool.get('stock.picking').do_split( cr, uid, context['active_ids'], context)
        return {'type': 'ir.actions.act_window_close'}
    
    
class split_picking_line(osv.osv_memory):
    _name = "split.picking.line"
    _inherit = "stock.partial.picking.line"
    
    _columns = {
        'wizard_id' : fields.many2one('split.picking', string="Split picking", ondelete='CASCADE'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
