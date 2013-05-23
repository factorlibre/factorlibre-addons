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
{
    "name": "FL Additional discount",
    "version": "1.0",
    "depends": ["base","sale","purchase","account"],
    "author": "E-nova tecnologies Pvt. Ltd. / Factor Libre",
    "category": "Sales",
    "description": """
    This module provide : additional discount at total sales order, purchase order and invoices instead of per order line,
    but there is no changes in existing discount on per order lines.
    Additional discount is fully integrated between sales, purchase and invoices.
    """,
    "init_xml": [],
    'update_xml': ['additional_discount_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
