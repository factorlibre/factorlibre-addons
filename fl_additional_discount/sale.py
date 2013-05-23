# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Hugo Santos (<http://factorlibre.com>).
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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import netsvc

class sale_order(osv.osv):

    _name = 'sale.order'
    _inherit = 'sale.order'

    def _amount_line_tax(self, cr, uid, line, discounts=0, context=None):
        val = 0.0
        line_price_unit = (line.price_unit * (1-(line.discount or 0.0)/100.0)) - abs(discounts)
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line_price_unit, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'add_disc_amt': 0.0,
                'amount_net': 0.0,
                }
            val = val1 = val_discount = 0.0
            cur = order.pricelist_id.currency_id
            val_discount = 0
            for line in order.order_line:
                line_discounts = 0                
                if order.add_disc > 0 and order.add_disc <= 100:
                    val2 = (line.price_subtotal) * order.add_disc/100.0
                    val_discount  += val2
                    line_discounts = -1 * (line.price_unit * order.add_disc/100.0)
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, discounts=line_discounts, context=context)
            res[order.id]['add_disc_amt'] = cur_obj.round(cr, uid, cur, val_discount)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_net'] = res[order.id]['amount_untaxed'] - res[order.id]['add_disc_amt']
            res[order.id]['amount_total'] = res[order.id]['amount_net'] + res[order.id]['amount_tax']
        return res


    _columns = {
            
            'add_disc':fields.float('Additional Discount(%)',digits=(4,2), readonly=True, states={'draft': [('readonly', False)]}),
            'add_disc_amt': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Additional Disc Amt',
                                            store =True,multi='sums', help="The additional discount on untaxed amount."),
            'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
                                              store = True,multi='sums', help="The amount without tax."),
            'amount_net': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Net Amount',
                                              store = True,multi='sums', help="The amount after additional discount."),                                              
            'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
                                          store = True,multi='sums', help="The tax amount."),
            'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
                                            store = True,multi='sums', help="The total amount."),
        }
    
    _defaults={
               'add_disc': 0.0,               
               }
    
    
    def _make_invoice(self, cr, uid, order, lines, context=None):
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}

        journal_ids = journal_obj.search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error !'),
                _('There is no sales journal defined for this company: "%s" (id:%d)') % (order.company_id.name, order.company_id.id))
        a = order.partner_id.property_account_receivable.id
        pay_term = order.payment_term and order.payment_term.id or False
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        inv = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': a,
            'partner_id': order.partner_id.id,
            'journal_id': journal_ids[0],
            'address_invoice_id': order.partner_invoice_id.id,
            'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice',False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            'add_disc': order.add_disc or 0.0
        }
        inv.update(self._inv_get(cr, uid, order))
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id
    
    
        
sale_order()
