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
import decimal_precision as dp
from tools.translate import _
import netsvc

class project_task(osv.osv):
    _inherit = 'project.task'

    # Compute: effective_hours, total_hours, progress
    def _hours_get(self, cr, uid, ids, field_names, args, context=None):
        task_emp_states = [
            '\'confirmed\'',
            '\'pending\'',
            '\'discharged\'',
            '\'worked\'',
            '\'pending_payment\'',
            '\'paid\''
        ]
        res = {}
        query = """SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_employee
         WHERE task_id IN (%s) AND state in (%s) GROUP BY task_id""" % (
            ','.join(["%s" % id for id in ids]),
            ','.join(task_emp_states)
            )
        cr.execute(query)
        hours = dict(cr.fetchall())
        for task in self.browse(cr, uid, ids, context=context):
            #res[task.id] = {'effective_hours': hours.get(task.id, 0.0), 'total_hours': (task.remaining_hours or 0.0) + hours.get(task.id, 0.0)}
            res[task.id] = {'effective_hours': hours.get(task.id, 0.0), 'total_hours': hours.get(task.id, 0.0)}
            res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
            res[task.id]['progress'] = 0.0
            if (task.remaining_hours + hours.get(task.id, 0.0)):
                res[task.id]['progress'] = round(min(100.0 * hours.get(task.id, 0.0) / res[task.id]['total_hours'], 99.99),2)
            if task.state in ('done','cancelled'):
                res[task.id]['progress'] = 100.0
        return res

    def _get_task(self, cr, uid, ids, context=None):
        result = {}
        for work in self.pool.get('project.task.work').browse(cr, uid, ids, context=context):
            if work.task_id: result[work.task_id.id] = True
        return result.keys()

    _columns = {
        'task_employee_ids': fields.one2many('project.task.employee', 'task_id', 'Employees',
            states={'open':[('readonly',False)]}, readonly=True),
        'dificulty': fields.char('Dificulty', size=32),
        'user_ids': fields.many2many('res.users','assigned_user_task_rel','user_id','task_id', 'Assigned to'),
        'effective_hours': fields.function(_hours_get, string='Hours Spent', multi='hours', help="Computed using the sum of the task work done.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['task_employee_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.employee': (_get_task, ['hours'], 10),
            }),
        'total_hours': fields.function(_hours_get, string='Total Hours', multi='hours', help="Computed as: Time Spent + Remaining Time.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['task_employee_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.employee': (_get_task, ['hours'], 10),
            }),
        'progress': fields.function(_hours_get, string='Progress (%)', multi='hours', group_operator="avg", help="If the task has a progress of 99.99% you should close the task if it's finished or reevaluate the time",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['task_employee_ids', 'remaining_hours', 'planned_hours','state'], 10),
                'project.task.employee': (_get_task, ['hours'], 10),
            }),
        'delay_hours': fields.function(_hours_get, string='Delay Hours', multi='hours', help="Computed as difference between planned hours by the project manager and the total hours of the task.",
            store = {
                'project.task': (lambda self, cr, uid, ids, c={}: ids, ['task_employee_ids', 'remaining_hours', 'planned_hours'], 10),
                'project.task.employee': (_get_task, ['hours'], 10),
            }),
    }

    def discharge_employees(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj in self.browse(cr, uid, ids, context=context):
            for emp in obj.task_employee_ids:
                if emp.state == 'pending':
                    wf_service.trg_validate(uid, 'project.task.employee', emp.id, 'discharge_employee', cr)
        return True

    def mark_as_worked(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj in self.browse(cr, uid, ids, context=context):
            for emp in obj.task_employee_ids:
                if emp.state == 'discharged':
                    wf_service.trg_validate(uid, 'project.task.employee', emp.id, 'mark_as_worked', cr)
        return True

    def payment_pending(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj in self.browse(cr, uid, ids, context=context):
            for emp in obj.task_employee_ids:
                if emp.state == 'worked':
                    wf_service.trg_validate(uid, 'project.task.employee', emp.id, 'pending_payment', cr)
        return True

    def pay_employees(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for obj in self.browse(cr, uid, ids, context=context):
            for emp in obj.task_employee_ids:
                if emp.state == 'pending_payment':
                    wf_service.trg_validate(uid, 'project.task.employee', emp.id, 'pay_employee', cr)
        return True

    def map_employee(self, cr, uid, old_task_id, new_task_id, context=None):
        """ copy and map employees from old to new task """
        if context is None:
            context = {}
        map_emp_id = {}
        emp_obj = self.pool.get('project.task.employee')
        task = self.browse(cr, uid, old_task_id, context=context)
        for emp in task.task_employee_ids:
            map_emp_id[emp.id] =  emp_obj.copy(cr, uid, emp.id, {}, context=context)
        self.write(cr, uid, new_task_id, {'task_employee_ids':[(6,0, map_emp_id.values())]})
        #emp_obj.duplicate_task(cr, uid, map_task_id, context=context)
        return True

    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}

        default = default or {}
        res = super(project_task, self).copy(cr, uid, id, default, context)
        self.map_employee(cr,uid,id,res,context)
        return res

    def copy_data(self, cr, uid, id, default={}, context=None):
        default = default or {}      
        default['task_employee_ids'] = []
        return super(project_task, self).copy_data(cr, uid, id, default, context)


project_task()

class project_task_employee(osv.osv):
    _name = 'project.task.employee'

    _rec_name = 'employee_id'

    #Funcion para calcular las horas del empleado que tiene asignadas en sus periodos.
    def _calculate_hours(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            hours = 0
            for period in obj.work_period_ids:
                end_date = datetime.strptime(period.end_date, "%Y-%m-%d %H:%M:%S")
                start_date = datetime.strptime(period.start_date, "%Y-%m-%d %H:%M:%S")
                deltadate = relativedelta(end_date, start_date)
                hours += deltadate.hours + (deltadate.minutes / 60.0)
            res[obj.id] = hours
        return res

    def _calculate_dates(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'start_date': None,
                'end_date': None,
            }
            min_start_date = False
            max_end_date = False
            for period in obj.work_period_ids:
                if not min_start_date and not max_end_date:
                    min_start_date = period.start_date
                    max_end_date = period.end_date
                    continue
                min_date = datetime.strptime(min_start_date, "%Y-%m-%d %H:%M:%S")
                max_date = datetime.strptime(max_end_date, "%Y-%m-%d %H:%M:%S")
                start_date = datetime.strptime(period.start_date, "%Y-%m-%d %H:%M:%S")
                end_date = datetime.strptime(period.end_date, "%Y-%m-%d %H:%M:%S")

                if min_date > start_date:
                    min_start_date = period.start_date
                if end_date > max_date:
                    max_end_date = period.end_date

            res[obj.id]['start_date'] = min_start_date
            res[obj.id]['end_date'] = max_end_date

        return res

    def _calculate_totals(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for emp in self.browse(cr, uid, ids, context=context):
            res[emp.id] = {
                'subtotal_hour': 0.0,
                'subtotal_km': 0.0,
                'subtotal_extra_hour': 0.0,
                'subtotal_diet': 0.0
            }
            res[emp.id]['subtotal_hour'] = (emp.hours * emp.price_hour) #cur_obj.round(cr, uid, (emp.hours * emp.price_hour))
            res[emp.id]['subtotal_km'] = (emp.km * emp.price_km) #cur_obj.round(cr, uid, (emp.km * emp.price_km))
            res[emp.id]['subtotal_extra_hour'] = (emp.extra_hour * emp.price_extra_hour) #cur_obj.round(cr, uid, (emp.extra_hour * emp.price_extra_hour))
            res[emp.id]['subtotal_diet'] = (emp.price_diet * emp.diets) #cur_obj.round(cr, uid, (emp.price_diet * emp.diets))
        return res

    def _get_task_employee(self, cr, uid, ids, context=None):
        result = {}
        for period in self.pool.get('employee.work.period').browse(cr, uid, ids, context=context):
            result[period.employee_task_id.id] = True
        return result.keys()

    ro_states_pending = {
        'draft': [('readonly', False)],
        'selected': [('readonly', False)],
        'confirmed': [('readonly', False)],
        'pending': [('readonly', False)]
    }

    ro_states_payment_pending = {
        'draft': [('readonly', False)],
        'selected': [('readonly', False)],
        'confirmed': [('readonly', False)],
        'pending': [('readonly', False)],
        'discharged': [('readonly', False)],
        'worked': [('readonly', False)]
    }

    _columns = {
        'task_id': fields.many2one('project.task', 'Task', select=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True,
            readonly=True, states={'draft': [('readonly', False)],'selected': [('readonly', False)]}, select=True),
        'employee_phone': fields.related('employee_id','mobile_phone', type="char", readonly=True, string="Mobile Phone"),
        'employee_mail': fields.related('employee_id','work_email', type="char", readonly=True, string="E-mail"),
        'work_address': fields.text('Work Address', 
            readonly=True, states=ro_states_pending),
        'work_activity': fields.text('Activity', readonly=True, states=ro_states_pending),
        'uniform': fields.text('Uniform', readonly=True, states=ro_states_pending),
        'instructions': fields.text('Instructions', readonly=True, states=ro_states_pending),
        'work_period_ids': fields.one2many('employee.work.period', 'employee_task_id', 'Periods',
            readonly=True, states=ro_states_pending),
        'hours': fields.function(_calculate_hours, method=True, type='float', 
            string="Hours",
            store = {
                'project.task.employee': (lambda self, cr, uid, ids, c={}: ids, ['work_period_ids'], 10),
                'employee.work.period': (_get_task_employee, ['start_date', 'end_date'], 10),
            }),
        'price_hour': fields.float('Price Per Hour', digits_compute= dp.get_precision('Sale Price'),
            readonly=True, states=ro_states_pending),
        'subtotal_hour': fields.function(_calculate_totals, multi='sums', type='float', 
            digits_compute= dp.get_precision('Sale Price'), string="Subtotal (Hours)"),
        'km': fields.float('Km.', readonly=True, states=ro_states_payment_pending),
        'price_km': fields.float('Price per Km', digits_compute= dp.get_precision('Sale Price'), 
            readonly=True, states=ro_states_payment_pending),
        'subtotal_km': fields.function(_calculate_totals, multi='sums', type='float', 
            digits_compute= dp.get_precision('Sale Price'), string= "Subtotal (Km)"),
        'extra_hour': fields.float('Extra Hour', readonly=True, states=ro_states_payment_pending),
        'price_extra_hour': fields.float('Price per Extra Hour', digits_compute= dp.get_precision('Sale Price'), 
            readonly=True, states=ro_states_payment_pending),
        'subtotal_extra_hour': fields.function(_calculate_totals, multi='sums', type='float', 
            digits_compute= dp.get_precision('Sale Price'), string="Subtotal (Extra Hour)"),
        'diets': fields.float('Diets', readonly=True, states=ro_states_payment_pending),
        'price_diet': fields.float('Price per diet', digits_compute= dp.get_precision('Sale Price'),
            readonly=True, states=ro_states_payment_pending),
        'subtotal_diet': fields.function(_calculate_totals, multi='sums', type='float', 
            digits_compute= dp.get_precision('Sale Price'), string='Subtotal (Diets)'),
        'other_cost': fields.float('Other Cost', readonly=True, states=ro_states_payment_pending),
        'observations': fields.text('observations', readonly=True, states=ro_states_payment_pending),
        'self_employed': fields.boolean('Self Employeed', readonly=True, states=ro_states_pending),
        'coordinator': fields.many2one('hr.employee','Coordinator', readonly=True, states=ro_states_payment_pending, select=True),
        'start_date': fields.function(_calculate_dates, type='date', multi='sums', string="Start Date", select=True),
        'end_date': fields.function(_calculate_dates, type='date', multi='sums', string="End Date", select=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'state': fields.selection(
                (('draft','Draft'),
                 ('selected','Selected'),
                 ('reserve','Reserve'),
                 ('confirmed','Confirmed'),
                 ('pending','Contract Pending'),
                 ('discharged','Discharged'),
                 ('worked','Worked'),
                 ('pending_payment','Pending Payment'),
                 ('paid','Paid'),
                 ('cancel','Void')),
            'state', readonly=True, select=True), 
    }

    _defaults = {
        'state': 'selected',
    }

    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}

        default = default or {}
        default['state'] = 'selected'
        default['work_period_ids'] = []
        default['km'] = 0.0
        default['diets'] = 0.0
        default['other_cost'] = 0.0
        default['extra_hour'] = 0.0
        return super(project_task_employee, self).copy(cr, uid, id, default=default, context=context)

    def contract_pending(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('hr.contract')
        for emp in self.browse(cr, uid, ids, context=context):
            contract_val = {
                'name': "%s - %s" % (emp.task_id.name, emp.employee_id.name),
                'employee_id': emp.employee_id.id,
                'wage': emp.subtotal_hour,
                'date_start': emp.start_date,
                'date_end': emp.end_date,
            }
            contract_obj.create(cr, uid, contract_val)
        self.write(cr, uid, ids, {'state': 'pending'})
        return True

    def discharge_employee(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'discharged'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        task_employee = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in task_employee:
            if t['state'] in ['draft', 'cancel']:
                unlink_ids.append(t['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('In order to delete an employee record, you must cancel it before !'))

        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    def button_dummy(self, cr, uid, ids, context=None):
        return True


project_task_employee()

class employee_work_period(osv.osv):
    _name = 'employee.work.period'

    _columns = {
        'start_date': fields.datetime('Start Date', required=True),
        'end_date': fields.datetime('End Date', required=True),
        'employee_task_id': fields.many2one('project.task.employee')
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

employee_work_period()