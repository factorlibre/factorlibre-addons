# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

import wizard
import pooler
import time
import report
from osv import osv, fields
from tools.translate import _


class fl_account_balance_reporting(osv.osv):

    _name = "account.balance.reporting"
    _inherit = "account.balance.reporting"
    
    def wiz_account_balance_reporting_calculate(self, cr, uid, ids, context=None):
        """
        Called when the user presses the Calculate button.
        It will use the report template to generate lines of detail for the
        report with calculated values.
        """
        report_line_facade = self.pool.get('account.balance.reporting.line')

        # Set the state to 'calculating'
        self.write(cr, uid, ids, {
                'state': 'calc',
                'calc_date': time.strftime('%Y-%m-%d %H:%M:%S')
            })

        #
        # Replace the lines of detail of the report with new lines from its template
        #

        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            # Clear the report data (unlink the lines of detail)
            report_line_facade.unlink(cr, uid, [line.id for line in report.line_ids])

            #
            # Fill the report with a 'copy' of the lines of its template (if it has one)
            #
            if report.template_id:
                for template_line in report.template_id.line_ids:
                    report_line_facade.create(cr, uid, {
                            'code': template_line.code,
                            'name': template_line.name,
                            'report_id': report.id,
                            'template_line_id': template_line.id,
                            'parent_id': None,
                            'current_value': None,
                            'previous_value': None,
                            'sequence': template_line.sequence,
                            'css_class': template_line.css_class,
                        }, context)

        #
        # Set the parents of the lines in the report
        # Note: We reload the reports objects to refresh the lines of detail.
        #
        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            if report.template_id:
                #
                # Establecemos los padres de las líneas (ahora que ya están creados)
                #
                for line in report.line_ids:
                    if line.template_line_id and line.template_line_id.parent_id:
                        parent_line_id = report_line_facade.search(cr, uid, [('report_id', '=', report.id), ('code', '=', line.template_line_id.parent_id.code)])
                        report_line_facade.write(cr, uid, line.id, {
                                'parent_id': len(parent_line_id) and parent_line_id[0] or None,
                            }, context)

        #
        # Calculate the values of the lines
        # Note: We reload the reports objects to refresh the lines of detail.
        #
        reports = self.browse(cr, uid, ids, context)
        for report in reports:
            if report.template_id:
                # Refresh the report's lines values
                for line in report.line_ids:
                    line.refresh_values()

                # Set the report as calculated
                self.write(cr, uid, [report.id], {
                        'state': 'calc_done'
                    })
            else:
                # Ouch! no template: Going back to draft state.
                self.write(cr, uid, [report.id], {'state': 'draft'})
        return True


fl_account_balance_reporting()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
