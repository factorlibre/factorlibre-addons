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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import fields, osv
import pooler
import tools
from tools.translate import _

class project_task_work(osv.osv):
    _inherit = "project.task.work"

    time_slots = (
        ('ordinary','Ordinary'),
        ('nocturnal','Nocturnal'),
        ('extra','Extra'),
        ('festive','Festive')
    )

    _columns = {
        'attendance_id': fields.many2one('resource.calendar.attendance', 'Time Slot'),
        'time_slot': fields.selection(time_slots, 'Time Slot', required=True),
    }

    def create(self, cr, uid, vals, *args, **kwargs):
        obj_timesheet = self.pool.get('hr.analytic.timesheet')
        
        vals_line = {}
        context = kwargs.get('context', {})
        res = super(project_task_work,self).create(cr, uid, vals, *args, **kwargs)

        obj = self.browse(cr, uid, res, context=context)
        if obj.hr_analytic_timesheet_id and 'time_slot' in vals:
            timesheet_vals = {'time_slot': vals['time_slot']}
            if obj.task_id:
                timesheet_vals['name'] = "%s: %s" % (obj.task_id.name_get()[0][1], obj.name)

            obj_timesheet.write(cr, uid, [obj.hr_analytic_timesheet_id.id], timesheet_vals)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        obj_timesheet = self.pool.get('hr.analytic.timesheet')

        res = super(project_task_work, self).write(cr, uid, ids, vals, context=context)
        if 'time_slot' in vals:
            for obj in self.browse(cr, uid, ids, context=context):
                if obj.hr_analytic_timesheet_id:
                    timesheet_vals = {'time_slot': vals['time_slot']}
                    if obj.task_id:
                        timesheet_vals['name'] = "%s: %s" % (obj.task_id.name_get()[0][1], obj.name)
                    obj_timesheet.write(cr, uid, [obj.hr_analytic_timesheet_id.id], timesheet_vals)
        return res

project_task_work()