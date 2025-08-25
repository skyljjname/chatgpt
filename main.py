# -*- coding: utf-8 -*-
"""
文件内容提取与上传工具 - 主程序入口
模块化版本
"""

import sys
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """检查必要的依赖"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    # pycryptodome是可选的，会在crypto_utils中处理
    
    if missing_deps:
        error_msg = f"缺少必要的依赖包:\n{', '.join(missing_deps)}\n\n"
        error_msg += "请安装缺少的依赖包:\n"
        for dep in missing_deps:
            if dep == "tkinter":
                error_msg += "- tkinter: 通常随Python安装，如果缺少请重新安装Python\n"
            elif dep == "requests":
                error_msg += "- requests: pip install requests\n"
        
        print(error_msg)
        return False
    
    return True

def setup_path():
    """设置模块路径"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

def main():
    """主函数"""
    # 检查依赖
    if not check_dependencies():
        input("按任意键退出...")
        sys.exit(1)
    
    # 设置路径
    setup_path()
    
    try:
        # 导入应用程序类
        from ui.main_window import MainApplication
        
        # 创建主窗口
        root = tk.Tk()
        app = MainApplication(root)
        
        # 启动主循环
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"导入模块失败: {str(e)}\n\n请确保所有模块文件都在正确的位置。"
        print(error_msg)
        messagebox.showerror("导入错误", error_msg)
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("程序被用户中断")
        
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        print(error_msg)
        messagebox.showerror("运行错误", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()