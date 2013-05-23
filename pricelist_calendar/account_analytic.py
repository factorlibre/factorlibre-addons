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

import time

from osv import osv, fields
from tools.translate import _

class account_analytic_line(osv.osv):
    _inherit = "account.analytic.line"

    time_slots = (
        ('ordinary','Ordinary'),
        ('nocturnal','Nocturnal'),
        ('extra','Extra'),
        ('festive','Festive')
    )

    _columns = {
        'attendance_id': fields.many2one('resource.calendar.attendance', 'Attendance'),
        'time_slot': fields.selection(time_slots, 'Time Slot'),
    }

    #
    # data = {
    #   'date': boolean
    #   'time': boolean
    #   'name': boolean
    #   'price': boolean
    #   'product': many2one id
    # }
    def invoice_cost_create(self, cr, uid, ids, data={}, context=None):
        analytic_account_obj = self.pool.get('account.analytic.account')
        res_partner_obj = self.pool.get('res.partner')
        account_payment_term_obj = self.pool.get('account.payment.term')
        invoice_obj = self.pool.get('account.invoice')
        product_obj = self.pool.get('product.product')
        invoice_factor_obj = self.pool.get('hr_timesheet_invoice.factor')
        pro_price_obj = self.pool.get('product.pricelist')
        fiscal_pos_obj = self.pool.get('account.fiscal.position')
        product_uom_obj = self.pool.get('product.uom')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoices = []
        if context is None:
            context = {}

        account_ids = {}
        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids, context=context):
            account_ids[line.account_id.id] = True

        account_ids_dict = dict(account_ids)
        account_ids = account_ids.keys() #data['accounts']

        for account in analytic_account_obj.browse(cr, uid, account_ids, context=context):
            partner = account.partner_id
            if (not partner) or not (account.pricelist_id):
                raise osv.except_osv(_('Analytic Account incomplete'),
                        _('Please fill in the Partner or Customer and Sale Pricelist fields in the Analytic Account:\n%s') % (account.name,))

            if not partner.address:
                raise osv.except_osv(_('Partner incomplete'),
                        _('Please fill in the Address field in the Partner: %s.') % (partner.name,))

            date_due = False
            if partner.property_payment_term:
                pterm_list= account_payment_term_obj.compute(cr, uid,
                        partner.property_payment_term.id, value=1,
                        date_ref=time.strftime('%Y-%m-%d'))
                if pterm_list:
                    pterm_list = [line[0] for line in pterm_list]
                    pterm_list.sort()
                    date_due = pterm_list[-1]

            curr_invoice = {
                'name': time.strftime('%d/%m/%Y')+' - '+account.name,
                'partner_id': account.partner_id.id,
                'address_contact_id': res_partner_obj.address_get(cr, uid,
                    [account.partner_id.id], adr_pref=['contact'])['contact'],
                'address_invoice_id': res_partner_obj.address_get(cr, uid,
                    [account.partner_id.id], adr_pref=['invoice'])['invoice'],
                'payment_term': partner.property_payment_term.id or False,
                'account_id': partner.property_account_receivable.id,
                'currency_id': account.pricelist_id.currency_id.id,
                'date_due': date_due,
                'fiscal_position': account.partner_id.property_account_position.id
            }
            last_invoice = invoice_obj.create(cr, uid, curr_invoice, context=context)
            invoices.append(last_invoice)
            account_ids_dict[account.id] = last_invoice

        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids, context=context):
            context2 = context.copy()
            qty = line.unit_amount
            if not line.to_invoice:
                continue
            factor_id = line.to_invoice.id
            uom = line.product_uom_id.id

            if account_ids_dict[line.account_id.id]:
                invoice = self.pool.get('account.invoice').browse(cr, uid, account_ids_dict[line.account_id.id],
                    context=context)
                context2['lang'] = invoice.partner_id.lang
                factor_name = ''
                factor = invoice_factor_obj.browse(cr, uid, factor_id, context2)

                if factor.customer_name:
                    factor_name = line.name+' - '+factor.customer_name
                else:
                    factor_name = line.name

                if line.product_id:
                 
                    product_id = line.product_id.id

                    product = product_obj.browse(cr, uid, product_id, context2)                    
                    
                    if data.get('product', False):
                        data['product'] = data['product'][0]
                        factor_name = product_obj.name_get(cr, uid, [data['product']], context=context)[0][1]

                    ctx =  context.copy()
                    ctx.update({'uom':uom})
                    if account.pricelist_id:
                        price = 0.0
                        pl = account.pricelist_id.id
                        if line.time_slot:
                            price = pro_price_obj.price_get_calendar(cr, uid, pl, data.get('product', False) or product_id,
                                qty or 1.0, account.partner_id.id, line.time_slot, context=ctx)
                        if not price:
                            price = pro_price_obj.price_get(cr,uid,[pl], data.get('product', False) or product_id, qty or 1.0, account.partner_id.id, context=ctx)[pl]
                    else:
                        price = 0.0

                    taxes = product.taxes_id
                    tax = fiscal_pos_obj.map_tax(cr, uid, account.partner_id.property_account_position, taxes)
                    account_id = product.product_tmpl_id.property_account_income.id or product.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_("Configuration Error"), _("No income account defined for product '%s'") % product.name)
                    curr_line = {
                        'price_unit': price,
                        'quantity': qty,
                        'discount':factor.factor,
                        'invoice_line_tax_id': [(6,0,tax )],
                        'invoice_id': invoice.id,
                        'name': factor_name,
                        'product_id': data.get('product',product_id),
                        'uos_id': uom,
                        'account_id': account_id,
                        'account_analytic_id': account.id,
                    }
                else:
                    curr_line = {
                        'price_unit': abs(line.amount),
                        'quantity': qty,
                        'discount':factor.factor,
                        #'invoice_line_tax_id': [(6,0,tax )],
                        'invoice_id': invoice.id,
                        'name': factor_name,
                        'account_id': line.general_account_id and line.general_account_id.id,
                        'account_analytic_id': account.id,
                    }
                

                invoice_line_obj.create(cr, uid, curr_line, context=context)
                cr.execute("update account_analytic_line set invoice_id=%s WHERE account_id = %s and id = %s", (invoice.id, account.id, line.id))

            invoice_obj.button_reset_taxes(cr, uid, [invoice.id], context)
        return invoices

account_analytic_line()