# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    #    Copyright (C) 2012 Factor Libre.
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

class wholesaler_pricelist_config(osv.osv):
    _name = 'wholesaler.pricelist.config'

    _columns = {
        'sequence': fields.integer('Sequence'),
        'pricelist_id': fields.many2one('product.pricelist', 'Wholesaler Pricelist'),
    }

    _defaults = {
        'sequence': 1
    }

    _order = 'sequence'

wholesaler_pricelist_config()