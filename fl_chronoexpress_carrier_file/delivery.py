# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010   Àngel Àlvarez 
#                      NaN Projectes de programari lliure S.L.
#                      (http://www.nan-tic.com) All Rights Reserved.
# Copyright (c) 2013  FactorLibre S.L.
#                     Hugo Santos
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from osv import fields,osv
from tools.translate import _
import netsvc
import base64
import os


class carrier_file_wizard( osv.osv_memory ):
    _name ='carrier.file.wizard'

    _columns = {
        'start_date': fields.datetime( 'Start Date' ),
        'end_date': fields.datetime('End Date' ),
    }

    def action_accept( self, cr, uid, ids, context=None ):
        if context == None:
            context ={}
        
        wizard = self.pool.get('carrier.file.wizard').browse( cr, uid, ids[0], context=context )
        filter = []
        if wizard.start_date:
            filter.append( ('date_done','>=',wizard.start_date) )
        if wizard.end_date:
            filter.append( ('date_done','<=',wizard.end_date) )

        filter.append( ( 'state', '=', 'done' ) )
        filter.append( ( 'type', '=', 'out' ) )
        picking_ids =  self.pool.get('stock.picking').search(cr, uid, filter, context=context) 
        
        self.pool.get('delivery.carrier').gen_carrier_files( cr, uid, picking_ids, context )
        return  {}

carrier_file_wizard()

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
                raise osv.osv_exception(_("Error"), _("File %s does not exist" % (file_path)))

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
    

class delivery_carrier( osv.osv ):
    _inherit = 'delivery.carrier'

    _columns = {
        'format_id': fields.many2one('file.format', 'File Format' ),
        'reimbursement': fields.boolean('Reimbursement')
    }

    def gen_carrier_files( self, cr, uid, picking_ids, context=None ):
        if context == None:
            context ={}

        picking_carriers = {}
        for picking in self.pool.get('stock.picking').browse(cr, uid, picking_ids, context ):
            if picking.type != 'out':
                continue
            if not picking.carrier_id and not picking.carrier_id.format_id:
                continue
            if not picking_carriers.get( picking.carrier_id.format_id.id , False ):
                picking_carriers[ picking.carrier_id.format_id.id ] = [ picking.id ]
            else:
                picking_carriers[ picking.carrier_id.format_id.id ].append( picking.id )

        
        for carrier_format in picking_carriers:
            self.pool.get('file.format').export_file( cr, uid, carrier_format, picking_carriers[carrier_format], context )
        
        return True

delivery_carrier()


class stock_picking( osv.osv ):
    _inherit = 'stock.picking'

    def action_done( self, cr, uid, ids, context=None ):
        result = super( stock_picking,self ).action_done( cr, uid, ids, context=context )
        self.pool.get( 'delivery.carrier' ).gen_carrier_files( cr, uid, ids, context ) 
        return result

stock_picking()
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
