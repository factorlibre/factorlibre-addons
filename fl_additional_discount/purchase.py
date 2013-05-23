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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp

class purchase_order(osv.osv):
    
    _name = "purchase.order"
    _inherit = "purchase.order"
    _description = "Purchase Order"
   


    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'add_disc_amt': 0.0,
                'amount_net': 0.0,
            }
            val = val1 = val2 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               line_price_unit = line.price_unit * (1-(order.add_disc or 0.0)/100.0)
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line_price_unit, line.product_qty, order.partner_address_id.id, line.product_id.id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            val2 = val1 * order.add_disc/100
            res[order.id]['add_disc_amt'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_net'] = res[order.id]['amount_untaxed'] - res[order.id]['add_disc_amt']
            res[order.id]['amount_total'] = res[order.id]['amount_net'] + res[order.id]['amount_tax']
        return res
            
    _columns={
            
            'add_disc':fields.float('Additional Discount(%)',digits=(4,2), states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
            'add_disc_amt': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Additional Disc Amt',
                                            store =True,multi='sums', help="The additional discount on untaxed amount."),
            'amount_net': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Net Amount',
                                              store = True,multi='sums', help="The amount after additional discount."),
            'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Untaxed Amount',
                                                store=True, multi="sums", help="The amount without tax"),
            'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Taxes',
                                          store=True, multi="sums", help="The tax amount"),
            'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Total',
                                            store=True, multi="sums",help="The total amount"),
              
            }
    
        
    _defaults={
               'add_disc': 0.0,               
               }
    
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        res = False

        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')

        for order in self.browse(cr, uid, ids, context=context):
            pay_acc_id = order.partner_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error !'),
                    _('There is no purchase journal defined for this company: "%s" (id:%d)') % (order.company_id.name, order.company_id.id))

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                if po_line.product_id:
                    acc_id = po_line.product_id.product_tmpl_id.property_account_expense.id
                    if not acc_id:
                        acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
                    if not acc_id:
                        raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (po_line.product_id.name, po_line.product_id.id,))
                else:
                    acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category').id
                fpos = order.fiscal_position or False
                acc_id = fiscal_obj.map_account(cr, uid, fpos, acc_id)

                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)

                po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)

            # get invoice data and create invoice
            inv_data = {
                'name': order.partner_ref or order.name,
                'reference': order.partner_ref or order.name,
                'account_id': pay_acc_id,
                'type': 'in_invoice',
                'partner_id': order.partner_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'address_invoice_id': order.partner_address_id.id,
                'address_contact_id': order.partner_address_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, inv_lines)], 
                'origin': order.name,
                'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                'payment_term': order.partner_id.property_payment_term and order.partner_id.property_payment_term.id or False,
                'company_id': order.company_id.id,
                'add_disc': order.add_disc or 0.0
            }
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            res = inv_id
        return res
    
    
purchase_order()