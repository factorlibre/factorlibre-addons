# -*- encoding: utf-8 -*-
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
from lxml import etree
import decimal_precision as dp

import netsvc
import pooler
from osv import fields, osv, orm
from tools.translate import _

class account_invoice(osv.osv):
    
    _name = "account.invoice"
    _inherit = "account.invoice"
    _description = 'Invoice'
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            amount_untaxed = 0.0
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'add_disc_amt': 0.0,
                'amount_net': 0.0,
            }
            for line in invoice.invoice_line:
                amount_untaxed += line.price_subtotal
            res[invoice.id]['add_disc_amt'] = amount_untaxed * invoice.add_disc/100  
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_untaxed'] = amount_untaxed - res[invoice.id]['add_disc_amt']
            res[invoice.id]['amount_net'] = res[invoice.id]['amount_untaxed']  
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res
    
    
    _columns={
              
            'add_disc':fields.float('Additional Discount(%)',digits=(4,2),readonly=True, states={'draft':[('readonly',False)]}),
            'add_disc_amt': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Additional Disc Amt',
                                            store =True,multi='sums', help="The additional discount on untaxed amount."),
            'amount_net': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Net Amount',
                                              store = True,multi='sums', help="The amount after additional discount."),   
            'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed',
                                              store=True, multi='all'),
            'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Tax',
                                          store=True,multi='all'),
            'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
                                            store=True,multi='all'),
              
              
              }
    
    _defaults={
               'add_disc': 0.0,               
               }


    

account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id


        for line in inv.invoice_line:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            tax_code_found= False

            line_price_unit = (line.price_unit * (1 - (line.discount or 0.0) / 100.0))
            line_price_unit = (line_price_unit * (1 - (inv.add_disc or 0.0) / 100.0))

            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    line_price_unit,
                    line.quantity, inv.address_invoice_id.id, line.product_id,
                    inv.partner_id, context=context)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = (line_price_unit * line.quantity) * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = (line_price_unit * line.quantity) * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        line_price_subtotal = line.price_subtotal
        if line.invoice_id and line.invoice_id.add_disc:
            line_price_subtotal = (line.price_subtotal * (1 - (line.invoice_id.add_disc or 0.0) / 100.0))

        return {
            'type':'src',
            'name': line.name[:64],
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price': line_price_subtotal,
            'account_id':line.account_id.id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
        }

account_invoice_line()

class account_invoice_tax(osv.osv):

    _inherit = 'account.invoice.tax'

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            line_price_unit = (line.price_unit * (1 - (line.discount or 0.0) / 100.0))
            line_price_unit = (line_price_unit * (1 - (inv.add_disc or 0.0) / 100.0))

            for tax in tax_obj.compute_all(
                    cr, uid, line.invoice_line_tax_id,
                    line_price_unit,
                    line.quantity, inv.address_invoice_id.id, line.product_id,
                    inv.partner_id, context=context)['taxes']:
                val={}

                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity']) 

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped

account_invoice_tax()
