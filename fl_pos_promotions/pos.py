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

class pos_order(osv.osv):
    _inherit = 'pos.order'

    _columns = {
        'coupon_code':fields.char('Promo Coupon Code', size=20),
        'refund_amount': fields.float('Refund Amount', readonly=True),
        'promotion_line_ids': fields.one2many('pos.order.promotion.line', 'promo_id', 'Promotion Lines',
            readonly=True, states={'draft': [('readonly',False)]}),
    }

    def apply_promotions(self, cursor, user, ids, context=None):
        """
        Applies the promotions to the given records
        @param cursor: Database Cursor
        @param user: ID of User
        @param ids: ID of current record.
        @param context: Context(no direct use).
        """
        promotions_obj = self.pool.get('promos.rules')
        for order_id in ids:
            order = self.browse(cursor, user, order_id, context=context)
            self.pool.get('promos.rules.actions').clear_existing_promotion_lines_pos(cursor, user, order, context=context)
            promotions_obj.apply_promotions_pos(cursor, user, 
                                            order_id, context=None)
            
        return True

pos_order()

class pos_order_line(osv.osv):
    _inherit = "pos.order.line"
    
    _columns = {
        'promotion_line':fields.boolean(
                "Promotion Line",
                help="Indicates if the line was created by promotions"
                                        )
    }
pos_order_line()

class pos_order_promotion_line(osv.osv):
    _name = 'pos.order.promotion.line'
    _rec_name = 'coupon_code'

    _columns = {
        'promo_id': fields.many2one('pos.order', 'Order'),
        'coupon_code': fields.char('Coupon Code', size=64) 
    }
pos_order_promotion_line()