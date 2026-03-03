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
        1. OCR文字（书名、作者、ISBN）
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
                'author': None,
                'isbn': None,
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
                'author': None,
                'isbn': None,
                'condition': None,
                'condition_reason': None
            }
        
        # 构建Prompt
        prompt = """请分析这张二手书籍照片，要求：
1. 识别图中文字，提取书名、作者、ISBN（如有）
2. 根据书籍封面磨损程度、页面笔记、折痕等情况，评估这本书的新旧程度

请按以下JSON格式输出：
{
    "book_name": "书名（如有）",
    "author": "作者（如有）", 
    "isbn": "ISBN（如有）",
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
                    'author': None,
                    'isbn': None,
                    'condition': None,
                    'condition_reason': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_name': None,
                'author': None,
                'isbn': None,
                'condition': None,
                'condition_reason': None
            }
    
    def _parse_json_response(self, text):
        """解析JSON响应"""
        try:
            # 尝试直接解析JSON
            data = json.loads(text)
            return {
                'success': True,
                'book_name': data.get('book_name'),
                'author': data.get('author'),
                'isbn': data.get('isbn'),
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
                        'author': data.get('author'),
                        'isbn': data.get('isbn'),
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
                'author': None,
                'isbn': None,
                'condition': None,
                'condition_reason': None,
                'parse_warning': 'Could not parse JSON, please check manually'
            }
    
    def test_connection(self):
        """测试API连接"""
        if not DASHSCOPE_AVAILABLE:
            return {'success': False, 'error': 'dashscope not installed'}
        
        try:
            # 简单测试调用
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
    便捷函数：分析书籍图片
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
            'condition': None,
            'condition_reason': None
        }
