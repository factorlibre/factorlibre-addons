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

from osv import osv, fields

class sale_order_line(osv.osv):
	_inherit = 'sale.order.line'

	_defaults = {
		'sequence': 1,
	}

	def create(self, cr, uid, vals, context = None):
		if context is None:
			context = {}

		max_sequence = 0
		if 'order_id' in vals and vals['order_id']:
			line_ids = self.search(cr, uid, [('order_id','=',vals['order_id'])], context=context)
			for line in self.browse(cr, uid, line_ids, context=context):
				if line.sequence > max_sequence:
					max_sequence = line.sequence
			vals['sequence'] = max_sequence + 1

		return super(sale_order_line, self).create(cr, uid, vals, context=context)	

sale_order_line()