"""
Quotation Comparison and Analysis Utilities
"""

from django.db.models import Min, Max, Avg, Q
from decimal import Decimal
from .models import SupplierQuotation, SupplierQuotationItem, RFQItem
from products.models import Product

class QuotationComparison:
    """Utility class for comparing supplier quotations"""
    
    def __init__(self, rfq):
        self.rfq = rfq
        self.quotations = SupplierQuotation.objects.filter(rfq=rfq, status='submitted')
    
    def get_comparison_matrix(self):
        """Generate a comparison matrix for all quotations"""
        comparison_data = []
        
        for rfq_item in self.rfq.items.all():
            product_comparison = {
                'product': rfq_item.product,
                'required_qty': rfq_item.quantity,
                'required_uom': rfq_item.required_uom,
                'target_price': rfq_item.target_unit_price,
                'quotations': []
            }
            
            # Get quotations for this product
            quotation_items = SupplierQuotationItem.objects.filter(
                quotation__in=self.quotations,
                product=rfq_item.product
            ).select_related('quotation__supplier')
            
            for quote_item in quotation_items:
                quote_data = {
                    'supplier': quote_item.quotation.supplier,
                    'quotation': quote_item.quotation,
                    'quoted_qty': quote_item.quantity,
                    'quoted_uom': quote_item.quoted_uom,
                    'unit_price': quote_item.unit_price,
                    'base_unit_price': quote_item.base_unit_price,
                    'package_qty': quote_item.package_qty,
                    'minimum_order_qty': quote_item.minimum_order_qty,
                    'total_amount': quote_item.total_amount,
                    'lead_time': quote_item.lead_time_days,
                    'payment_terms': quote_item.quotation.payment_terms,
                    'valid_until': quote_item.quotation.valid_until,
                    'cost_for_required_qty': self._calculate_cost_for_required_qty(
                        quote_item, rfq_item.quantity
                    )
                }
                product_comparison['quotations'].append(quote_data)
            
            # Sort by base unit price
            product_comparison['quotations'].sort(
                key=lambda x: x['base_unit_price']
            )
            
            comparison_data.append(product_comparison)
        
        return comparison_data
    
    def _calculate_cost_for_required_qty(self, quote_item, required_qty):
        """Calculate actual cost for the required quantity"""
        # Convert required quantity to supplier's UOM
        if quote_item.package_qty > 0:
            packages_needed = required_qty / quote_item.package_qty
            # Round up to minimum order quantity
            packages_needed = max(packages_needed, quote_item.minimum_order_qty)
            total_cost = packages_needed * quote_item.unit_price
            actual_qty_received = packages_needed * quote_item.package_qty
            
            return {
                'packages_needed': packages_needed,
                'total_cost': total_cost,
                'actual_qty_received': actual_qty_received,
                'unit_cost_for_required_qty': total_cost / required_qty if required_qty > 0 else 0
            }
        else:
            return {
                'packages_needed': required_qty,
                'total_cost': required_qty * quote_item.unit_price,
                'actual_qty_received': required_qty,
                'unit_cost_for_required_qty': quote_item.unit_price
            }
    
    def get_best_quotation_analysis(self):
        """Analyze and recommend best quotations"""
        comparison_matrix = self.get_comparison_matrix()
        recommendations = []
        
        for product_data in comparison_matrix:
            if not product_data['quotations']:
                continue
            
            # Find best options by different criteria
            best_price = min(product_data['quotations'], 
                           key=lambda x: x['base_unit_price'])
            best_lead_time = min(product_data['quotations'], 
                               key=lambda x: x['lead_time'])
            best_total_cost = min(product_data['quotations'], 
                                key=lambda x: x['cost_for_required_qty']['total_cost'])
            
            # Calculate savings
            worst_price = max(product_data['quotations'], 
                            key=lambda x: x['base_unit_price'])
            potential_savings = (worst_price['base_unit_price'] - 
                               best_price['base_unit_price']) * product_data['required_qty']
            
            recommendation = {
                'product': product_data['product'],
                'best_price_supplier': best_price['supplier'],
                'best_price_per_unit': best_price['base_unit_price'],
                'best_lead_time_supplier': best_lead_time['supplier'],
                'best_lead_time': best_lead_time['lead_time'],
                'best_total_cost_supplier': best_total_cost['supplier'],
                'best_total_cost': best_total_cost['cost_for_required_qty']['total_cost'],
                'potential_savings': potential_savings,
                'recommendation': self._generate_recommendation(
                    best_price, best_lead_time, best_total_cost, product_data
                )
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_recommendation(self, best_price, best_lead_time, best_total_cost, product_data):
        """Generate recommendation based on analysis"""
        # Simple scoring algorithm
        scores = {}
        
        for quote in product_data['quotations']:
            supplier = quote['supplier']
            score = 0
            
            # Price score (40% weight)
            if quote == best_price:
                score += 40
            else:
                price_ratio = best_price['base_unit_price'] / quote['base_unit_price']
                score += 40 * price_ratio
            
            # Lead time score (30% weight)
            if quote == best_lead_time:
                score += 30
            elif quote['lead_time'] > 0:
                time_ratio = best_lead_time['lead_time'] / quote['lead_time']
                score += 30 * time_ratio
            
            # Total cost score (30% weight)
            if quote == best_total_cost:
                score += 30
            else:
                cost_ratio = (best_total_cost['cost_for_required_qty']['total_cost'] / 
                            quote['cost_for_required_qty']['total_cost'])
                score += 30 * cost_ratio
            
            scores[supplier] = {
                'score': score,
                'quotation': quote
            }
        
        # Get highest scoring supplier
        recommended = max(scores.items(), key=lambda x: x[1]['score'])
        
        return {
            'supplier': recommended[0],
            'score': recommended[1]['score'],
            'reasons': self._get_recommendation_reasons(
                recommended[1]['quotation'], best_price, best_lead_time, best_total_cost
            )
        }
    
    def _get_recommendation_reasons(self, quote, best_price, best_lead_time, best_total_cost):
        """Generate reasons for recommendation"""
        reasons = []
        
        if quote == best_price:
            reasons.append("Best unit price")
        if quote == best_lead_time:
            reasons.append("Fastest delivery")
        if quote == best_total_cost:
            reasons.append("Best total cost for required quantity")
        
        # Add quality indicators
        supplier = quote['supplier']
        if hasattr(supplier, 'quality_rating') and supplier.quality_rating >= 8:
            reasons.append("High quality rating")
        if hasattr(supplier, 'delivery_rating') and supplier.delivery_rating >= 8:
            reasons.append("Reliable delivery record")
        
        return reasons

class UOMConverter:
    """Utility for UOM conversions in purchase context"""
    
    @staticmethod
    def convert_quotation_to_base_units(quotation_item):
        """Convert quotation item to base units for comparison"""
        base_units = quotation_item.quantity * quotation_item.package_qty
        base_unit_price = quotation_item.unit_price / quotation_item.package_qty if quotation_item.package_qty > 0 else quotation_item.unit_price
        
        return {
            'total_base_units': base_units,
            'price_per_base_unit': base_unit_price,
            'original_qty': quotation_item.quantity,
            'original_uom': quotation_item.quoted_uom,
            'package_size': quotation_item.package_qty
        }
    
    @staticmethod
    def calculate_purchase_requirements(required_base_units, supplier_quote_item):
        """Calculate how many packages to order for required base units"""
        if supplier_quote_item.package_qty <= 0:
            return {
                'packages_to_order': required_base_units,
                'total_cost': required_base_units * supplier_quote_item.unit_price,
                'units_received': required_base_units,
                'excess_units': 0
            }
        
        packages_needed = required_base_units / supplier_quote_item.package_qty
        packages_to_order = max(packages_needed, supplier_quote_item.minimum_order_qty)
        
        # Round up to nearest whole package
        import math
        packages_to_order = math.ceil(packages_to_order)
        
        units_received = packages_to_order * supplier_quote_item.package_qty
        excess_units = units_received - required_base_units
        total_cost = packages_to_order * supplier_quote_item.unit_price
        
        return {
            'packages_to_order': packages_to_order,
            'total_cost': total_cost,
            'units_received': units_received,
            'excess_units': excess_units,
            'effective_unit_cost': total_cost / units_received if units_received > 0 else 0
        }

class QuotationValidator:
    """Validate quotations for business rules"""
    
    @staticmethod
    def validate_quotation(quotation):
        """Validate a supplier quotation"""
        errors = []
        warnings = []
        
        # Check if quotation is expired
        from django.utils import timezone
        if quotation.valid_until < timezone.now().date():
            errors.append("Quotation has expired")
        
        # Check if all RFQ items are quoted
        rfq_items = quotation.rfq.items.all()
        quoted_products = set(item.product_id for item in quotation.items.all())
        missing_products = []
        
        for rfq_item in rfq_items:
            if rfq_item.product_id not in quoted_products:
                missing_products.append(rfq_item.product.name)
        
        if missing_products:
            errors.append(f"Missing quotations for: {', '.join(missing_products)}")
        
        # Check minimum order quantities
        for item in quotation.items.all():
            if item.quantity < item.minimum_order_qty:
                warnings.append(
                    f"{item.product.name}: Quoted quantity ({item.quantity}) "
                    f"is below minimum order quantity ({item.minimum_order_qty})"
                )
        
        # Check pricing reasonableness (if target prices exist)
        for item in quotation.items.all():
            try:
                rfq_item = quotation.rfq.items.get(product=item.product)
                if rfq_item.target_unit_price and rfq_item.target_unit_price > 0:
                    if item.base_unit_price > rfq_item.target_unit_price * Decimal('1.2'):  # 20% over target
                        warnings.append(
                            f"{item.product.name}: Price significantly higher than target "
                            f"(${item.base_unit_price} vs ${rfq_item.target_unit_price})"
                        )
            except:
                pass
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
