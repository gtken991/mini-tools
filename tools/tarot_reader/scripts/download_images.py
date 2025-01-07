"""Download and process tarot card images from Unsplash"""
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging
import time
import os

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Unsplash API 配置
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')  # 从环境变量获取
UNSPLASH_BASE_URL = "https://api.unsplash.com"

# 塔罗牌图片映射
CARD_IMAGES = {
    "the_fool": "mystical wanderer nature path",
    "the_magician": "magical wizard mystical light",
    "the_high_priestess": "mystical priestess moon night",
    "the_empress": "nature abundance garden flowers",
    "the_emperor": "throne power mountain castle",
    "the_hierophant": "spiritual teacher wisdom temple",
    "the_lovers": "love couple harmony garden",
    "the_chariot": "victory chariot triumph",
    "strength": "lion strength courage nature",
    "the_hermit": "solitary wisdom mountain lantern",
    "wheel_of_fortune": "cosmic wheel fortune stars",
    "justice": "balance scales justice marble",
    "the_hanged_man": "surrender meditation floating",
    "death": "transformation butterfly change",
    "temperance": "balance harmony water flow",
    "the_devil": "dark chains shadow cave",
    "the_tower": "lightning storm tower ruins",
    "the_star": "hope stars night water",
    "the_moon": "mystery moon night water",
    "the_sun": "sun radiance joy nature",
    "judgement": "awakening rebirth light",
    "the_world": "completion universe circle"
}

def search_unsplash(query: str) -> str:
    """从Unsplash搜索图片"""
    try:
        response = requests.get(
            f"{UNSPLASH_BASE_URL}/search/photos",
            params={
                "query": query,
                "orientation": "portrait",
                "per_page": 1
            },
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if data["results"]:
            return data["results"][0]["urls"]["regular"]
        else:
            raise Exception("No images found")
            
    except Exception as e:
        logger.error(f"Failed to search Unsplash: {e}")
        return None

def download_and_process_image(url: str, output_path: Path, size=(300, 450)):
    """下载并处理图片"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # 调整图片大小，保持纵横比
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # 创建新的画布
        new_img = Image.new('RGB', size, (0, 0, 0))
        
        # 将调整后的图片居中粘贴
        offset = ((size[0] - img.size[0]) // 2,
                 (size[1] - img.size[1]) // 2)
        new_img.paste(img, offset)
        
        # 添加边框
        draw = ImageDraw.Draw(new_img)
        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline='#916DB3', width=2)
        
        new_img.save(output_path, quality=95)
        logger.info(f"Successfully saved image to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to process {url}: {e}")
        create_placeholder_image(output_path, size)

def create_card_back(output_dir: Path, size=(300, 450)):
    """创建默认的卡背图片"""
    card_back = Image.new('RGB', size, color='#2B0D41')  # 深紫色背景
    draw = ImageDraw.Draw(card_back)
    
    # 绘制边框
    border = 10
    draw.rectangle([border, border, size[0]-border, size[1]-border], 
                  outline='#916DB3', width=2)
    
    # 添加装饰性图案
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = min(size[0], size[1]) // 4
    
    # 绘制多层圆形装饰
    for i in range(3):
        r = radius - (i * 15)
        draw.ellipse([center_x - r, center_y - r, 
                     center_x + r, center_y + r], 
                    outline='#916DB3', width=2)
    
    # 绘制星形图案
    star_points = []
    for i in range(5):
        angle = i * (2 * 3.14159 / 5) - 3.14159 / 2
        x = center_x + int(radius * 0.5 * -1 * (angle))
        y = center_y + int(radius * 0.5 * -1 * (angle))
        star_points.extend([x, y])
    draw.polygon(star_points, outline='#916DB3', width=2)
    
    card_back.save(output_dir / "card_back.jpg", quality=95)
    logger.info("Created card back image")

def create_placeholder_image(output_path: Path, size=(300, 450)):
    """创建占位图片"""
    img = Image.new('RGB', size, color='#2B0D41')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
        card_name = output_path.stem.replace('_', ' ').title()
        draw.text((size[0]//2, size[1]//2), card_name, 
                  fill='#FFFFFF', anchor="mm", font=font)
    except Exception as e:
        logger.error(f"Error adding text to placeholder: {e}")
    
    img.save(output_path)
    logger.info(f"Created placeholder image for: {output_path.name}")

def main():
    # 检查 Unsplash API key
    if not UNSPLASH_ACCESS_KEY:
        logger.error("请设置 UNSPLASH_ACCESS_KEY 环境变量!")
        return
    
    # 创建输出目录
    output_dir = Path(__file__).parent.parent / "frontend/public/images/cards"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建卡背图片
    card_back_path = output_dir / "card_back.jpg"
    if not card_back_path.exists():
        create_card_back(output_dir)
    
    # 下载并处理每张卡牌图片
    for card_name, search_query in CARD_IMAGES.items():
        output_path = output_dir / f"{card_name}.jpg"
        
        if not output_path.exists():
            logger.info(f"Processing {card_name}...")
            image_url = search_unsplash(search_query)
            
            if image_url:
                download_and_process_image(image_url, output_path)
                # 遵守 Unsplash API 限制，每小时最多 50 次请求
                time.sleep(2)
            else:
                create_placeholder_image(output_path)
        else:
            logger.info(f"Skipping {card_name} (already exists)")

if __name__ == "__main__":
    main() 