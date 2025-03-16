"""
构建Windows可执行文件的脚本
使用PyInstaller将fbx2tiles.py打包成独立的exe文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_exe():
    """构建Windows可执行文件"""
    print("开始构建Windows可执行文件...")
    
    # 当前目录
    current_dir = Path(__file__).parent.absolute()
    
    # 构建命令 - 假设PyInstaller已添加到环境变量
    cmd = [
        "pyinstaller",
        "--onefile",  # 生成单个可执行文件
        "--name", "model2tiles",  # 可执行文件名称
        "--icon", "NONE",  # 无图标
        "--clean",  # 清理临时文件
        "--noconfirm",  # 不确认覆盖
        "fbx2tiles.py"  # 主脚本
    ]
    
    # 执行构建命令
    try:
        print(f"运行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, cwd=current_dir)
        print("构建成功！")
        
        # 可执行文件路径
        exe_path = current_dir / "dist" / "model2tiles.exe"
        
        if exe_path.exists():
            print(f"可执行文件已生成: {exe_path}")
            
            # 创建发布目录
            release_dir = current_dir / "release"
            if not release_dir.exists():
                release_dir.mkdir()
            
            # 复制可执行文件到发布目录
            release_exe = release_dir / "model2tiles.exe"
            shutil.copy(exe_path, release_exe)
            
            # 创建README文件
            with open(release_dir / "README.txt", "w", encoding="utf-8") as f:
                f.write("Model2Tiles - 3D模型转3D Tiles工具\n")
                f.write("==================================\n\n")
                f.write("使用方法:\n")
                f.write("model2tiles.exe 输入文件.fbx 输出目录 [选项]\n\n")
                f.write("支持的输入格式:\n")
                f.write("- FBX (.fbx)\n")
                f.write("- glTF (.gltf, .glb)\n\n")
                f.write("选项:\n")
                f.write("--lod-levels N    : 设置LOD级别数量 (默认: 3)\n")
                f.write("--longitude VALUE : 设置经度 (WGS84)\n")
                f.write("--latitude VALUE  : 设置纬度 (WGS84)\n")
                f.write("--height VALUE    : 设置高度 (米)\n")
                f.write("--verbose, -v     : 显示详细输出\n\n")
                f.write("示例:\n")
                f.write("model2tiles.exe model.fbx output --longitude 116.3912757 --latitude 39.906217 --height 50 --verbose\n")
            
            print(f"发布包已准备完成: {release_dir}")
            print("可以将release目录中的文件分发给用户。")
        else:
            print("构建似乎成功，但找不到可执行文件。")
    
    except Exception as e:
        print(f"构建失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_exe()
