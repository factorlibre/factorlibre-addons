# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
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

class efficiency_report_wizard(osv.osv_memory):
    _name = 'efficiency.report.wizard'

    _columns = {
        'date_from': fields.date('From Date', required=True),
        'date_to': fields.date('To Date', required=True),
        'category_id': fields.many2one('product.category', 'Season'),
        'seller_id': fields.many2one('res.partner', 'Seller')
    }


    def calculate_efficiency(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        report_line_pool = self.pool.get('efficiency.report.line')
        report_line_ids = report_line_pool.search(cr, uid, [])
        report_line_pool.unlink(cr, uid, report_line_ids)

        product_pool = self.pool.get('product.product')
        warehouse_pool = self.pool.get('stock.warehouse')
        location_pool = self.pool.get('stock.location')

        
        warehouses = warehouse_pool.browse(cr, uid, warehouse_pool.search(cr, uid, []))

        customer_location_id = False
        customer_location_ids = location_pool.search(cr, uid, [('usage','=','customer')])
        if customer_location_ids:
            customer_location_id = customer_location_ids[0]

        supplier_location_id = False
        supplier_location_ids = location_pool.search(cr, uid, [('usage','=','supplier')])
        if supplier_location_ids:
            supplier_location_id = supplier_location_ids[0]

        line_ids = []
        for obj in self.browse(cr, uid, ids, context=context):
            product_domain = []
            if obj.category_id:
                product_domain.append(('categ_ids','in',[obj.category_id.id]))
            if obj.seller_id:
                product_domain.append(('seller_id','=',obj.seller_id.id))

            product_ids = product_pool.search(cr, uid, product_domain)
            for product_id in product_ids:
                buy_total_qty = {}
                product_lines = []
                for warehouse in warehouses:
                    query = """
                    select coalesce(sum(product_qty), 0.0) from stock_move 
                        where date >= '%s' 
                          and date <= '%s'
                          and location_id = %d
                          and location_dest_id = %d
                          and product_id = %d
                          and state='done';
                        """ % (obj.date_from, obj.date_to, 
                              supplier_location_id, warehouse.lot_stock_id.id, product_id)
                    cr.execute(query)
                    buy_qty = cr.fetchone()[0]

                    query = """
                    select coalesce(sum(product_qty), 0.0) from stock_move 
                        where location_id = %d
                          and location_dest_id = %d
                          and product_id = %d
                          and state='done';
                        """ % (supplier_location_id, warehouse.lot_stock_id.id, product_id)
                    cr.execute(query)
                    if warehouse.company_id.id in buy_total_qty.keys():
                        buy_total_qty[warehouse.company_id.id] += buy_qty
                    else:
                        buy_total_qty[warehouse.company_id.id] = buy_qty

                    query = """
                    select coalesce(sum(product_qty), 0.0) from stock_move 
                        where date >= '%s' 
                          and date <= '%s'
                          and location_id not in (%d)
                          and location_dest_id = %d
                          and product_id = %d
                          and state='done';
                        """ % (obj.date_from, obj.date_to, warehouse.lot_stock_id.id, warehouse.lot_stock_id.id, product_id)
                    cr.execute(query)
                    move_in_qty = cr.fetchone()[0]

                    query = """
                    select coalesce(sum(product_qty), 0.0) from stock_move 
                        where date >= '%s' 
                          and date <= '%s'
                          and location_id = %d
                          and location_dest_id in (%d,%d)
                          and product_id = %d
                          and state='done';
                        """ % (obj.date_from, obj.date_to, warehouse.lot_stock_id.id, 
                               customer_location_id, warehouse.lot_output_id.id, product_id)
                    cr.execute(query)
                    sell_qty = cr.fetchone()[0]

                    query = """
                    select coalesce(sum(product_qty), 0.0) from stock_move 
                        where date >= '%s' 
                          and date <= '%s'
                          and location_id = %d
                          and location_dest_id not in (%d)
                          and product_id = %d
                          and state='done';
                        """ % (obj.date_from, obj.date_to, warehouse.lot_stock_id.id, warehouse.lot_stock_id.id, product_id)
                    cr.execute(query)
                    move_out_qty = cr.fetchone()[0]

                    move_efficiency = 0.0
                    if move_in_qty > 0:
                        move_efficiency =  move_out_qty * 100 / move_in_qty

                    # if not sell_qty and not buy_qty:
                    #    continue

                    ctx = context.copy()
            
                    ctx['warehouse'] = warehouse.id
                    ctx['location'] = warehouse.lot_stock_id.id

                    product = product_pool.browse(cr, uid, product_id, context=ctx)

                    template_id = product.product_tmpl_id and product.product_tmpl_id.id

                    
                    query = """select coalesce(value_float, 0.0) from ir_property where name='list_price' 
                    and res_id='product.template,%d' and company_id=%d""" % (template_id, warehouse.company_id and warehouse.company_id.id)
                    cr.execute(query)
                    res = cr.fetchone()
                    list_price = res and (res[0] + product.price_extra) or 0.0

                    query = """select coalesce(value_float, 0.0) from ir_property where name='standard_price' 
                    and res_id='product.template,%d' and company_id=%d""" % (template_id, warehouse.company_id and warehouse.company_id.id)
                    cr.execute(query)
                    res = cr.fetchone()
                    standard_price = res and (res[0] + product.cost_price_extra) or 0.0

                    line_values = {
                        'product_template_id': template_id,
                        'product_id': product_id,
                        'warehouse_id': warehouse.id,
                        'buy_qty': buy_qty,
                        'sell_qty': sell_qty,
                        'move_out_qty': move_out_qty,
                        'move_in_qty': move_in_qty,
                        'move_efficiency': move_efficiency,
                        'seller_id': product.seller_id and product.seller_id.id,
                        'purchase_amount': buy_qty * standard_price,
                        'sale_amount': sell_qty * list_price,
                        'standard_price': standard_price,
                        'list_price': list_price,
                        'stock': product.qty_available,
                    }
                    line_id = report_line_pool.create(cr, uid, line_values)
                    product_lines.append({'id': line_id, 'sell_qty': sell_qty, 'company_id': warehouse.company_id.id})
                    line_ids.append(line_id)

                for line in product_lines:
                    efficiency = 0.0
                    company_id = line['company_id']
                    if buy_total_qty.get(company_id) > 0:
                        efficiency = line['sell_qty'] * 100 / buy_total_qty.get(company_id)
                    report_line_pool.write(cr, uid, line['id'], {'buy_total_qty': buy_total_qty.get(company_id), 'efficiency': efficiency})

       
        #search_view = False

        return{
            'name': _('Efficiency Report'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'efficiency.report.line',
            'type': 'ir.actions.act_window',
            'domain': str([('id', 'in', line_ids)]),
            'res_id': line_ids
         }

efficiency_report_wizard()


class efficiency_report_line(osv.osv_memory):
    _name = 'efficiency.report.line'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'product_template_id': fields.many2one('product.template', 'Product Template'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'seller_id': fields.many2one('res.partner', 'Supplier', readonly=True),
        'buy_qty': fields.float('Buy Qty', readonly=True),
        'sell_qty': fields.float('Sell Qty', readonly=True),
        'move_out_qty': fields.float('Move out Qty', readonly=True),
        'move_in_qty': fields.float('Move In Qty', readonly=True),
        'efficiency': fields.float('Efficiency %', readonly=True),
        'move_efficiency': fields.float('Move Efficiency %', readonly= True, group_operator='avg'),
        'standard_price': fields.float('Standard Price', readonly=True),
        'list_price': fields.float('List Price', readonly=True),
        'purchase_amount': fields.float('Purchase Amount', readonly=True),
        'sale_amount': fields.float('Sale Amount', readonly=True),
        'stock': fields.float('Stock', readonly=True),
        'buy_total_qty': fields.float('Total Purchased', readonly=True, group_operator='avg'),
    }
efficiency_report_line()