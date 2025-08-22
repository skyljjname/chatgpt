# -*- coding: utf-8 -*-
"""
加密工具模块
提供3DES解密和数据格式化功能
"""

import base64
import json
import re
from typing import List, Tuple, Optional, Dict, Any
from config.settings import Config

try:
    from Crypto.Cipher import DES3
    from Crypto.Util.Padding import unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class CryptoUtils:
    """加密工具类，提供3DES解密等功能"""
    
    def __init__(self):
        self.config = Config
        self.des3_key = self.config.DES3_KEY
        self.debug_mode = True
    
    def decrypt_3des_ecb(self, encrypted_data: str) -> str:
        """
        3DES ECB模式解密，保守的填充处理方式
        
        Args:
            encrypted_data: Base64编码的加密数据
            
        Returns:
            解密后的文本
        """
        if not CRYPTO_AVAILABLE:
            return "[解密失败: 缺少加密库，请安装 pycryptodome]"
        
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 创建3DES解密器（ECB模式）
            cipher = DES3.new(self.des3_key, DES3.MODE_ECB)
            
            # 解密
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            
            # 保守的处理方式：尝试多种策略
            decoded_results = []
            
            # 策略1：直接解码，不去除任何字节
            try:
                result1 = decrypted_bytes.decode('utf-8', errors='ignore')
                if len(result1.strip()) > 10:  # 确保有实际内容
                    decoded_results.append(("完整", result1))
            except Exception:
                pass
            
            # 策略2：标准PKCS7去填充
            try:
                unpadded_bytes = unpad(decrypted_bytes, DES3.block_size)
                result2 = unpadded_bytes.decode('utf-8', errors='ignore')
                if len(result2.strip()) > 10:
                    decoded_results.append(("PKCS7", result2))
            except Exception:
                pass
            
            # 策略3：只去除末尾的零字节（最多去除8个字节，DES块大小）
            try:
                temp_bytes = decrypted_bytes
                removed_count = 0
                while (len(temp_bytes) > 0 and 
                       temp_bytes[-1] == 0 and 
                       removed_count < 8):  # 最多去除一个DES块的大小
                    temp_bytes = temp_bytes[:-1]
                    removed_count += 1
                
                result3 = temp_bytes.decode('utf-8', errors='ignore')
                if len(result3.strip()) > 10:
                    decoded_results.append(("限制零填充", result3))
            except Exception:
                pass
            
            # 选择最佳结果：优先选择能解析为有效JSON的结果
            best_result = None
            
            for strategy, result in decoded_results:
                try:
                    if result.strip().startswith('{'):
                        json.loads(result.strip())  # 验证JSON
                        if self.debug_mode:
                            print(f"使用{strategy}策略成功解密并验证JSON")
                        return result
                except json.JSONDecodeError:
                    continue
            
            # 如果没有有效的JSON，返回最长的结果
            if decoded_results:
                best_result = max(decoded_results, key=lambda x: len(x[1]))[1]
                if self.debug_mode:
                    strategy_name = max(decoded_results, key=lambda x: len(x[1]))[0]
                    print(f"使用{strategy_name}策略解密（未验证JSON）")
                return best_result
            
            # 如果所有策略都失败，返回错误信息
            return "[解密失败: 所有解密策略都未成功]"
            
        except Exception as e:
            if self.debug_mode:
                print(f"3DES解密失败: {str(e)}")
            return f"[解密失败: {str(e)}]"
    
    def format_json_tree_structure(self, text: str) -> str:
        """
        将JSON数据格式化为树状结构显示
        
        Args:
            text: JSON文本
            
        Returns:
            格式化后的树状结构
        """
        if not text or not text.strip():
            return "[空数据]"
        
        try:
            # 尝试解析为标准JSON
            if text.strip().startswith('{') and text.strip().endswith('}'):
                json_obj = json.loads(text)
                return self._build_json_tree(json_obj)
            
            # 处理非标准JSON格式
            cleaned_text = text.strip()
            if '{' in cleaned_text and '}' in cleaned_text:
                # 提取大括号内的内容并尝试修复
                match = re.search(r'\{(.*?)\}', cleaned_text, re.DOTALL)
                if match:
                    content = match.group(1)
                    json_obj = self._parse_key_value_pairs(content)
                    if json_obj:
                        return self._build_json_tree(json_obj)
            
            # 如果无法解析为JSON，按文本结构显示
            return self._format_structured_text(text)
            
        except json.JSONDecodeError:
            return self._format_structured_text(text)
        except Exception as e:
            return f"[格式化失败: {str(e)}]\n\n原始解密内容:\n{text}"
    
    def _build_json_tree(self, obj: Any, indent: int = 0, path: str = "root") -> str:
        """构建JSON树状结构"""
        lines = []
        indent_str = "  " * indent
        
        if isinstance(obj, dict):
            if indent == 0:
                lines.append(f"JSON数据 (共{len(obj)}个字段)")
                lines.append("")
            
            items = list(obj.items())
            for i, (key, value) in enumerate(items):
                is_last = (i == len(items) - 1)
                current_prefix = "└─ " if is_last else "├─ "
                next_indent_char = "   " if is_last else "│  "
                
                # 显示键名
                lines.append(f"{indent_str}{current_prefix} {key}:")
                
                # 递归显示值内容
                if isinstance(value, (dict, list)):
                    sub_lines = self._build_json_tree(value, indent + 1, f"{path}.{key}")
                    for line in sub_lines:
                        lines.append(f"{indent_str}{next_indent_char}{line}")
                else:
                    # 叶子节点，显示完整的实际值
                    formatted_value = self._format_complete_leaf_value(value)
                    value_lines = formatted_value.split('\n')
                    for j, value_line in enumerate(value_lines):
                        lines.append(f"{indent_str}{next_indent_char}    {value_line}")
        
        elif isinstance(obj, list):
            lines.append(f"数组 (共{len(obj)}个元素)")
            for i, item in enumerate(obj):
                is_last = (i == len(obj) - 1)
                current_prefix = "└─ " if is_last else "├─ "
                next_indent_char = "   " if is_last else "│  "
                
                lines.append(f"{indent_str}{current_prefix}[{i}]:")
                
                if isinstance(item, (dict, list)):
                    sub_lines = self._build_json_tree(item, indent + 1, f"{path}[{i}]")
                    for line in sub_lines:
                        lines.append(f"{indent_str}{next_indent_char}{line}")
                else:
                    formatted_value = self._format_complete_leaf_value(item)
                    value_lines = formatted_value.split('\n')
                    for j, value_line in enumerate(value_lines):
                        lines.append(f"{indent_str}{next_indent_char}    {value_line}")
        
        return '\n'.join(lines)
    
    def _format_complete_leaf_value(self, value: Any) -> str:
        """格式化叶子节点的值 - 处理多条数据分割显示"""
        if isinstance(value, str):
            # 使用 detect_and_split_multi_data 分割
            multi_data = self._detect_and_split_multi_data(value)

            # 多条记录，编号显示
            if len(multi_data) > 1:
                return '\n'.join(f"[{i}] {item}" for i, item in enumerate(multi_data, 1))

            # 单条记录，如果包含换行符，逐行加引号显示
            single_line = multi_data[0]
            if '\n' in single_line:
                return '\n'.join(f'"{line}"' for line in single_line.split('\n'))

            # 单条普通文本
            return f'"{single_line}"'

        # 非字符串类型处理
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"

        # 其他类型直接转字符串
        return str(value)
    
    def _detect_and_split_multi_data(self, text: str) -> List[str]:
        """根据内容类型分割数据：含#用逗号，不含#用换行符"""
        if not text or len(text.strip()) == 0:
            return [text]

        text = text.strip()

        # 含 # 的数据，按逗号分割
        if '#' in text:
            parts = [part.strip() for part in text.split(',') if part.strip()]
            return parts

        # 不含 # 的数据，按换行符分割
        if '\n' in text:
            parts = [part.strip() for part in text.split('\n') if part.strip()]
            return parts

        # 都不符合，返回单条
        return [text]
    
    def _parse_key_value_pairs(self, content: str) -> Optional[Dict[str, Any]]:
        """解析键值对内容为字典"""
        result = {}
        items = self._smart_split_key_value_pairs(content)
        
        for item in items:
            item = item.strip()
            if ':' in item:
                # 找到第一个冒号
                colon_pos = item.find(':')
                key = item[:colon_pos].strip().strip('"\'')
                value = item[colon_pos+1:].strip()
                
                # 移除值两端的引号，但保留内部引号
                if ((value.startswith('"') and value.endswith('"')) or 
                    (value.startswith("'") and value.endswith("'"))):
                    value = value[1:-1]
                
                # 尝试转换值的类型，但保持字符串的完整性
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.lower() == 'null' or value == '':
                    value = None
                elif value.replace('.', '').replace('-', '').replace('+', '').isdigit():
                    value = float(value) if '.' in value else int(value)
                # 否则保持为字符串
                
                result[key] = value
        
        return result if result else None
    
    def _smart_split_key_value_pairs(self, content: str) -> List[str]:
        """智能分割键值对，处理嵌套结构"""
        items = []
        current_item = ""
        brace_count = 0
        quote_count = 0
        in_quotes = False
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == '"' and (i == 0 or content[i-1] != '\\'):
                in_quotes = not in_quotes
                quote_count += 1 if in_quotes else -1
            elif not in_quotes:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char in [',', '，'] and brace_count == 0:
                    # 在没有嵌套的情况下遇到逗号，分割
                    if current_item.strip():
                        items.append(current_item.strip())
                    current_item = ""
                    i += 1
                    continue
            
            current_item += char
            i += 1
        
        # 添加最后一项
        if current_item.strip():
            items.append(current_item.strip())
        
        return items if items else [content]
    
    def _format_structured_text(self, text: str) -> str:
        """格式化结构化文本 - 用于无法解析为JSON的解密数据"""
        lines = ["解密数据内容:"]
        lines.append("=" * 50)
        lines.append("")
        
        # 如果包含键值对模式
        if ':' in text and ('{' in text or ',' in text):
            lines.append("检测到键值对结构，尝试解析:")
            lines.append("")
            
            # 尝试按键值对解析
            content = text.strip('{}')
            items = self._smart_split_key_value_pairs(content)
            
            for i, item in enumerate(items, 1):
                item = item.strip()
                if ':' in item:
                    # 找到第一个冒号作为分隔符
                    colon_pos = item.find(':')
                    key = item[:colon_pos].strip()
                    value = item[colon_pos+1:].strip()
                    
                    lines.append(f" {key}:")
                    # 如果值很长或包含换行，分行显示
                    if len(value) > 80 or '\n' in value:
                        value_lines = value.split('\n') if '\n' in value else [
                            value[j:j+80] for j in range(0, len(value), 80)
                        ]
                        for value_line in value_lines:
                            lines.append(f"    {value_line}")
                    else:
                        lines.append(f"    {value}")
                    lines.append("")
                else:
                    lines.append(f" 其他内容: {item}")
                    lines.append("")
        else:
            # 普通文本完整显示
            lines.append("完整内容:")
            lines.append(text)
        
        return '\n'.join(lines)
    
    def format_raw_data_display(self, text: str) -> str:
        """格式化原始数据显示 - 完全按原始内容显示"""
        if not text:
            return "[空数据]"
        
        # 直接返回原始数据，不添加行号、不分行处理
        return text
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled