# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    #    Copyright (C) 2013 Factor Libre.
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

class purchase_advance_payment_inv(osv.osv_memory):
    _name = 'purchase.advance.payment.inv'
    _columns = {
        'product_id': fields.many2one('product.product', 'Advance Product', required=True,
            help="Select a product of type service which is called 'Advance Product'. You may have to create it and set it as a default value on this field."),
        'amount': fields.float('Advance Amount', digits=(16, 2), required=True, help="The amount to be invoiced in advance."),
        'qtty': fields.float('Quantity', digits=(16, 2), required=True),
    }
    _defaults = {
        'qtty': 1.0
    }

    def create_invoices(self, cr, uid, ids, context=None):
        """
             To create invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs if we want more than one
             @param context: A standard dictionary

             @return:

        """
        list_inv = []
        obj_purchase = self.pool.get('purchase.order')
        obj_lines = self.pool.get('account.invoice.line')
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')

        if context is None:
            context = {}

        for purchase_adv_obj in self.browse(cr, uid, ids, context=context):
            for purchase in obj_purchase.browse(cr, uid, context.get('active_ids', []), context=context):
                journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', purchase.company_id.id)], limit=1)
                create_ids = []
                ids_inv = []
                val = obj_lines.product_id_change(cr, uid, [], purchase_adv_obj.product_id.id,
                        uom = False, partner_id = purchase.partner_id.id, fposition_id = purchase.fiscal_position.id)
                res = val['value']
                if not res.get('account_id'):
                    raise osv.except_osv(_('Configuration Error !'),
                                _('There is no income account defined ' \
                                        'for this product: "%s" (id:%d)') % \
                                        (purchase_adv_obj.product_id.name, purchase_adv_obj.product_id.id,))
                
                line_id = obj_lines.create(cr, uid, {
                    'name': res.get('name'),
                    'account_id': res['account_id'],
                    'price_unit': purchase_adv_obj.amount,
                    'quantity': purchase_adv_obj.qtty,
                    'discount': False,
                    'uos_id': res.get('uos_id'),
                    'product_id': purchase_adv_obj.product_id.id,
                    'invoice_line_tax_id': [(6, 0, res.get('invoice_line_tax_id'))],
                    #'account_analytic_id': purchase_adv_obj.product_id.account_analytic_id.id or False,
                    #'note':'',
                })
                create_ids.append(line_id)
                inv = {
                    'name': purchase.partner_ref or purchase.name,
                    'reference': purchase.partner_ref or purchase.name,
                    'account_id': purchase.partner_id.property_account_payable.id,
                    'type': 'in_invoice',
                    'partner_id': purchase.partner_id.id,
                    'currency_id': purchase.pricelist_id.currency_id.id,
                    'address_invoice_id': purchase.partner_address_id.id,
                    'address_contact_id': purchase.partner_address_id.id,
                    'journal_id': len(journal_ids) and journal_ids[0] or False,
                    'invoice_line': [(6, 0, create_ids)], 
                    'origin': purchase.name,
                    'fiscal_position': purchase.fiscal_position.id or purchase.partner_id.property_account_position.id,
                    'payment_term': purchase.partner_id.property_payment_term and purchase.partner_id.property_payment_term.id or False,
                    'company_id': purchase.company_id.id,
                }

                inv_id = inv_obj.create(cr, uid, inv)
                inv_obj.button_reset_taxes(cr, uid, [inv_id], context=context)

                for inv in purchase.invoice_ids:
                    ids_inv.append(inv.id)
                ids_inv.append(inv_id)
                obj_purchase.write(cr, uid, purchase.id, {'initial_payment': True, 'invoice_ids': [(6, 0, ids_inv)]})
                list_inv.append(inv_id)

        context.update({'invoice_id':list_inv})

        return {
            'name': 'Open Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.open.invoice',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

purchase_advance_payment_inv()

class purchase_open_invoice(osv.osv_memory):
    _name = "purchase.open.invoice"
    _description = "Purchase Open Invoice"

    def open_invoice(self, cr, uid, ids, context=None):

        """
             To open invoice.
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs if we want more than one
             @param context: A standard dictionary
             @return:

        """
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        for advance_pay in self.browse(cr, uid, ids, context=context):
            form_res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
            form_id = form_res and form_res[1] or False
            tree_res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_tree')
            tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Advance Invoice'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': int(context['invoice_id'][0]),
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': "{'type': 'in_invoice'}",
            'type': 'ir.actions.act_window',
         }

purchase_open_invoice()
