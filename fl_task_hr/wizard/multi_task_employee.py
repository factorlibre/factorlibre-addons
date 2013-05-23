# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Factor Libre SL (<hugosantosred@gmail.com>).
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
from dateutil.relativedelta import relativedelta

from osv import osv, fields
from tools.translate import _

class multi_task_employee(osv.osv_memory):
    _name = 'multi.task.employee'

    _columns = {
        'employee_ids': fields.many2many('hr.employee', 'hr_employee_multi_task_rel', 'emp_id', 
            'task_id', 'Employees', required=True),
        'work_activity': fields.text('Activity'),
        'work_address': fields.text('Work Address'),
        'instructions': fields.text('Instructions'),
        'uniform': fields.text('Uniform'),
        'price_hour': fields.float('Price per hour'),
        'price_km': fields.float('Price per km'),
        'price_extra_hour': fields.float('Price per extra hour'),
        'price_diet': fields.float('Price per diet'),
        'coordinator': fields.many2one('hr.employee', 'Coordinator'),
        'work_period_ids': fields.one2many('multi.task.employee.period', 'multi_task_id', 'Periods'),
    }

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        order = self.pool.get('project.task').browse(cr, uid, record_id, context=context)
        if order.state != 'open':
            raise osv.except_osv(_('Warning !'),_('You can not add employees if task is not open'))
        return False


    def create_lines(self, cr, uid, ids, context=None):
        if not context.get('active_id', False):
            raise osv.except_osv(_('Error'),_('Task not found!. Please save the record and try again'))

        task_id = context['active_id']
        task_employee_pool = self.pool.get('project.task.employee')
        work_period_pool = self.pool.get('employee.work.period')

        for obj in self.browse(cr, uid, ids, context=context):
            values = {
                'task_id': task_id,
                'work_activity': obj.work_activity,
                'work_address': obj.work_address,
                'price_hour': obj.price_hour,
                'price_km': obj.price_km,
                'price_diet': obj.price_diet,
                'price_extra_hour': obj.price_extra_hour,
                'coordinator': obj.coordinator and obj.coordinator.id,
                'instructions': obj.instructions,
                'uniform': obj.uniform
            }
            for emp in obj.employee_ids:
                values['employee_id'] = emp.id
                task_employee_id = task_employee_pool.create(cr, uid, values)

                for period in obj.work_period_ids:
                    period_values = {
                        'employee_task_id': task_employee_id,
                        'start_date': period.start_date,
                        'end_date': period.end_date
                    }
                    work_period_pool.create(cr, uid, period_values)
        return {'type': 'ir.actions.act_window_close'}

multi_task_employee()

class multi_task_employee_period(osv.osv_memory):
    _name = 'multi.task.employee.period'

    _columns ={
        'start_date': fields.datetime('Start Date', required=True),
        'end_date': fields.datetime('End Date', required=True),
        'multi_task_id': fields.many2one('multi.task.employee')
    }

    def onchange_date(self, cr, uid, ids, start_date_view, end_date_view):
        res = {}
        if start_date_view and end_date_view:
            start_date = datetime.strptime(start_date_view, "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(end_date_view, "%Y-%m-%d %H:%M:%S")
            deltadate = relativedelta(end_date, start_date)
            if abs(deltadate.days) > 1:
                res['warning'] = {
                    'title': _('Warning'),
                    'message': _('Difference between ending date and starting date not permitted')
                }
                res['value'] = {'start_date': None, 'end_date': None}
        return res

multi_task_employee_period()