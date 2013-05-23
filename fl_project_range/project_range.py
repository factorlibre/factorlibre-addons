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
from dateutil.relativedelta import relativedelta

from osv import osv, fields

class project_task_period(osv.osv):
    _name = 'project.task.period'

    _columns = {
        'code': fields.char('Code', size=16, required=True),
        'name': fields.char('Name', size=255, translate=True, required=True),
        'repeat': fields.integer('Times in a Year', required=True),
    }

project_task_period()

class project_range(osv.osv):
    _name = 'project.range'

    plan_duration_type = (
        ('month','Months'),
        ('year','Years')
    )

    _columns = {
        'name': fields.char('Planning No.', size=64, required=True, readonly=True, 
            states={'draft': [('readonly',False)]}),
        'project_id': fields.many2one('project.project', 'Project', required=True, 
            readonly=True, states={'draft': [('readonly',False)]}),
        'plan_duration_type': fields.selection(plan_duration_type, 'Plan Duration type', required=True),
        'months': fields.integer('Months', readonly=True, states={'draft': [('readonly',False)]}),
        'years': fields.integer('Years', readonly=True, states={'draft': [('readonly',False)]}),
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True),
        'date_start': fields.date('Starting Date', required=True),
        'plan_task_ids': fields.one2many('project.range.task', 'range_id', 'Task to plan', readonly=True, 
            states={'draft': [('readonly',False)]}),
        'state': fields.selection((
                ('draft','Draft'),
                ('confirm','Confirmed'),
                ('cancel','Cancel')
            ), 'State', readonly=True),
        'company_id': fields.related('project_id','company_id',type='many2one',readonly=True,relation='res.company',string='Company'),
    }

    _defaults = {
        'plan_duration_type': 'year',
        'state': 'draft',
        'years': 1,
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        project_pool = self.pool.get('project.project')
        if vals.get('project_id', False):
            project = project_pool.browse(cr, uid, vals['project_id'], context=context)
            if project.partner_id:
                vals['partner_id'] = project.partner_id.id

        return super(project_range, self).create(cr, uid, vals, context=context)


    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        project_pool = self.pool.get('project.project')
        if vals.get('project_id', False):
            project = project_pool.browse(cr, uid, vals['project_id'], context=context)
            if project.partner_id:
                vals['partner_id'] = project.partner_id.id

        return super(project_range, self).write(cr, uid, ids, vals, context=context)

            

    def onchange_project(self, cr, uid, ids, project_id):
        value = {}
        if not project_id:
            return {}
        project = self.pool.get('project.project').browse(cr, uid, project_id)
        value['partner_id'] = project.partner_id and project.partner_id.id
        return {'value': value}

    def confirm_project_range(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        period_pool = self.pool.get('project.task.period')
        task_pool = self.pool.get('project.task')

        task_periodicy = {
            'weekly': 'relativedelta(days=+7)',
            'biweekly': 'relativedelta(days=+15)',
            'monthly': 'relativedelta(months=+1)',
            'bimonthly': 'relativedelta(months=+2)',
            'quarterly': 'relativedelta(months=+3)',
            'biannual': 'relativedelta(months=+6)',
            'annual': 'relativedelta(years=+1)'                    
        }
        for obj in self.browse(cr, uid, ids, context=context):
            for task in obj.plan_task_ids:
                task_values = {
                    'name': task.name,
                    'category_id': task.task_category_id and task.task_category_id.id,
                    'project_id': obj.project_id.id,
                    'description': task.note,
                    'task_type': task.task_type,
                    'task_execution': task.task_execution,
                    'official': task.official,
                    'planned_hours': task.planned_hours,
                    'remaining_hours': task.planned_hours,
                    'project_range_id': obj.id,
                    'task_action': 'planned',
                    'range_code': task.task_id and task.task_id.range_code,
                    'category_id': task.category_id and task.category_id.id,
                    'date_start': obj.date_start,
                    'task_periodicy': task.task_periodicy,
                    'facility_id': obj.facility_id and obj.facility_id.id,
                    'partner_id': obj.partner_id and obj.partner_id.id
                }

                if task.task_type == 'periodical':
                    task_start_date = datetime.strptime(obj.date_start, '%Y-%m-%d')
                    if obj.plan_duration_type == 'year':
                        task_end_date = task_start_date
                        for y in range(obj.years):
                            year_end_date = datetime.strptime(obj.date_start, '%Y-%m-%d') + relativedelta(years=+(y+1))

                            if not task_periodicy.get(task.task_periodicy, False):
                                continue
                            while task_end_date < year_end_date:                            
                                task_values.update({
                                    'name': task.name,
                                    'date_start': str(task_start_date),
                                    'date_deadline': str(task_end_date)
                                })
                                task_start_date = task_end_date
                                task_end_date = task_end_date + eval(task_periodicy[task.task_periodicy])
                                task_pool.create(cr, uid, task_values)

                    if obj.plan_duration_type == 'month':
                        task_end_date = task_start_date
                        for m in range(obj.months):
                            month_end_date = datetime.strptime(obj.date_start, '%Y-%m-%d') + relativedelta(months=+(m+1))

                            if not task_periodicy.get(task.task_periodicy, False):
                                break
                            while task_end_date < month_end_date:
                                task_values.update({
                                    'name': task.name,
                                    'date_start': str(task_start_date),
                                    'date_deadline': str(task_end_date)
                                })
                                task_start_date = task_end_date
                                task_end_date = task_end_date + eval(task_periodicy[task.task_periodicy])
                                task_pool.create(cr, uid, task_values)

                        
                else:
                    task_pool.create(cr, uid, task_values)
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return True       


project_range()

class project_range_task(osv.osv):
    _name = 'project.range.task'

    PLAN_TYPE = (
        ('weekly', 'Weekly'),
        ('biweekly','Biweekly'),
        ('monthly','Monthly'),
        ('bimonthly','Bimonthly'),
        ('quarterly','Quartery'),
        ('biannual','Biannual'),
        ('annual','Annual')
    )

    _columns = {
        'name': fields.char('Description', size=255, required=True),
        'task_id': fields.many2one('project.task', 'Range Code', domain=[('template','=',True)]),
        'task_category_id': fields.related('task_id', 'category_id', type="many2one", relation="project.task.category",
            string="Category"),
        'note': fields.text('Note'),
        'task_type': fields.selection((('periodical','Periodical'), ('especial','Especial')), 'Type', required=True),
        'task_execution': fields.selection((('internal','Internal'),('external','External')), 'Execution'),
        'official': fields.boolean('Official'),
        'planned_hours': fields.float('Planned Hours'),
        'task_periodicy': fields.selection(PLAN_TYPE, 'Periodicy'),
        'range_id': fields.many2one('project.range', 'Range', required=True, ondelete="cascade"),
    }

    def task_type_change(self, cr, uid, ids, task_type):
        res = {}
        if task_type and task_type == 'especial':
            res['value'] = {'task_periodicy': ''}
        return res

    def onchange_task(self, cr, uid, ids, task_id):
        res = {}
        if not task_id:
            return res
        task_pool = self.pool.get('project.task')
        task = task_pool.browse(cr, uid, task_id)
        res['value'] = {
            'name': task.name,
            'note': task.description,
            'task_type': task.task_type,
            'task_execution': task.task_execution,
            'official': task.official,
            'planned_hours': task.planned_hours,
            'category_id': task.category_id and task.category_id.id or False,
            'task_periodicy': task.task_periodicy or "",
        }

        return res


project_range_task()