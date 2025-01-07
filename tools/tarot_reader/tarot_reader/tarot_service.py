"""Tarot Reader Service"""
import logging
import time
from typing import List, Dict, Any
from tarot_core import TarotDeck, TarotAnalyzer, TarotCard

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TarotService:
    """塔罗牌服务"""
    
    def __init__(self):
        self.deck = TarotDeck()
        self.analyzer = TarotAnalyzer()
        logger.info("塔罗牌服务初始化完成")
    
    def do_reading(self, question: str, spread_type: str) -> Dict[str, Any]:
        """执行塔罗牌解读"""
        start_time = time.time()
        logger.info("开始新的塔罗牌解读...")
        logger.info(f"问题: {question}")
        logger.info(f"牌阵类型: {spread_type}")

        # 将英文spread_type转换为中文
        spread_type_map = {
            "single_card": "单张牌",
            "three_card": "三张牌",
            "celtic_cross": "凯尔特十字"
        }
        chinese_spread_type = spread_type_map.get(spread_type)
        if not chinese_spread_type:
            error_msg = f"无效的牌阵类型: {spread_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        num_cards = {"单张牌": 1, "三张牌": 3, "凯尔特十字": 10}[chinese_spread_type]
        
        if not question.strip():
            logger.warning("提供了空问题")
            return {"error": "请输入你的问题"}
            
        # 洗牌并抽取
        logger.info("开始洗牌...")
        shuffle_start = time.time()
        self.deck.shuffle()
        logger.info(f"洗牌完成，耗时: {(time.time() - shuffle_start)*1000:.2f}ms")
        
        logger.info(f"抽取{num_cards}张牌...")
        draw_start = time.time()
        cards = [self.deck.draw() for _ in range(num_cards)]
        logger.info(f"抽牌完成，耗时: {(time.time() - draw_start)*1000:.2f}ms")
        
        # 生成解读结果
        logger.info("生成解读结果...")
        positions = {
            "单张牌": ["当前形势"],
            "三张牌": ["过去", "现在", "未来"],
            "凯尔特十字": [
                "当前形势", "阻碍", "基础", "过去",
                "思维", "未来", "自我", "环境",
                "希望/恐惧", "最终结果"
            ]
        }
        
        result = [f"问题: {question}\n", f"牌阵: {chinese_spread_type}\n"]
        for card, position in zip(cards, positions[chinese_spread_type]):
            logger.info(f"位置 '{position}': {card.name} {'(逆位)' if card.reversed else '(正位)'}")
            result.append(f"\n{position}:")
            result.append(f"牌面: {card.name} {'逆位' if card.reversed else '正位'}")
            result.append(f"含义: {card.meaning}\n")
        
        # 添加卡牌关联分析
        if len(cards) > 1:
            logger.info("执行卡牌关联分析...")
            analysis = self.analyzer.analyze_relationship(cards)
            
            result.append("\n==== 详细分析 ====")
            result.append(analysis)
            result.append("\n==== 建议 ====")
            result.append(self._generate_advice(cards))
        
        reading_result = "\n".join(result)
        
        # 构造返回结果
        response = {
            "cards": [
                {
                    "id": i,
                    "name": card.name,
                    "meaning": card.meaning,
                    "reversed": card.reversed
                }
                for i, card in enumerate(cards)
            ],
            "result": reading_result
        }
        
        total_time = (time.time() - start_time) * 1000
        logger.info(f"塔罗牌解读完成，总耗时: {total_time:.2f}ms")
        
        return response

    def _generate_advice(self, cards: List[TarotCard]) -> str:
        """生成建议"""
        logger.info("生成建议...")
        # 根据卡牌组合生成具体建议
        if all(not card.reversed for card in cards):
            advice = "当前形势积极，建议：\n1. 把握机会，大胆行动\n2. 保持当前的发展方向"
            logger.info("生成积极建议")
        elif all(card.reversed for card in cards):
            advice = "当前面临挑战，建议：\n1. 调整心态，重新规划\n2. 寻求他人帮助"
            logger.info("生成谨慎建议")
        else:
            advice = "形势喜忧参半，建议：\n1. 灵活应对，保持平衡\n2. 关注积极的信号"
            logger.info("生成平衡建议")
        return advice 