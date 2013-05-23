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

class facility_facility(osv.osv):
    _name = 'facility.facility'

    def _get_attendance(self, cr, uid, ids, field, args, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = self.pool.get('resource.calendar.attendance').search(cr, uid, [
                ('calendar_id', '=', obj.calendar_id and obj.calendar_id.id)])
        return res

    _columns = {
        'code': fields.char('Code', size=20, required=True),
        'name': fields.char('Name', size=128, required=True),
        'calendar_id': fields.many2one('resource.calendar', 'Working Time'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),
        'calendar_attendance_ids': fields.function(_get_attendance, type="one2many", 
            relation="resource.calendar.attendance", string="Attendance",
            method=True),
        'partner_ids': fields.many2many('res.partner','partner_facility_rel','facility_id','partner_id','Partners'),
        'employee_ids': fields.many2many('hr.employee','employee_facility_rel','facility_id','employee_id','Employees'),
        'company_id': fields.many2one('res.company', 'Company'),
    }

facility_facility()