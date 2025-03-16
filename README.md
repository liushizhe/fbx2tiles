# FBX to 3D Tiles Converter

这个工具可以将FBX格式的3D模型转换为3D Tiles格式，适用于3D地图应用和Web端3D可视化。

## 功能特点

- 支持FBX格式的3D模型转换
- 生成符合3D Tiles规范的输出文件
- 简单易用的命令行接口

## 安装

1. 确保已安装Python 3.7或更高版本
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

3. 安装FBX2glTF工具（必需）:
   - 从 [FBX2glTF GitHub仓库](https://github.com/facebookincubator/FBX2glTF/releases) 下载最新版本
   - 将FBX2glTF可执行文件添加到系统PATH环境变量中

## 使用方法

基本用法：

```bash
python fbx2tiles.py 输入文件.fbx 输出目录
```

高级选项：

```bash
python fbx2tiles.py 输入文件.fbx 输出目录 --longitude 120 --latitude 39 --height 0 --verbose
```

参数说明：
- `输入文件.fbx`：要转换的FBX文件路径
- `输出目录`：3D Tiles输出目录
- logitude：模型经度
- latitude：模型纬度
- height：模型高度
- `--verbose`：显示详细输出信息

## 输出文件

转换完成后，输出目录将包含以下文件：

- `tileset.json`：3D Tiles的主配置文件
- `tiles/`：包含所有瓦片的目录
  - `model.b3dm`：3D Tiles格式的模型文件

## 如果没有FBX2glTF

如果无法安装FBX2glTF，可以使用以下替代方法：

1. 使用Blender手动转换：
   - 安装 [Blender](https://www.blender.org/)
   - 导入FBX文件 (文件 > 导入 > FBX)
   - 导出为glTF格式 (文件 > 导出 > glTF 2.0)
   - 将导出的glTF文件放在输出目录的temp子目录中，命名为"model.gltf"
   - 然后运行转换工具

2. 使用在线转换服务：
   - [Aspose 3D Conversion](https://products.aspose.app/3d/conversion/fbx-to-gltf)
   - [Online-Convert](https://www.online-convert.com/)

## 示例

```bash
python fbx2tiles.py models/building.fbx output/building_tiles --verbose
```

## 注意事项

- 确保安装了所有依赖项
- FBX2glTF工具是必需的，请确保正确安装
- 转换过程中会创建临时文件，完成后会自动清理

## 依赖项

- numpy
- pygltflib
- trimesh
- python-dateutil
- requests
- pillow
- pybind11
