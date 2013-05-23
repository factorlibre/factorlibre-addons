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
from tools.translate import _

class hr_analytic_timesheet(osv.osv):
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'pricelist_id': fields.related('account_id', 'pricelist_id', type="many2one", 
            relation="product.pricelist", string="Pricelist", readonly=True),
    }

    # Cambia el calculo del precio de coste de las lineas de contabilidad analitica
    # def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount, company_id, 
    #   unit=False, journal_id=False, context=None):
    #     pricelist_pool = self.pool.get('product.pricelist')

    #     res = super(hr_analytic_timesheet, self).on_change_unit_amount(cr, uid, id, 
    #         prod_id, unit_amount, company_id, unit=unit, journal_id=journal_id, 
    #         context=context)

    #     if id:
    #         obj = self.browse(cr, uid, id, context=context)
    #         if obj.pricelist_id:
    #             price_unit = pricelist_pool.price_get(cr, uid, [obj.pricelist_id.id], prod_id,
    #                 unit_amount)
    #             res['value'].update({'amount': price_unit[prod_id]}) 
    #     return res
hr_analytic_timesheet()