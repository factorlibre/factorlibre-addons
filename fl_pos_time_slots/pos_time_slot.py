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

from datetime import datetime
import pytz

from osv import osv, fields

class pos_time_slot(osv.osv):
    _name = 'pos.time.slot'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'time_start': fields.float('Time Start', required=True),
        'time_end': fields.float('Time End', required=True),
    }

pos_time_slot()

class pos_order(osv.osv):
    _inherit = 'pos.order'

    _columns = {
        'time_slot': fields.many2one('pos.time.slot', 'Time Slot'),
    }

    def write(self, cr, uid, ids, value, context=None):
        if context is None:
            context = {}

        time_slot_pool = self.pool.get('pos.time.slot')
        res = super(pos_order, self).write(cr, uid, ids, value, context=context)
        if context.get('updated_slot',False):
            return res
        if not isinstance(ids, list):
            ids = list([ids])
        for obj in self.browse(cr, uid, ids, context=context):
            if self.test_paid(cr, uid, [obj.id]):
                if not obj.time_slot:
                    if obj.date_order:
                        
                        date_order_time = datetime.strptime(obj.date_order, "%Y-%m-%d %H:%M:%S")
                        utc = pytz.UTC
                        date_order_time = utc.localize(date_order_time)
                        if obj.user_id and obj.user_id.context_tz:
                            date_order_time = date_order_time.astimezone(pytz.timezone(obj.user_id.context_tz))
                        if context.get('tz', False): #Context is not received                            
                            date_order_time = date_order_time.astimezone(pytz.timezone(context['tz']))
                        
                        minute = (date_order_time.minute / 60.0)
                        time_float = date_order_time.hour + minute
                        slot_ids = time_slot_pool.search(cr, uid, [
                            ('time_start','<=',time_float),
                            ('time_end','>=',time_float)
                        ])
                        
                        ctx2 = context.copy()
                        ctx2.update({'updated_slot': True})
                        if slot_ids:
                            self.write(cr, uid, [obj.id], {'time_slot': slot_ids[0]}, context=ctx2)
        return res

pos_order()