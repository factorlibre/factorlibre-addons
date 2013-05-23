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

import re
from osv import osv, fields
from tools.translate import _

class project_task_category(osv.osv):
    _name = 'project.task.category'

    _columns = {
        'name': fields.char('Name', size=255, translate=True, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id
    }

project_task_category()

class project_task(osv.osv):
    _inherit = 'project.task'

    TASK_NATURE = (
        ('preventive','Preventive'),
        ('corrective','Corrective'),
        #('inspection','Inspection'),
        #('official_inspection','Official Inspection')
    )

    PLAN_TYPE = (
        ('weekly', 'Weekly'),
        ('biweekly','Biweekly'),
        ('monthly','Monthly'),
        ('bimonthly','Bimonthly'),
        ('quarterly','Quartery'),
        ('biannual','Biannual'),
        ('annual','Annual')
    )

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]

        if vals.get('state', False) and not vals.get('not_check_state',False):
            for task in self.browse(cr, uid, ids, context=context):
                if task.project_id:
                    if task.project_id.state not in ['open','pending_renovation','close']:
                        raise osv.except_osv(_('Error'),_("The related project is %s. Task state can't be changed.") % task.project_id.state)

        return super(project_task, self).write(cr, uid, ids, vals, context=context)

    
    _columns = {
        'range_code': fields.char('Range Code', size=64),
        'order_number': fields.char('Order No.',size=64,readonly=True),
        'task_nature': fields.selection(TASK_NATURE, 'Nature', size=32),
        'project_range_id': fields.many2one('project.range', 'Range'),
        'category_id': fields.many2one('project.task.category', 'Category'),
        'task_type': fields.selection((('periodical','Periodical'),('especial','Especial')), 'Type'),
        'task_execution': fields.selection((('internal','Internal'),('external','External')), 'Execution'),
        'official': fields.boolean('Official'),
        'template': fields.boolean('Template?'),
        'user_ids': fields.many2many('res.users','assigned_user_task_rel','user_id','task_id', 'Workers'),
        'task_action': fields.selection((('planned','Planned'),('not_planned','Not Planned')), 'Action', readonly=True),
        'task_periodicy': fields.selection(PLAN_TYPE, 'Periodicy'),
    }

    _defaults = {
        'task_action': 'planned',
        'task_nature': 'preventive',
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for task in self.browse(cr, uid, ids, context=context):
            name = ""
            if task.template:
                name = task.range_code or task.name
            else:
                name = task.order_number or task.name
            res.append((task.id, name))
        return res

    def create(self, cr, uid, vals, context=None):
        if not vals.get('template', False):
            vals['order_number'] = self.pool.get('ir.sequence').get(cr, uid, 'project.task.order_number')
        
        return super(project_task, self).create(cr, uid, vals, context=context)

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('order_number','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('order_number',operator,name)], limit=limit, context=context))
                if len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit-len(ids)), context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('order_number','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

project_task()