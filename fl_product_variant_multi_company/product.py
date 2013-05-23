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
import decimal_precision as dp

class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        'company_price_ids': fields.one2many('product.template.company.price', 'tmpl_id', 'Company Prices')
    }

    def update_multi_company_prices(self, cr, uid, ids, context=None):
        property_obj = self.pool.get('ir.property')
        field_obj = self.pool.get('ir.model.fields')
        std_price_field_id = field_obj.search(cr, uid, 
            [('model','=','product.template'),('name','=','standard_price')])[0]
        lst_price_field_id = field_obj.search(cr, uid,
            [('model','=','product.template'),('name','=','list_price')])[0]

        for tmpl in self.browse(cr, uid, ids, context=context):
            for price in tmpl.company_price_ids:
                company_id = price.company_id and price.company_id.id
                reference = "product.template,%s" % (tmpl.id)
                
                values = {
                    'res_id': reference,
                    'company_id': company_id,
                    'type': 'float'
                }

                lst_values = values.copy()
                lst_values['name'] = 'list_price'
                lst_values['fields_id'] = lst_price_field_id,
                lst_values['value_float'] = price.list_price

                std_values = values.copy()
                std_values['name'] = 'standard_price'
                std_values['fields_id'] = std_price_field_id
                std_values['value_float'] = price.standard_price

                lst_price_property_ids = property_obj.search(cr, uid, [
                    ('company_id', '=', company_id),
                    ('fields_id', '=', lst_price_field_id),
                    ('res_id','=',reference)
                    ])

                std_price_property_ids = property_obj.search(cr, uid, [
                    ('company_id', '=', company_id),
                    ('fields_id', '=', std_price_field_id),
                    ('res_id','=',reference)
                    ])

                if lst_price_property_ids:
                    property_obj.write(cr, uid, lst_price_property_ids, lst_values)
                else:
                    property_obj.create(cr, uid, lst_values)

                if std_price_property_ids:
                    property_obj.write(cr, uid, std_price_property_ids, std_values)
                else:
                    property_obj.create(cr, uid, std_values)

                
        return True

product_template()

class product_template_company_price(osv.osv):
    _name = 'product.template.company.price'

    _columns = {
        'tmpl_id': fields.many2one('product.template', 'Template'),
        'list_price': fields.float('Sale Price', digits_compute=dp.get_precision('Sale Price'), help="Base price for computing the customer price. Sometimes called the catalog price."),
        'standard_price': fields.float('Cost Price', required=True, digits_compute=dp.get_precision('Purchase Price'), help="Product's cost for accounting stock valuation. It is the base price for the supplier price."),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'list_price': 1.0,
        'standard_price': 1.0
    }

product_template_company_price()