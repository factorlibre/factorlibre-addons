# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Hugo Santos.
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
import base64
import os

class download_carrier_file_wizard(osv.osv_memory):
    _name = 'download.carrier.file.wizard'

    _columns = {
        'format_id': fields.many2one('file.format', 'Carrier File Format', required=True),
        'carrier_file': fields.binary('Carrier File', readonly=True),
        'carrier_file_name': fields.char('Carrier File Name', size=255),
        'state': fields.selection((('init','Init'),('download','Download')), 'State')
    }

    _defaults = {
        'state': 'init'
    }

    def download_file(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for obj in self.browse(cr, uid, ids, context=context):
            file_name = obj.format_id.file_name
            file_path = obj.format_id.path + "/" + file_name
            if not os.path.isfile(file_path):
                raise osv.except_osv(_("Error"), _("File %s does not exist" % (file_path)))

            carrier_file = open( file_path, 'rb' )
            carrier_file_b64 = base64.b64encode(carrier_file.read())
            carrier_file.close()

            carrier_file = open(file_path, 'w')
            carrier_file.write('')
            carrier_file.close()

        return self.write(cr, uid, ids, {
            'carrier_file': carrier_file_b64, 
            'state': 'download',
            'carrier_file_name': file_name})


download_carrier_file_wizard()