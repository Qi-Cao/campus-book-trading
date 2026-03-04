"""
百炼大模型工具类
用于OCR识别和图像理解（评估书籍新旧程度）
"""
import json
import os
from config import Config

# 尝试导入 dashscope
try:
    import dashscope
    from dashscope import MultiModalConversation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("Warning: dashscope not installed. Install with: pip install dashscope")


class BookAIAnalyzer:
    """书籍AI分析器 - 同时完成OCR和图像理解"""
    
    def __init__(self):
        self.api_key = Config.DASHSCOPE_API_KEY
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not configured. Please set it in .env file.")
        
        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.api_key
    
    def analyze_book_image(self, image_path=None, image_url=None, image_base64=None):
        """
        分析书籍图片，同时识别：
        1. OCR文字（书名、作者、ISBN、出版社）
        2. 图像理解（新旧程度评估）
        
        参数:
            image_path: 本地图片路径
            image_url: 图片URL
            image_base64: Base64编码的图片
            
        返回:
            dict: 包含识别结果的字典
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                'success': False,
                'error': 'dashscope not installed',
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None
            }
        
        # 准备图片输入
        if image_path:
            image_input = f"file://{image_path}"
        elif image_url:
            image_input = image_url
        elif image_base64:
            image_input = f"data:image/jpeg;base64,{image_base64}"
        else:
            return {
                'success': False,
                'error': 'No image provided',
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None
            }
        
        # 构建Prompt - 包含出版社和原价识别
        prompt = """请分析这张二手书籍照片，要求：
1. 识别图中文字，提取书名、作者、ISBN、出版社、书籍原价（如有）
2. 根据书籍封面磨损程度、页面笔记、折痕等情况，评估这本书的新旧程度

请按以下JSON格式输出：
{
    "book_name": "书名（如有）",
    "author": "作者（如有）", 
    "isbn": "ISBN（如有）",
    "publisher": "出版社（如有）",
    "original_price": 原价（如有，如 49.00 或 49元），只返回数字，如果没有返回 null,
    "condition": "全新/几乎全新/较好/一般/较差",
    "condition_reason": "评估依据简要说明"
}

如果无法识别某项，请返回null。"""

        # 调用百炼多模态模型
        messages = [
            {
                'role': 'user',
                'content': [
                    {'image': image_input},
                    {'text': prompt}
                ]
            }
        ]
        
        try:
            response = MultiModalConversation.call(
                model='qwen-vl-plus',
                messages=messages
            )
            
            if response.status_code == 200:
                # 解析返回结果
                content = response.output.choices[0].message.content
                result_text = content[0]['text']
                
                # 尝试解析JSON
                return self._parse_json_response(result_text)
            else:
                return {
                    'success': False,
                    'error': f"API error: {response.code} - {response.message}",
                    'book_name': None,
                    'original_price': None,
                    'author': None,
                    'isbn': None,
                    'publisher': None,
                    'condition': None,
                    'condition_reason': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None
            }
    
    def analyze_multiple_images(self, image_paths=None, image_urls=None, image_base64_list=None):
        """
        批量分析多张书籍图片，综合提取信息
        
        参数:
            image_paths: 本地图片路径列表
            image_urls: 图片URL列表
            image_base64_list: Base64编码的图片列表
            
        返回:
            dict: 综合所有图片的识别结果
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                'success': False,
                'error': 'dashscope not installed',
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None,
                'images_analyzed': 0
            }
        
        # 准备多张图片
        image_contents = []
        
        if image_paths:
            for path in image_paths:
                image_contents.append({'image': f"file://{path}"})
        elif image_urls:
            for url in image_urls:
                image_contents.append({'image': url})
        elif image_base64_list:
            for b64 in image_base64_list:
                image_contents.append({'image': f"data:image/jpeg;base64,{b64}"})
        
        if not image_contents:
            return {
                'success': False,
                'error': 'No images provided',
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None,
                'images_analyzed': 0
            }
        
        # 构建Prompt - 包含出版社和原价识别
        prompt = """请分析这些二手书籍照片（多张图片），要求：
1. 综合所有图片中的文字信息，提取书名、作者、ISBN、出版社、书籍原价（如有）
2. 根据书籍封面磨损程度、页面笔记、折痕等情况，评估这本书的新旧程度
3. 如果某些信息在某张图片上找不到，可能在另一张图片上，仔细对比所有图片

请按以下JSON格式输出：
{
    "book_name": "书名（综合判断）",
    "author": "作者（综合判断）", 
    "isbn": "ISBN（综合判断）",
    "publisher": "出版社（综合判断）",
    "original_price": 原价（如有，如 49.00 或 49元），只返回数字，如果没有返回 null,
    "condition": "全新/几乎全新/较好/一般/较差",
    "condition_reason": "评估依据简要说明"
}

如果无法识别某项，请返回null。"""

        # 调用百炼多模态模型
        messages = [
            {
                'role': 'user',
                'content': image_contents + [{'text': prompt}]
            }
        ]
        
        try:
            response = MultiModalConversation.call(
                model='qwen-vl-plus',
                messages=messages
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                result_text = content[0]['text']
                
                result = self._parse_json_response(result_text)
                result['images_analyzed'] = len(image_contents)
                return result
            else:
                return {
                    'success': False,
                    'error': f"API error: {response.code} - {response.message}",
                    'book_name': None,
                    'original_price': None,
                    'author': None,
                    'isbn': None,
                    'publisher': None,
                    'condition': None,
                    'condition_reason': None,
                    'images_analyzed': len(image_contents)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None,
                'images_analyzed': len(image_contents)
            }
    
    def _parse_json_response(self, text):
        """解析JSON响应"""
        try:
            # 尝试直接解析JSON
            data = json.loads(text)
            return {
                'success': True,
                'book_name': data.get('book_name'),
            'original_price': data.get('original_price'),
                'author': data.get('author'),
                'isbn': data.get('isbn'),
                'publisher': data.get('publisher'),
                'condition': data.get('condition'),
                'condition_reason': data.get('condition_reason')
            }
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON块
            import re
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return {
                        'success': True,
                        'book_name': data.get('book_name'),
            'original_price': data.get('original_price'),
                        'author': data.get('author'),
                        'isbn': data.get('isbn'),
                        'publisher': data.get('publisher'),
                        'condition': data.get('condition'),
                        'condition_reason': data.get('condition_reason')
                    }
                except:
                    pass
            
            # 无法解析，返回原始文本
            return {
                'success': True,
                'raw_text': text,
                'book_name': None,
                'original_price': None,
                'author': None,
                'isbn': None,
                'publisher': None,
                'condition': None,
                'condition_reason': None,
                'parse_warning': 'Could not parse JSON, please check manually'
            }
    
    def test_connection(self):
        """测试API连接"""
        if not DASHSCOPE_AVAILABLE:
            return {'success': False, 'error': 'dashscope not installed'}
        
        try:
            messages = [
                {
                    'role': 'user',
                    'content': [{'text': '你好'}]
                }
            ]
            response = dashscope.Generation.call(
                model='qwen-turbo',
                messages=messages
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Connection OK'}
            else:
                return {'success': False, 'error': f'{response.code} - {response.message}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def analyze_book_image(image_path=None, image_url=None, image_base64=None):
    """
    便捷函数：分析单张书籍图片
    """
    try:
        analyzer = BookAIAnalyzer()
        return analyzer.analyze_book_image(image_path, image_url, image_base64)
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'book_name': None,
            'author': None,
            'isbn': None,
            'publisher': None,
            'condition': None,
            'condition_reason': None
        }


def analyze_multiple_images(image_paths=None, image_urls=None, image_base64_list=None):
    """
    便捷函数：批量分析多张书籍图片
    """
    try:
        analyzer = BookAIAnalyzer()
        return analyzer.analyze_multiple_images(image_paths, image_urls, image_base64_list)
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'book_name': None,
            'author': None,
            'isbn': None,
            'publisher': None,
            'condition': None,
            'condition_reason': None,
            'images_analyzed': 0
        }
