# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
#    Author:
#        Hugo Santos <hugo.santos@factorlibre.com>
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

from osv import osv

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        lines = []
        lines_by_account = {'credit': {}, 'debit': {}}
        for line in move_lines:
            if not line[2].get('product_id'):
                lines.append(line)
            else:
                acc_id = line[2].get('account_id')
                acc_type = line[2].get('credit') and 'credit' or 'debit'
                tax_code_id = line[2].get('tax_code_id', 'no_tax')
                if acc_id:
                    if acc_id in lines_by_account[acc_type].keys():
                        if tax_code_id in lines_by_account[acc_type][acc_id].keys():
                            lines_by_account[acc_type][acc_id][tax_code_id][acc_type] += line[2].get(acc_type)
                            lines_by_account[acc_type][acc_id][tax_code_id]['tax_amount'] += line[2].get('tax_amount')
                        else:
                            lines_by_account[acc_type][acc_id][tax_code_id] = line[2]
                            lines_by_account[acc_type][acc_id][tax_code_id]['product_id'] = False
                            lines_by_account[acc_type][acc_id][tax_code_id]['name'] = 'Lines %s' % tax_code_id
                    else:
                        lines_by_account[acc_type][acc_id] = {}
                        lines_by_account[acc_type][acc_id][tax_code_id] = line[2]
                        lines_by_account[acc_type][acc_id][tax_code_id]['product_id'] = False
                        lines_by_account[acc_type][acc_id][tax_code_id]['name'] = 'Lines %s' % tax_code_id

        for cd_key in lines_by_account.keys():
            for acc_key in lines_by_account[cd_key].keys():
                for tax_key in lines_by_account[cd_key][acc_key].keys():
                    lines.append((0, 0, lines_by_account[cd_key][acc_key][tax_key]))
        return lines

account_invoice()