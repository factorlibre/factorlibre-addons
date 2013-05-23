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

from osv import osv, fields
from tools import float_compare, ustr
from tools.translate import _
from datetime import datetime

class project_task_extraordinary_expenses(osv.osv):
    _name = 'project.task.extraordinary.expenses'

    _columns = {
        'name': fields.char('Description', size=255, required=True),
        'amount': fields.float('Amount', required=True),
        'account_analytic_line_id': fields.many2one('account.analytic.line','Analytic Line'),
        'task_id': fields.many2one('project.task', 'Work Order'),
        'user_id': fields.many2one('res.users', 'Made By', required=True),
        'company_id': fields.related('user_id','company_id',type='many2one',readonly=True,relation='res.company',string='Company')
    }


    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def create(self, cr, uid, vals, *args, **kwargs):
        obj_timesheet = self.pool.get('account.analytic.line')
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        journal_obj = self.pool.get('account.analytic.journal')
        account_obj = self.pool.get('account.account')
        product_obj = self.pool.get('product.product')
        unit_obj = self.pool.get('product.uom')
        
        vals_line = {}
        context = kwargs.get('context', {})
        if not context.get('no_analytic_entry',False):
            journal_ids = journal_obj.search(cr, uid, [('code','=','EXP')])
            if not journal_ids:
                raise osv.except_osv(_('Error!'),_('You must create an analytic journal with code EXP for extraordinary expenses'))
            account_ids = False
            parent_account_ids = account_obj.search(cr, uid, [('code','=','678')])
            if parent_account_ids:
                account_ids = account_obj.search(cr, uid, [('parent_id','=',parent_account_ids[0])])
            if not account_ids and not account_ids[0]:
                raise osv.except_osv(_('Error!'),_('Expense account not found for company, please install the accounting plan for that company'))

            obj_task = task_obj.browse(cr, uid, vals['task_id'])
            vals_line['name'] = '%s: %s' % (ustr(obj_task.name_get()[0][1]), ustr(vals.get('name','')) or '/')
            vals_line['unit_amount'] = 1
            #Poner a unidades
            unit_ids = unit_obj.search(cr, uid, [('name','=','PCE')])
            if unit_ids:
                vals_line['product_uom_id'] = unit_ids[0]

            
            acc_id = obj_task.project_id and obj_task.project_id.analytic_account_id.id or False
            if acc_id:
                vals_line['account_id'] = acc_id
                res = obj_timesheet.on_change_account_id(cr, uid, False, acc_id)
                if res.get('value'):
                    vals_line.update(res['value'])
                vals_line['general_account_id'] = account_ids[0]
                if journal_ids:
                    vals_line['journal_id'] = journal_ids[0]
                vals_line['amount'] = -(vals.get('amount', 0.0))
                
                timeline_id = obj_timesheet.create(cr, uid, vals=vals_line, context=context)
                vals['account_analytic_line_id'] = timeline_id
        return super(project_task_extraordinary_expenses,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        journal_obj = self.pool.get('account.analytic.journal')
        result = {}
        journal_ids = journal_obj.search(cr, uid, [('code','=','EXP')])
        if not journal_ids:
            raise osv.except_osv(_('Error!'),_('You must create an analytic journal with code EXP for extraordinary expenses'))
        
        if isinstance(ids, (long, int)):
            ids = [ids,]

        for expense in self.browse(cr, uid, ids, context=context):
            line_id = expense.account_analytic_line_id
            if not line_id:
                # if a record is deleted from timesheet, the line_id will become
                # null because of the foreign key on-delete=set null
                continue
            
            vals_line = {}
            if 'name' in vals:
                vals_line['name'] = '%s: %s' % (ustr(expense.task_id.name_get()[0][1]), ustr(vals['name']) or '/')

            if 'amount' in vals:
                vals_line['amount'] = -(vals['amount'])

            self.pool.get('account.analytic.line').write(cr, uid, [line_id.id], vals_line, context=context)
            
        return super(project_task_extraordinary_expenses,self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, *args, **kwargs):
        aal_obj = self.pool.get('account.analytic.line')
        aal_ids = []
        for expense in self.browse(cr, uid, ids):
            if expense.account_analytic_line_id:
                aal_ids.append(expense.account_analytic_line_id.id)
        if aal_ids:
            aal_obj.unlink(cr, uid, aal_ids, *args, **kwargs)
        return super(project_task_extraordinary_expenses,self).unlink(cr, uid, ids, *args, **kwargs)

project_task_extraordinary_expenses() 

class project_task_material(osv.osv):
    _name = 'project.task.material'

    _rec_name = 'product_id'

    def _allowed_warehouses(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        warehouse_ids = []

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.user_id:
                hr_user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',obj.user_id.id)])
                if hr_user_ids:
                    employee = self.pool.get('hr.employee').browse(cr, uid, hr_user_ids[0])
                    for facility in employee.facility_ids:
                        if facility.warehouse_id:
                            warehouse_ids.append(facility.warehouse_id.id)
            res[obj.id] = warehouse_ids
        return res

    def _allowed_users(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        user_ids = []

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.task_id:
                user_ids = map(lambda u: u.id, obj.task_id.user_ids)
                user_ids.append(obj.task_id.user_id.id)
            res[obj.id] = user_ids
        return res

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'qty': fields.float('Qty.'),
        'product_uom': fields.many2one('product.uom', 'Product UOM.', required=True),
        'description': fields.text('Description'),
        'task_id': fields.many2one('project.task', 'Work Order', required=True),
        'account_analytic_line_id': fields.many2one('account.analytic.line', 'Analytic Line'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
        'allowed_warehouses': fields.function(_allowed_warehouses, type="one2many", relation="stock.warehouse",
            string="Allowed Warehouses", method=True),
        'allowed_users': fields.function(_allowed_users, type="one2many", relation="res.users", 
            string="Users", method=True),
        'user_id': fields.many2one('res.users', 'Made By', required=True),
        'company_id': fields.related('user_id','company_id',type='many2one',readonly=True,relation='res.company',string='Company')
    }

    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def onchange_task_id(self, cr, uid, ids, task_id):
        if not task_id:
            return {}
        user_ids = []
        task = self.pool.get('project.task').browse(cr, uid, task_id)
        user_ids = map(lambda u: u.id, task.user_ids)
        user_ids.append(task.user_id.id)
        return {'value': {'allowed_users': user_ids}}

    def onchange_user_id(self, cr, uid, ids, user_id):
        if not user_id:
            return {}
        warehouse_ids = []
        hr_user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',user_id)])
        if hr_user_ids:
            employee = self.pool.get('hr.employee').browse(cr, uid, hr_user_ids[0])
            for facility in employee.facility_ids:
                if facility.warehouse_id:
                    warehouse_ids.append(facility.warehouse_id.id)
        return {'value': {'allowed_warehouses': warehouse_ids}}


    def create(self, cr, uid, vals, *args, **kwargs):
        obj_timesheet = self.pool.get('account.analytic.line')
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')
        journal_obj = self.pool.get('account.analytic.journal')
        
        vals_line = {}
        context = kwargs.get('context', {})
        if not context.get('no_analytic_entry',False):
            journal_ids = journal_obj.search(cr, uid, [('code','=','MAT')])
            if not journal_ids:
                raise osv.except_osv(_('Error!'),_('You must create an analytic journal with code MAT for materials'))
            prod = prod_obj.browse(cr, uid, vals['product_id'], context=context)

            obj_task = task_obj.browse(cr, uid, vals['task_id'])
            vals_line['name'] = '%s: %s' % (ustr(obj_task.name_get()[0][1]), ustr(prod.name) or '/')
            #vals_line['user_id'] = vals['user_id']
            vals_line['product_id'] = vals['product_id']
            #vals_line['date'] = vals['date'][:10]
            
            #calculate quantity based on employee's product's uom 
            vals_line['unit_amount'] = vals['qty']

            default_uom = vals['product_uom']
            
            acc_id = obj_task.project_id and obj_task.project_id.analytic_account_id.id or False
            if acc_id:
                vals_line['account_id'] = acc_id
                res = obj_timesheet.on_change_account_id(cr, uid, False, acc_id)
                if res.get('value'):
                    vals_line.update(res['value'])
                vals_line['general_account_id'] = prod.product_tmpl_id.property_account_expense and prod.product_tmpl_id.property_account_expense.id \
                    or prod.categ_id.property_account_expense_categ and prod.categ_id.property_account_expense_categ.id
                if journal_ids:
                    vals_line['journal_id'] = journal_ids[0]
                vals_line['amount'] = 0.0
                vals_line['product_uom_id'] = vals['product_uom']
                amount = vals_line['unit_amount']
                prod_id = vals_line['product_id']
                unit = False
                timeline_id = obj_timesheet.create(cr, uid, vals=vals_line, context=context)
                # Compute based on pricetype
                amount_unit = obj_timesheet.on_change_unit_amount(cr, uid, timeline_id,
                    prod_id, amount, False, unit=unit, journal_id=vals_line['journal_id'], context=context)
                if amount_unit and 'amount' in amount_unit.get('value',{}):
                    updv = { 'amount': amount_unit['value']['amount'] }
                    obj_timesheet.write(cr, uid, [timeline_id], updv, context=context)
                vals['account_analytic_line_id'] = timeline_id
        return super(project_task_material,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        timesheet_obj = self.pool.get('account.analytic.line')
        project_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')
        journal_obj = self.pool.get('account.analytic.journal')
        result = {}
        journal_ids = journal_obj.search(cr, uid, [('type','=','purchase')])
        if not journal_ids:
            raise osv.except_osv(_('Error!'),_('You must create an analytic journal of purchase type'))
        
        if isinstance(ids, (long, int)):
            ids = [ids,]

        for task in self.browse(cr, uid, ids, context=context):
            line_id = task.account_analytic_line_id
            if not line_id:
                # if a record is deleted from timesheet, the line_id will become
                # null because of the foreign key on-delete=set null
                continue
            
            vals_line = {}
            prod = task.product_id
            default_uom = task.product_uom.id
            if 'product_id' in vals:
                prod = prod_obj.browse(cr, uid, vals['product_id'], context=context)
                vals_line['name'] = '%s: %s' % (ustr(task.task_id.name_get()[0][1]), ustr(prod.name) or '/')
                vals_line['product_id'] = vals['product_id']

            if 'product_uom' in vals:
                default_uom = vals['product_uom']
                        
            if 'qty' in vals:
                vals_line['unit_amount'] = vals['qty']
                vals_line['journal_id'] = journal_ids and journal_ids[0]
                prod_id = vals_line.get('product_id', line_id.product_id.id) # False may be set

                if result.get('product_uom_id',False) and (not result['product_uom_id'] == default_uom):
                    vals_line['unit_amount'] = uom_obj._compute_qty(cr, uid, default_uom, vals['qty'], result['product_uom_id'])
                    
                # Compute based on pricetype
                amount_unit = timesheet_obj.on_change_unit_amount(cr, uid, line_id.id,
                    prod_id, vals_line['unit_amount'], False, unit=False, journal_id=vals_line['journal_id'], context=context)

                if amount_unit and 'amount' in amount_unit.get('value',{}):
                    vals_line['amount'] = amount_unit['value']['amount']

            self.pool.get('account.analytic.line').write(cr, uid, [line_id.id], vals_line, context=context)
            
        return super(project_task_material,self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, *args, **kwargs):
        aal_obj = self.pool.get('account.analytic.line')
        aal_ids = []
        for task in self.browse(cr, uid, ids):
            if task.account_analytic_line_id:
                aal_ids.append(task.account_analytic_line_id.id)
        if aal_ids:
            aal_obj.unlink(cr, uid, aal_ids, *args, **kwargs)
        return super(project_task_material,self).unlink(cr, uid, ids, *args, **kwargs)

    def product_id_change(self, cr, uid, ids, product, qty=0,
            uom=False, context=None):
        context = context or {}
        warning = {}
        result = {'qty': qty or 1}
        warning_msgs = ""
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')

        if not product:
            return {'value': {'qty': 0, 'product_uom': False}, 'domain': {'product_uom': []}}
        product_obj = product_obj.browse(cr, uid, product, context=context)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
       
        domain = {}
        if (not uom):
            result['product_uom'] = product_obj.uom_id.id
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)]}

        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}

project_task_material()

class project_task(osv.osv):
    _inherit = 'project.task'

    _columns = {
        'task_material_ids': fields.one2many('project.task.material', 'task_id', 'Task Materials'),
        'extraordinary_expenses_ids': fields.one2many('project.task.extraordinary.expenses', 'task_id', 'Extraordinary Expenses')
    }

    def do_close(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        location_obj = self.pool.get('stock.location')

        for task in self.browse(cr, uid, ids, context=context):
            if task.task_material_ids:
                picking_value = {
                    'company_id': task.company_id and task.company_id.id,
                    'type': 'out',
                }
                picking_id = picking_obj.create(cr, uid, picking_value, context=context)
                for task_material in task.task_material_ids:
                    move_value = {
                        'picking_id': picking_id,
                        'product_id': task_material.product_id.id,
                        'product_qty': task_material.qty,
                        'product_uom': task_material.product_uom.id,
                        'name': task_material.product_id.name_get()[0][1],
                        'date': datetime.now(),
                        'date_expected': datetime.now(),
                        'location_id': task_material.warehouse_id.lot_stock_id.id,
                        'location_dest_id': task_material.warehouse_id.lot_output_id.id
                    }
                    move_obj.create(cr, uid, move_value, context=context)

        return super(project_task, self).do_close(cr, uid, ids, context=context)

    def copy_data(self, cr, uid, id, default={}, context=None):
        default = default or {}
        default.update({'task_material_ids': []})
        return super(project_task, self).copy_data(cr, uid, id, default=default, context=context)

project_task()