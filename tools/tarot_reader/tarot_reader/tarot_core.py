"""Simple Tarot Card Implementation"""
import random
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

@dataclass
class TarotCard:
    """Represents a single Tarot card"""
    name: str
    meaning_up: str
    meaning_rev: str
    element: str
    number: int
    keywords: list[str]
    reversed: bool = False
    
    @property
    def meaning(self) -> str:
        return self.meaning_rev if self.reversed else self.meaning_up

class TarotDeck:
    """Represents a deck of Tarot cards"""
    def __init__(self):
        self.cards = self._create_deck()
        self.shuffle()
    
    def _create_deck(self) -> List[TarotCard]:
        """Create a standard deck of Tarot cards"""
        cards = []
        # Major Arcana
        major_arcana = [
            (0, "The Fool", "新的开始，冒险，纯真", "鲁莽，冒失，过度冒险", "风", 
             ["开始", "冒险", "自由"]),
            (1, "The Magician", "创造力，技能，意志力", "欺骗，犹豫，技能不足", "火",
             ["创造", "技能", "意志"]),
            (2, "The High Priestess", "直觉，神秘，内在知识", "表面性格，隐藏的敌意", "水",
             ["直觉", "神秘", "智慧"]),
            (3, "The Empress", "丰收，母性，创造力", "依赖，空虚，缺乏创造力", "土",
             ["丰收", "母性", "创造"]),
            # ... 更多卡牌数据
        ]
        
        for num, name, up, rev, elem, keys in major_arcana:
            cards.append(TarotCard(name, up, rev, elem, num, keys))
        
        return cards
    
    def shuffle(self) -> None:
        """Shuffle the deck"""
        random.shuffle(self.cards)
        for card in self.cards:
            card.reversed = random.random() < 0.2  # 20% 概率逆位
    
    def draw(self) -> TarotCard:
        """Draw a card from the deck"""
        if not self.cards:
            self.cards = self._create_deck()
            self.shuffle()
        return self.cards.pop()

class TarotAnalyzer:
    """分析卡牌关系"""
    
    def __init__(self):
        # 初始化分析器的配置
        self.elements = {
            "火": {"火": "激情加强", "水": "互相抵消", "风": "助长火势", "土": "火土相容"},
            "水": {"火": "水火不容", "水": "随波逐流", "风": "风平浪静", "土": "润物无声"},
            # ... 更多元素关系
        }
        
        self.special_combinations = {
            ("The Fool", "The World"): "一个周期的完整轮回",
            ("The High Priestess", "The Magician"): "内在与外在力量的结合",
            ("The Emperor", "The Empress"): "阴阳平衡，理想的合作",
            ("Death", "The Sun"): "经过转变后的重生",
            ("The Moon", "The Sun"): "从迷惑到清晰的过程",
        }
    
    def analyze_relationship(self, cards: List[TarotCard]) -> str:
        """分析卡牌之间的关系"""
        if len(cards) == 1:
            return "单张牌解读"
            
        analysis = []
        
        # 分析相邻卡牌
        for i in range(len(cards)-1):
            card1, card2 = cards[i], cards[i+1]
            
            # 元素关系
            element_harmony = self._analyze_elements(card1.element, card2.element)
            analysis.append(f"「{card1.name}」和「{card2.name}」的元素关系：{element_harmony}")
            
            # 数字关系
            number_meaning = self._analyze_numbers(card1.number, card2.number)
            analysis.append(f"数字关系显示：{number_meaning}")
            
            # 象征意义
            symbol_connection = self._find_symbol_connection(card1, card2)
            analysis.append(f"象征意义的联系：{symbol_connection}")
            
            # 正逆位互动
            position_impact = self._analyze_positions(card1, card2)
            analysis.append(f"位置影响：{position_impact}")
        
        # 整体趋势
        trend = self._analyze_trend(cards)
        analysis.append(f"\n整体发展趋势：{trend}")
        
        return "\n".join(analysis)

    def _analyze_elements(self, element1: str, element2: str) -> str:
        """分析元素相生相克"""
        return self.elements.get(element1, {}).get(element2, "中性关系")

    def _analyze_trend(self, cards: List[TarotCard]) -> str:
        """分析整体趋势"""
        all_upright = all(not card.reversed for card in cards)
        all_reversed = all(card.reversed for card in cards)
        
        if all_upright:
            return "整体发展顺利，充满积极能量"
        elif all_reversed:
            return "当前面临较大挑战，需要调整心态"
        else:
            return "起伏变化中蕴含机遇，保持灵活应对"

    def _analyze_numbers(self, num1: int, num2: int) -> str:
        """分析数字关系"""
        diff = abs(num1 - num2)
        
        # 数字差值的含义
        diff_meanings = {
            0: "重复强调，加强当前主题",
            1: "紧密相连，自然过渡",
            2: "需要调和，寻找平衡",
            3: "变化显著，需要适应",
            4: "稳定基础上的改变",
            5: "重大转折点",
            6: "循环完成，新的开始",
            7: "神秘数字，深层启示",
            8: "力量与平衡的考验",
            9: "完成与新生的交替",
            10: "一个周期的结束"
        }
        
        # 数字本身的含义
        number_meanings = {
            0: "无限可能",
            1: "开始，独立",
            2: "二元性，合作",
            3: "创造，表达",
            4: "稳定，基础",
            5: "变化，自由",
            6: "和谐，责任",
            7: "探索，神秘",
            8: "力量，物质",
            9: "完成，智慧",
            10: "圆满，循环"
        }
        
        return f"{number_meanings.get(num1, '')}与{number_meanings.get(num2, '')}的关系：{diff_meanings.get(diff, '中性关系')}"

    def _find_symbol_connection(self, card1: TarotCard, card2: TarotCard) -> str:
        """分析卡牌间的象征意义联系"""
        # 检查关键词重叠
        common_keywords = set(card1.keywords) & set(card2.keywords)
        
        analysis = []
        
        # 添加关键词分析
        if common_keywords:
            analysis.append(f"共同主题：{', '.join(common_keywords)}")
        
        # 添加特殊组合分析
        combo = (card1.name, card2.name)
        if combo in self.special_combinations:
            analysis.append(self.special_combinations[combo])
        elif (card2.name, card1.name) in self.special_combinations:
            analysis.append(self.special_combinations[(card2.name, card1.name)])
        
        # 分析正逆位关系
        if card1.reversed == card2.reversed:
            analysis.append("能量方向一致" if not card1.reversed else "共同面临挑战")
        else:
            analysis.append("能量互补，寻求平衡")
        
        return "；".join(analysis)

    def _analyze_positions(self, card1: TarotCard, card2: TarotCard) -> str:
        """分析卡牌位置的影响"""
        position_effects = []
        
        # 分析正逆位组合
        if not card1.reversed and not card2.reversed:
            position_effects.append("双正位显示进展顺利")
        elif card1.reversed and card2.reversed:
            position_effects.append("双逆位提醒需要特别注意")
        else:
            position_effects.append("正逆交替说明情况在变化")
        
        # 分析能量流动
        if card1.element == card2.element:
            position_effects.append(f"同为{card1.element}元素，能量加强")
        else:
            position_effects.append(f"从{card1.element}到{card2.element}的能量转换")
        
        return "，".join(position_effects)