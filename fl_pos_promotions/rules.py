#########################################################################
#                                                                       #
# Copyright (C) 2010 Open Labs Business Solutions                       #
# Copyright (C) 2011 Zikzakmedia                                        #
# Copyright (C) 2012 Factor Libre                                       #
# Special Credit: Yannick Buron for design evaluation                   #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

try:
    #Backward compatible
    from sets import Set as set
except:
    pass

from osv import osv, fields
from tools.misc import ustr
import netsvc
from tools.translate import _

LOGGER = netsvc.Logger()
DEBUG = True
PRODUCT_UOM_ID = 1

class PromotionRules(osv.osv):
    _inherit = 'promos.rules'

    def count_coupon_use(self, cursor, user, ids, 
                          name, arg, context=None):
        '''
        This function count the number of sale orders(not in cancelled state)
        that are linked to a particular coupon.
        @param cursor: Database Cursor
        @param user: ID of User
        @param ids: ID of Current record.
        @param name: Name of the field which calls this function.
        @param arg: Any argument(here None).
        @param context: Context(no direct use).
        @return: No. of of pos orders(not in cancelled state)
                that are linked to a particular coupon
        '''
        pos_obj = self.pool.get('pos.order')
        pos_promo_line_obj = self.pool.get('pos.order.promotion.line')
        sale_obj = self.pool.get('sale.order')
        res = {}
        for promotion_rule in self.browse(cursor, user, ids, context):
            if promotion_rule.coupon_code:
                #If there is uses per coupon defined check if its overused
                if promotion_rule.uses_per_coupon > -1:
                    promo_line_ids = pos_promo_line_obj.search(cursor, user, [
                            ('coupon_code','=',promotion_rule.coupon_code),
                        ])
                    matching_ids_pos = pos_obj.search(cursor, user,
                            [
                            ('promotion_line_ids', 'in', promo_line_ids),
                            ('state', '<>', 'cancel')
                            ], context=context)
                    matching_ids = sale_obj.search(cursor, user,
                            [
                            ('coupon_code', '=', promotion_rule.coupon_code),
                            ('state', '<>', 'cancel')
                            ], context=context)
                res[promotion_rule.id] = len(matching_ids) + len(matching_ids_pos)
        return res

    _columns = {
        'coupon_used': fields.function(
                    count_coupon_use, 
                    method=True, 
                    type='integer',
                    string='Number of Coupon Uses',
                    help='The number of times this coupon has been used.'),
    }

    def clear_used_rules(self, cursor, user):
        """Planned action to mark used coupons as inactive"""
        
        active_rules = self.search(cursor, user, [('active','=',True)])
        for obj in self.browse(cursor, user, active_rules):
            if obj.coupon_used >= obj.uses_per_coupon:
                self.write(cursor, user, [obj.id], {'active': False})
        return True

    def check_primary_conditions_pos(self, cursor, user,
                                  promotion_rule, order, context):
        """
        Checks the conditions for 
            Coupon Code
            Validity Date
        @param cursor: Database Cursor
        @param user: ID of User
        @param promotion_rule: Browse record sent by calling func. 
        @param order: Browse record sent by calling func.
        @param context: Context(no direct use).
        """
        sales_obj = self.pool.get('pos.order')
        #Check if the customer is in the specified partner cats
        if promotion_rule.partner_categories:
            applicable_ids = [
                        category.id \
                          for category in promotion_rule.partner_categories
                            ]
            partner_categories = [
                        category.id \
                            for category in order.partner_id.category_id
                                ]
            if not set(applicable_ids).intersection(partner_categories):
                raise Exception("Not applicable to Partner Category")
        if promotion_rule.coupon_code:
            #If the codes don't match then this is not the promo
            apply_promo = False
            for promo_line in order.promotion_line_ids: 
                if promo_line.coupon_code == promotion_rule.coupon_code:
                    apply_promo = True
                    break
            
            if not apply_promo:
                raise Exception("Coupon codes do not match")
            # Calling count_coupon_use to check whether no. of 
            # uses is greater than allowed uses.
            count = self.count_coupon_use(cursor, user, [promotion_rule.id], 
                                           True, None, context).values()[0]
            if count > promotion_rule.uses_per_coupon:
                raise Exception("Coupon is overused")
            #If a limitation exists on the usage per partner
            if promotion_rule.uses_per_partner > -1 and order.partner_id:
                promo_line_ids = self.pool.get('pos.order.promotion.line').search(cursor,
                    user, [('coupon_code','=',promo_line.coupon_code)])
                matching_ids = sales_obj.search(cursor, user,
                         [
                          ('partner_id', '=', order.partner_id.id),
                          ('state', '<>', 'cancel'),
                          ('promotion_line_ids','in',promo_line_ids)
                          ], context=context)
                if len(matching_ids) > promotion_rule.uses_per_partner:
                    raise Exception("Customer already used coupon")
        #if a start date has been specified
        if promotion_rule.from_date and \
            not (self.promotion_date(
                order.date_order) >= self.promotion_date(promotion_rule.from_date)):
            raise Exception("Order before start of promotion")
        #If an end date has been specified
        if promotion_rule.to_date and \
            not (self.promotion_date(
                order.date_order) <= self.promotion_date(promotion_rule.to_date)):
            raise Exception("Order after end of promotion")
        #All tests have succeeded
        return True

    def evaluate_pos(self, cursor, user, promotion_rule, order, context=None):
        """
        Evaluates if a promotion is valid
        @param cursor: Database Cursor
        @param user: ID of User
        @param promotion_rule: Browse Record
        @param order: Browse Record
        @param context: Context(no direct use).
        """
        if not context:
            context = {}
        expression_obj = self.pool.get('promos.rules.conditions.exps')
        try:
            self.check_primary_conditions_pos(
                                           cursor, user,
                                           promotion_rule, order,
                                           context)
        except Exception, e:
            if DEBUG:
                LOGGER.notifyChannel("Promotions",
                                     netsvc.LOG_INFO,
                                     ustr(e))
            return False
        #Now to the rules checking
        expected_result = eval(promotion_rule.expected_logic_result)
        logic = promotion_rule.logic
        #Evaluate each expression
        for expression in promotion_rule.expressions:
            result = 'Execution Failed'
            try:
                result = expression_obj.evaluate_pos(cursor, user,
                                             expression, order, context)
                #For and logic, any False is completely false
                if (not (result == expected_result)) and (logic == 'and'):
                    return False
                #For OR logic any True is completely True
                if (result == expected_result) and (logic == 'or'):
                    return True
                #If stop_further is given, then execution stops  if the
                #condition was satisfied
                if (result == expected_result) and expression.stop_further:
                    return True
            except Exception, e:
                raise osv.except_osv("Expression Error", e)
            finally:
                if DEBUG:
                    LOGGER.notifyChannel(
                        "Promotions",
                        netsvc.LOG_INFO,
                        "%s evaluated to %s" % (
                                               expression.serialised_expr,
                                               result
                                               )
                        )
        if logic == 'and':
            #If control comes here for and logic, then all conditions were 
            #satisfied
            return True
        else:
            #if control comes here for OR logic, none were satisfied
            return False

    def apply_promotions_pos(self, cursor, user, order_id, context=None):
        """
        Applies promotions
        @param cursor: Database Cursor
        @param user: ID of User
        @param order_id: ID of sale order
        @param context: Context(no direct use).
        """
        order = self.pool.get('pos.order').browse(cursor, user,
                                                   order_id, context=context)
        active_promos = self.search(cursor, user,
                                    [('active', '=', True)],
                                    context=context)
        for promotion_rule in self.browse(cursor, user,
                                          active_promos, context):
            result = self.evaluate_pos(cursor, user,
                                   promotion_rule, order,
                                   context)
            #If evaluates to true
            if result:
                try:
                    self.execute_actions_pos(cursor, user,
                                     promotion_rule, order_id,
                                     context)
                except Exception, e:
                    raise osv.except_osv(
                                         "Promotions",
                                         ustr(e)
                                         )
                #If stop further is true
                if promotion_rule.stop_further:
                    return True
        return True

    def execute_actions_pos(self, cursor, user, promotion_rule,
                            order_id, context):
        """
        Executes the actions associated with this rule
        @param cursor: Database Cursor
        @param user: ID of User
        @param promotion_rule: Browse Record
        @param order_id: ID of sale order
        @param context: Context(no direct use).
        """
        action_obj = self.pool.get('promos.rules.actions')
        if DEBUG:
            LOGGER.notifyChannel(
                        "Promotions", netsvc.LOG_INFO,
                        "Applying promo %s to %s" % (
                                               promotion_rule.id,
                                               order_id
                                               ))
        order = self.pool.get('pos.order').browse(cursor, user,
                                                   order_id, context)
        for action in promotion_rule.actions:
            try:
                action_obj.execute_pos(cursor, user, action.id,
                                   order, context=None)
            except Exception, error:
                raise error
        return True

PromotionRules()

class PromotionsRulesConditionsExprs(osv.osv):
    "Expressions for conditions"
    _inherit = 'promos.rules.conditions.exps'

    def evaluate_pos(self, cursor, user,
                 expression, order, context=None):
        """
        Evaluates the expression in given environment
        @param cursor: Database Cursor
        @param user: ID of User
        @param expression: Browse record of expression
        @param order: Browse Record of sale order
        @param context: Context(no direct use).
        @return: True if evaluation succeeded
        """
        products = []   # List of product Codes
        prod_qty = {}   # Dict of product_code:quantity
        prod_unit_price = {}
        prod_sub_total = {}
        prod_discount = {}
        prod_weight = {}
        prod_net_price = {}
        prod_lines = {}
        for line in order.lines:
            if line.product_id:
                product_code = line.product_id.code
                products.append(product_code)
                prod_lines[product_code] = line.product_id
                prod_qty[product_code] = prod_qty.get(
                                            product_code, 0.00
                                                    ) + line.qty
#                prod_net_price[product_code] = prod_net_price.get(
#                                                    product_code, 0.00
#                                                    ) + line.price_net
                prod_unit_price[product_code] = prod_unit_price.get(
                                                    product_code, 0.00
                                                    ) + line.price_unit
                prod_sub_total[product_code] = prod_sub_total.get(
                                                    product_code, 0.00
                                                    ) + line.price_subtotal
                prod_discount[product_code] = prod_discount.get(
                                                    product_code, 0.00
                                                    ) + line.discount
                #Total Weight Not exists on PoS
                #prod_weight[product_code] = prod_weight.get(
                #                                    product_code, 0.00
                #                                    ) + line.th_weight 
        return eval(expression.serialised_expr)

PromotionsRulesConditionsExprs()

class PromotionsRulesActions(osv.osv):
    "Promotions actions"
    _inherit = 'promos.rules.actions'

    def clear_existing_promotion_lines_pos(self, cursor, user,
                                        order, context=None):
        """
        Deletes existing promotion lines before applying
        @param cursor: Database Cursor
        @param user: ID of User
        @param order: Sale order
        @param context: Context(no direct use).
        """
        order_line_obj = self.pool.get('pos.order.line')
        #Delete all promotion lines
        order_line_ids = order_line_obj.search(cursor, user,
                                            [
                                             ('order_id', '=', order.id),
                                             ('promotion_line', '=', True),
                                            ], context=context
                                            )
        if order_line_ids:
            order_line_obj.unlink(cursor, user, order_line_ids, context)
        #Clear discount column
        order_line_ids = order_line_obj.search(cursor, user,
                                            [
                                             ('order_id', '=', order.id),
                                            ], context=context
                                            )
        if order_line_ids:
            order_line_obj.write(cursor, user,
                                 order_line_ids,
                                 {'discount':0.00},
                                 context=context)
        return True

    def execute_pos(self, cursor, user, action_id,
                                   order, context=None):
        """
        Executes the action into the order
        @param cursor: Database Cursor
        @param user: ID of User
        @param action_id: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        #self.clear_existing_promotion_lines_pos(cursor, user, order, context)
        action = self.browse(cursor, user, action_id, context)
        method_name = 'pos_action_' + action.action_type
        return getattr(self, method_name).__call__(cursor, user, action,
                                                   order, context)

    def pos_action_prod_disc_perc(self, cursor, user,
                               action, order, context=None):
        """
        Action for 'Discount % on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        order_line_obj = self.pool.get('pos.order.line')
        for order_line in order.order_line:
            if order_line.product_id.code == eval(action.product_code):
                return order_line_obj.write(cursor,
                                     user,
                                     order_line.id,
                                     {
                                      'discount':eval(action.arguments),
                                      },
                                     context
                                     )
    
    def pos_action_prod_disc_fix(self, cursor, user,
                              action, order, context=None):
        """
        Action for 'Fixed amount on Product'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        order_line_obj = self.pool.get('pos.order.line')
        product_obj = self.pool.get('product.product')
        line_name = '%s on %s' % (action.promotion.name,
                                     eval(action.product_code))
        product_id = product_obj.search(cursor, user,
                       [('default_code', '=', eval(action.product_code))],
                       context=context)

        promo_product = product_obj.search(cursor, user, [('default_code','=','POSPROMO')])

        if not product_id:
            raise Exception("No product with the product code")
        if len(product_id) > 1:
            raise Exception("Many products with same code")
        product = product_obj.browse(cursor, user, product_id[0], context)
        return order_line_obj.create(cursor,
                              user,
                              {
                              'order_id':order.id,
                              'name':line_name,
                              'promotion_line':True,
                              'product_id': promo_product[0],
                              'price_unit':-eval(action.arguments),
                              'qty':1,
                              },
                              context
                              )
    
    def pos_action_cart_disc_perc(self, cursor, user,
                               action, order, context=None):
        """
        'Discount % on Sub Total'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        product_obj = self.pool.get('product.product')
        order_line_obj = self.pool.get('pos.order.line')
        promo_product = product_obj.search(cursor, user, [('default_code','=','POSPROMO')])
        return order_line_obj.create(cursor,
                                  user,
                                  {
                      'order_id':order.id,
                      'name':action.promotion.name,
                      'price_unit':-((order.amount_total - order.amount_tax) \
                                    * eval(action.arguments) / 100),
                      'product_id': promo_product[0],
                      'qty':1,
                      'promotion_line':True
                                  },
                                  context
                                  )
        
    def pos_action_cart_disc_fix(self, cursor, user,
                              action, order, context=None):
        """
        'Fixed amount on Sub Total'
        @param cursor: Database Cursor
        @param user: ID of User
        @param action: Action to be taken on sale order
        @param order: sale order
        @param context: Context(no direct use).
        """
        product_obj = self.pool.get('product.product')
        order_line_obj = self.pool.get('pos.order.line')
        promo_product = product_obj.search(cursor, user, [('default_code','=','POSPROMO')])
        if action.action_type == 'cart_disc_fix':
            refund_amount = 0.0
            discount = abs(eval(action.arguments))
            if discount > order.amount_total:
                discount = order.amount_total
                refund_amount = abs(eval(action.arguments)) - order.amount_total

            #Change with many discount refunds
            self.pool.get('pos.order').write(cursor, user, [order.id], {'refund_amount': refund_amount})
            
            return order_line_obj.create(cursor,
                                  user,
                                  {
                      'order_id':order.id,
                      'name':action.promotion.name,
                      'product_id': promo_product[0],
                      'price_unit':-(discount),
                      'qty':1,
                      'promotion_line':True,
                                  },
                                  context
                                  )
PromotionsRulesActions()