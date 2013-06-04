# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    #    Copyright (C) 2012 Factor Libre.
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

class sale_order(osv.osv):
    """heredamos las facturas para añadirles el representante de venta"""

    _inherit = "sale.order"
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)
        agent_order_id=self.pool.get('sale.order.agent').search(cr, uid,[('sale_id', '=', order.id)], context=context)
        for agent_id in self.pool.get('sale.order.agent').browse(cr, uid, agent_order_id, context=context):
            invoice_vals['agent_id']=agent_id.agent_id.id
        return invoice_vals
    