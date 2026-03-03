"""
智能定价模块
基于书籍信息、市场供需和历史交易数据进行智能定价
"""
from sqlalchemy import func
from app.models.models import db, Book, PriceHistory, Order


class SmartPricing:
    """智能定价引擎"""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def calculate_price(self, book_data):
        """
        计算智能定价
        
        参数:
            book_data: 包含书籍信息的字典
                - original_price: 原价
                - condition: 新旧程度 (new, like_new, good, fair, poor)
                - edition: 版本 (latest, recent, old)
                - category: 分类
                - isbn: ISBN号
        
        返回:
            dict: 包含定价信息的字典
        """
        # 1. 获取基础价格
        base_price = self._get_base_price(book_data)
        
        # 2. 新旧程度系数
        condition_multiplier = self._get_condition_multiplier(book_data.get('condition', 'good'))
        
        # 3. 版本系数
        edition_multiplier = self._get_edition_multiplier(book_data.get('edition', 'recent'))
        
        # 4. 市场供需系数
        demand_multiplier = self._get_demand_multiplier(
            book_data.get('isbn'),
            book_data.get('category')
        )
        
        # 5. 综合计算
        smart_price = base_price * condition_multiplier * edition_multiplier * demand_multiplier
        
        # 6. 价格修正（确保在合理范围内）
        smart_price = self._adjust_price(smart_price, base_price)
        
        # 7. 返回价格区间和建议价
        return {
            'base_price': base_price,
            'smart_price': round(smart_price, 2),
            'min_price': round(smart_price * 0.8, 2),
            'max_price': round(smart_price * 1.2, 2),
            'condition_score': condition_multiplier,
            'edition_score': edition_multiplier,
            'demand_score': demand_multiplier
        }
    
    def _get_base_price(self, book_data):
        """获取基础价格"""
        original_price = book_data.get('original_price')
        
        if original_price and original_price > 0:
            # 有原价时，默认为原价的 30-50%
            return original_price * 0.4
        
        # 没有原价时，基于分类估算
        category_prices = {
            '教材': 15,
            '小说': 12,
            '杂志': 8,
            '工具书': 20,
            '其他': 10
        }
        return category_prices.get(book_data.get('category', '其他'), 10)
    
    def _get_condition_multiplier(self, condition):
        """获取新旧程度系数"""
        weights = {
            'new': 1.0,       # 全新
            'like_new': 0.9,  # 几乎全新
            'good': 0.7,      # 较好
            'fair': 0.5,      # 一般
            'poor': 0.3       # 较差
        }
        return weights.get(condition, 0.7)
    
    def _get_edition_multiplier(self, edition):
        """获取版本系数"""
        weights = {
            'latest': 1.0,   # 最新版
            'recent': 0.85,  # 近几年
            'old': 0.6       # 旧版
        }
        return weights.get(edition, 0.85)
    
    def _get_demand_multiplier(self, isbn=None, category=None):
        """获取市场供需系数"""
        # 计算同一ISBN或分类的供给数量
        supply_count = 0
        demand_count = 0
        
        if isbn:
            # 统计同ISBN的在售书籍数量（供给）
            supply_count = Book.query.filter(
                Book.isbn == isbn,
                Book.status == 'available'
            ).count()
            
            # 统计同ISBN的想要人数（需求）
            demand_count = Book.query.filter(
                Book.isbn == isbn
            ).with_entities(func.sum(Book.want_count)).scalar() or 0
        
        if category and supply_count == 0:
            # 如果没有ISBN信息，使用分类统计
            supply_count = Book.query.filter(
                Book.category == category,
                Book.status == 'available'
            ).count()
        
        # 计算供需比
        if supply_count == 0:
            # 无供给时，使用基准系数
            return 1.1
        
        if demand_count == 0:
            demand_count = 1
        
        ratio = demand_count / supply_count
        
        # 根据供需比计算系数
        if ratio > 2:
            return 1.3  # 供不应求
        elif ratio > 1:
            return 1.1  # 略供不应求
        elif ratio == 1:
            return 1.0  # 平衡
        else:
            return 0.9  # 供过于求
    
    def _adjust_price(self, price, base_price):
        """价格修正，确保在合理范围内"""
        min_price = self.config.get('base_price_range', (5, 100))[0]
        max_price = self.config.get('base_price_range', (5, 100))[1]
        
        # 价格不应该低于最低价
        price = max(price, min_price)
        
        # 价格不应该高于原价（如果有）
        if base_price and price > base_price * 0.9:
            price = base_price * 0.9
        
        return price
    
    def get_historical_prices(self, isbn):
        """获取历史价格数据"""
        if not isbn:
            return []
        
        prices = PriceHistory.query.filter(
            PriceHistory.isbn == isbn
        ).order_by(PriceHistory.created_at.desc()).limit(20).all()
        
        return [{
            'price': p.price,
            'type': p.price_type,
            'date': p.created_at.strftime('%Y-%m-%d')
        } for p in prices]
    
    def record_price(self, isbn, book_id, price, price_type='smart'):
        """记录价格到历史"""
        price_record = PriceHistory(
            isbn=isbn,
            book_id=book_id,
            price=price,
            price_type=price_type
        )
        db.session.add(price_record)
        db.session.commit()
    
    def get_average_deal_price(self, isbn):
        """获取同ISBN书籍的平均成交价"""
        if not isbn:
            return None
        
        # 查找已完成的订单中同ISBN书籍的成交价
        result = db.session.query(func.avg(Book.final_price)).join(
            Order, Order.book_id == Book.id
        ).filter(
            Book.isbn == isbn,
            Order.status == 'completed',
            Book.final_price.isnot(None)
        ).scalar()
        
        return round(result, 2) if result else None


def calculate_smart_price(book_data, config=None):
    """
    便捷函数：计算智能定价
    """
    pricing = SmartPricing(config)
    return pricing.calculate_price(book_data)
