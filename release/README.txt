Model2Tiles - 3D模型转3D Tiles工具
==================================

使用方法:
model2tiles.exe 输入文件.fbx 输出目录 [选项]

支持的输入格式:
- FBX (.fbx)
- glTF (.gltf, .glb)

选项:
--lod-levels N    : 设置LOD级别数量 (默认: 3)
--longitude VALUE : 设置经度 (WGS84)
--latitude VALUE  : 设置纬度 (WGS84)
--height VALUE    : 设置高度 (米)
--verbose, -v     : 显示详细输出

示例:
model2tiles.exe model.fbx output --longitude 116.3912757 --latitude 39.906217 --height 50 --verbose
