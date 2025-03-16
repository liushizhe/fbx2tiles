#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FBX to 3D Tiles Converter
This script converts FBX 3D models to 3D Tiles format for use in 3D mapping applications.
It uses a two-step process:
1. Convert FBX to glTF using FBX2glTF
2. Convert glTF to 3D Tiles (B3DM) with LOD support and geographic positioning
"""

import os
import sys
import json
import math
import shutil
import struct
import base64
import argparse
import subprocess
import numpy as np
from datetime import datetime
import tempfile


class FBX2Tiles:
    """Main converter class for transforming FBX models to 3D Tiles format."""
    
    def __init__(self, input_file, output_dir, lod_levels=10, longitude=None, latitude=None, height=None, verbose=False):
        """
        Initialize the converter with input and output paths.
        
        Args:
            input_file (str): Path to input FBX file
            output_dir (str): Directory to output 3D Tiles files
            lod_levels (int): Number of LOD levels to generate
            longitude (float): Longitude in degrees (WGS84)
            latitude (float): Latitude in degrees (WGS84)
            height (float): Height in meters above ellipsoid
            verbose (bool): Whether to print verbose output
        """
        self.input_file = os.path.abspath(input_file)
        self.output_dir = os.path.abspath(output_dir)
        self.lod_levels = lod_levels
        
        # Set geographic coordinates (default to central Beijing if not provided)
        self.longitude = longitude if longitude is not None else 116.3912757
        self.latitude = latitude if latitude is not None else 39.906217
        self.height = height if height is not None else 0.0
        
        self.verbose = verbose
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Create temp directory
        self.temp_dir = os.path.join(self.output_dir, "temp")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Set paths
        self.gltf_dir = os.path.join(self.temp_dir, "model_out")
        self.gltf_path = os.path.join(self.gltf_dir, "model.gltf")
        
        # Validate input file
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        if not self.input_file.lower().endswith('.fbx'):
            raise ValueError("Input file must be an FBX file")
    
    def convert_fbx_to_gltf(self):
        """
        Convert FBX to glTF using FBX2glTF command-line tool.
        Note: FBX2glTF must be installed separately.
        """
        if self.verbose:
            print(f"Converting FBX to glTF: {self.input_file}")
        
        # Check if FBX2glTF is available
        try:
            # Try to find FBX2glTF in PATH
            fbx2gltf_path = "FBX2glTF"
            
            # Construct command
            cmd = [
                fbx2gltf_path,
                "--input", self.input_file,
                "--output", os.path.join(self.temp_dir, "model")
            ]
            
            if self.verbose:
                print(f"Running command: {' '.join(cmd)}")
            
            # Run command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error converting FBX to glTF: {result.stderr}")
                print("If FBX2glTF is not installed, please install it from: https://github.com/facebookincubator/FBX2glTF")
                print("Alternative conversion methods:")
                print("1. Use Blender to convert FBX to glTF")
                print("2. Use online converters like https://products.aspose.app/3d/conversion/fbx-to-gltf")
                return False
            
            # Check if the output file exists
            if not os.path.exists(self.gltf_path):
                print(f"Expected glTF file not found at: {self.gltf_path}")
                print(f"Checking for alternative output locations...")
                
                # Try to find the file in the temp directory
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        if file.endswith('.gltf'):
                            found_path = os.path.join(root, file)
                            print(f"Found glTF file at: {found_path}")
                            self.gltf_dir = os.path.dirname(found_path)
                            self.gltf_path = found_path
                            return True
                
                print("Could not find any generated glTF file")
                return False
            
            if self.verbose:
                print(f"Successfully converted FBX to glTF: {self.gltf_path}")
            
            return True
        except Exception as e:
            print(f"Error converting FBX to glTF: {e}")
            print("Manual conversion steps:")
            print("1. Install Blender (https://www.blender.org/)")
            print("2. Open Blender, import the FBX file (File > Import > FBX)")
            print("3. Export as glTF (File > Export > glTF 2.0)")
            print("4. Place the exported glTF file in the temp directory as 'model.gltf'")
            return False
    
    def find_binary_data(self, gltf_path):
        """Find and load binary data associated with the glTF file."""
        gltf_dir = os.path.dirname(gltf_path)
        
        # Get the binary data from the glTF file
        bin_path = os.path.join(gltf_dir, os.path.basename(gltf_path).replace('.gltf', '.bin'))
        
        if not os.path.exists(bin_path):
            print(f"Binary file not found at: {bin_path}")
            print("Searching for binary files in the directory...")
            
            # Try to find any .bin file in the directory
            bin_files = []
            for file in os.listdir(gltf_dir):
                if file.endswith('.bin'):
                    bin_files.append(os.path.join(gltf_dir, file))
            
            if bin_files:
                bin_path = bin_files[0]
                print(f"Found binary file: {bin_path}")
            else:
                # Check if the binary data is embedded in the glTF file
                with open(gltf_path, 'r') as f:
                    gltf_json = json.load(f)
                
                if 'buffers' in gltf_json and len(gltf_json['buffers']) > 0:
                    buffer = gltf_json['buffers'][0]
                    if 'uri' in buffer and buffer['uri'].startswith('data:'):
                        print("Binary data is embedded in the glTF file")
                        return None, True  # Embedded data
                
                print("No binary files found. The model may not have any geometry.")
                return None, False
        
        # Read the binary data
        with open(bin_path, 'rb') as f:
            binary_data = f.read()
        
        return binary_data, False  # External data
    
    def create_b3dm(self, gltf_path, lod_level=0):
        """
        Create a B3DM file from glTF according to the 3D Tiles specification.
        
        B3DM format: 
        [header, 28 bytes][feature table JSON][feature table binary][batch table JSON][batch table binary][glTF]
        """
        if self.verbose:
            print(f"Creating B3DM file for LOD level {lod_level}...")
        
        # Find binary data
        binary_data, is_embedded = self.find_binary_data(gltf_path)
        
        # Read the glTF file
        with open(gltf_path, 'r') as f:
            gltf_json = json.load(f)
        
        # If binary data is external, update the URI to be relative
        if binary_data and not is_embedded and 'buffers' in gltf_json and len(gltf_json['buffers']) > 0:
            gltf_json['buffers'][0]['uri'] = f"buffer_lod{lod_level}.bin"
        
        # Convert glTF JSON to bytes
        gltf_bytes = json.dumps(gltf_json).encode('utf-8')
        
        # Create empty feature table
        feature_table_json = {
            "BATCH_LENGTH": 0
        }
        feature_table_json_str = json.dumps(feature_table_json)
        # Pad to 4-byte boundary
        feature_table_json_str += ' ' * ((4 - len(feature_table_json_str) % 4) % 4)
        feature_table_json_bytes = feature_table_json_str.encode('utf-8')
        feature_table_binary = b''
        
        # Create empty batch table
        batch_table_json = {}
        batch_table_json_str = json.dumps(batch_table_json)
        # Pad to 4-byte boundary
        batch_table_json_str += ' ' * ((4 - len(batch_table_json_str) % 4) % 4)
        batch_table_json_bytes = batch_table_json_str.encode('utf-8')
        batch_table_binary = b''
        
        # If we have external binary data, we need to create a GLB
        if binary_data and not is_embedded:
            # Create a GLB header
            glb_header = struct.pack('<4sII', b'glTF', 2, len(gltf_bytes) + len(binary_data) + 28)
            
            # JSON chunk header
            json_chunk_header = struct.pack('<II', len(gltf_bytes), 0x4E4F534A)  # 'JSON' in little endian
            
            # BIN chunk header
            bin_chunk_header = struct.pack('<II', len(binary_data), 0x004E4942)  # 'BIN\0' in little endian
            
            # Combine everything into a GLB
            glb_data = glb_header + json_chunk_header + gltf_bytes + bin_chunk_header + binary_data
        else:
            # Just use the glTF data as is
            glb_data = gltf_bytes
        
        # Calculate lengths for B3DM header
        feature_table_json_byte_length = len(feature_table_json_bytes)
        feature_table_binary_byte_length = len(feature_table_binary)
        batch_table_json_byte_length = len(batch_table_json_bytes)
        batch_table_binary_byte_length = len(batch_table_binary)
        
        # Create B3DM header
        # magic (4 bytes) + version (4 bytes) + byte length (4 bytes) + 
        # feature table JSON byte length (4 bytes) + feature table binary byte length (4 bytes) +
        # batch table JSON byte length (4 bytes) + batch table binary byte length (4 bytes)
        b3dm_header = struct.pack('<4sIIIIII', 
                                b'b3dm',  # magic
                                1,  # version
                                28 + feature_table_json_byte_length + feature_table_binary_byte_length + 
                                batch_table_json_byte_length + batch_table_binary_byte_length + len(glb_data),  # total byte length
                                feature_table_json_byte_length,
                                feature_table_binary_byte_length,
                                batch_table_json_byte_length,
                                batch_table_binary_byte_length)
        
        # Combine everything into a B3DM file
        b3dm_data = b3dm_header + feature_table_json_bytes + feature_table_binary + batch_table_json_bytes + batch_table_binary + glb_data
        
        return b3dm_data, binary_data, is_embedded
    
    def create_lod_models(self):
        """
        Create multiple LOD versions of the model.
        For simplicity, we'll just use the same model for all LODs.
        In a real application, you would create simplified versions of the model.
        """
        if self.verbose:
            print(f"Creating {self.lod_levels} LOD levels...")
        
        lod_models = []
        
        # For each LOD level
        for i in range(self.lod_levels):
            # In a real application, you would create a simplified version of the model here
            # For this example, we'll just use the same model for all LODs
            lod_gltf_path = self.gltf_path
            
            # Create a B3DM file for this LOD level
            b3dm_data, binary_data, is_embedded = self.create_b3dm(lod_gltf_path, i)
            
            if not b3dm_data:
                print(f"Failed to create B3DM for LOD level {i}")
                continue
            
            lod_models.append({
                'level': i,
                'b3dm_data': b3dm_data,
                'binary_data': binary_data,
                'is_embedded': is_embedded
            })
        
        return lod_models
    
    def wgs84_to_ecef(self, lon, lat, h):
        """
        Convert WGS84 coordinates (longitude, latitude, height) to ECEF (Earth-Centered, Earth-Fixed).
        
        Args:
            lon (float): Longitude in degrees
            lat (float): Latitude in degrees
            h (float): Height above ellipsoid in meters
            
        Returns:
            tuple: (x, y, z) coordinates in ECEF
        """
        # WGS84 ellipsoid parameters
        a = 6378137.0  # semi-major axis in meters
        f = 1 / 298.257223563  # flattening
        e_squared = 2 * f - f * f  # eccentricity squared
        
        # Convert to radians
        lon_rad = math.radians(lon)
        lat_rad = math.radians(lat)
        
        # Calculate N (radius of curvature in the prime vertical)
        N = a / math.sqrt(1 - e_squared * math.sin(lat_rad) * math.sin(lat_rad))
        
        # Calculate ECEF coordinates
        x = (N + h) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + h) * math.cos(lat_rad) * math.sin(lon_rad)
        z = (N * (1 - e_squared) + h) * math.sin(lat_rad)
        
        return (x, y, z)
    
    def get_transform_matrix(self):
        """
        Calculate the transform matrix from local coordinates to ECEF.
        
        Returns:
            list: 4x4 transformation matrix as a flat array (column-major)
        """
        # Convert WGS84 to ECEF
        ecef_x, ecef_y, ecef_z = self.wgs84_to_ecef(self.longitude, self.latitude, self.height)
        
        # Convert to radians
        lon_rad = math.radians(self.longitude)
        lat_rad = math.radians(self.latitude)
        
        # Calculate local East-North-Up (ENU) basis vectors
        # East
        east_x = -math.sin(lon_rad)
        east_y = math.cos(lon_rad)
        east_z = 0
        
        # North
        north_x = -math.sin(lat_rad) * math.cos(lon_rad)
        north_y = -math.sin(lat_rad) * math.sin(lon_rad)
        north_z = math.cos(lat_rad)
        
        # Up
        up_x = math.cos(lat_rad) * math.cos(lon_rad)
        up_y = math.cos(lat_rad) * math.sin(lon_rad)
        up_z = math.sin(lat_rad)
        
        # Construct the transformation matrix (column-major)
        transform = [
            east_x, north_x, up_x, 0,
            east_y, north_y, up_y, 0,
            east_z, north_z, up_z, 0,
            ecef_x, ecef_y, ecef_z, 1
        ]
        
        return transform
    
    def calculate_bounding_volume(self, transform_matrix):
        """
        Calculate a bounding volume for the model in ECEF coordinates.
        
        Args:
            transform_matrix (list): 4x4 transformation matrix as a flat array
            
        Returns:
            dict: Bounding volume definition
        """
        # For simplicity, we'll use a fixed-size bounding box
        # In a real application, you would calculate this from the model geometry
        
        # Local model size (adjust based on your model scale)
        model_half_width = 50
        model_half_height = 50
        model_half_depth = 50
        
        # Create a bounding box in ECEF coordinates
        return {
            "box": [
                0, 0, 0,  # Center point (will be transformed)
                model_half_width, 0, 0,  # X half-axis
                0, model_half_height, 0,  # Y half-axis
                0, 0, model_half_depth  # Z half-axis
            ]
        }
    
    def create_tileset_json(self, lod_models):
        """Create a tileset.json file with LOD support and geographic positioning."""
        if self.verbose:
            print("Creating tileset.json with LOD support and geographic positioning...")
        
        # Get the transform matrix for positioning
        transform = self.get_transform_matrix()
        
        # Calculate a bounding volume
        bounding_volume = self.calculate_bounding_volume(transform)
        
        # Create the root tile
        root_tile = {
            "transform": transform,
            "boundingVolume": bounding_volume,
            "geometricError": 100,  # High error for the root
            "refine": "REPLACE",  # Use REPLACE for LOD
            "children": []
        }
        
        # Add children for each LOD level, from lowest to highest detail
        prev_tile = None
        for i, lod in enumerate(reversed(lod_models)):
            level = lod['level']
            geometric_error = 100 / (2 ** (i + 1))  # Decrease error with each level
            
            tile = {
                "boundingVolume": bounding_volume,
                "geometricError": geometric_error,
                "refine": "REPLACE",
                "content": {
                    "uri": f"tiles/model_lod{level}.b3dm"
                }
            }
            
            # If this is not the highest detail level, add children
            if prev_tile:
                tile["children"] = [prev_tile]
            
            prev_tile = tile
        
        # Add the highest detail level as the first child of the root
        if prev_tile:
            root_tile["children"].append(prev_tile)
        
        # Create the tileset JSON
        tileset = {
            "asset": {
                "version": "1.0",
                "tilesetVersion": "1.0",
                "gltfUpAxis": "Y"
            },
            "geometricError": 200,  # Higher than the root tile
            "root": root_tile
        }
        
        return tileset
    
    def convert_gltf_to_3dtiles(self):
        """Convert glTF to 3D Tiles with LOD support and geographic positioning."""
        if self.verbose:
            print(f"Converting glTF to 3D Tiles with LOD and positioning: {self.gltf_path}")
            print(f"Geographic coordinates: Lon={self.longitude}, Lat={self.latitude}, Height={self.height}")
        
        try:
            # Create tiles directory
            tiles_dir = os.path.join(self.output_dir, "tiles")
            if not os.path.exists(tiles_dir):
                os.makedirs(tiles_dir)
            
            # Create LOD models
            lod_models = self.create_lod_models()
            
            if not lod_models:
                print("Failed to create any LOD models")
                return False
            
            # Save B3DM files
            for lod in lod_models:
                level = lod['level']
                b3dm_data = lod['b3dm_data']
                binary_data = lod['binary_data']
                is_embedded = lod['is_embedded']
                
                # Save the B3DM file
                b3dm_path = os.path.join(tiles_dir, f"model_lod{level}.b3dm")
                with open(b3dm_path, 'wb') as f:
                    f.write(b3dm_data)
                
                # If we have external binary data, save it
                if binary_data and not is_embedded:
                    bin_path = os.path.join(tiles_dir, f"buffer_lod{level}.bin")
                    with open(bin_path, 'wb') as f:
                        f.write(binary_data)
            
            # Create tileset.json with geographic positioning
            tileset = self.create_tileset_json(lod_models)
            
            # Write tileset.json
            tileset_path = os.path.join(self.output_dir, "tileset.json")
            with open(tileset_path, 'w') as f:
                json.dump(tileset, f, indent=2)
            
            if self.verbose:
                print(f"Successfully created 3D Tiles with LOD and positioning in: {self.output_dir}")
            
            return True
        except Exception as e:
            print(f"Error converting glTF to 3D Tiles: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def convert(self):
        """Run the full conversion process."""
        if self.verbose:
            print(f"Starting conversion of {self.input_file} to 3D Tiles")
            print(f"Output directory: {self.output_dir}")
            print(f"Geographic coordinates: Lon={self.longitude}, Lat={self.latitude}, Height={self.height}")
        
        # Convert FBX to glTF
        if not self.convert_fbx_to_gltf():
            print("Failed to convert FBX to glTF. Please try manual conversion.")
            return False
        
        # Convert glTF to 3D Tiles
        if not self.convert_gltf_to_3dtiles():
            print("Failed to convert glTF to 3D Tiles.")
            return False
        
        # Clean up
        self.cleanup()
        
        if self.verbose:
            print("Conversion completed successfully")
            print(f"3D Tiles output is available at: {self.output_dir}")
        
        return True


def main():
    """Main function to run the converter from command line."""
    parser = argparse.ArgumentParser(description='Convert FBX models to 3D Tiles format')
    parser.add_argument('input_file', help='Path to input FBX file')
    parser.add_argument('output_dir', help='Directory to output 3D Tiles files')
    parser.add_argument('--lod-levels', type=int, default=3, help='Number of LOD levels to generate (default: 3)')
    parser.add_argument('--longitude', type=float, help='Longitude in degrees (WGS84)')
    parser.add_argument('--latitude', type=float, help='Latitude in degrees (WGS84)')
    parser.add_argument('--height', type=float, help='Height in meters above ellipsoid')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    converter = FBX2Tiles(
        args.input_file, 
        args.output_dir, 
        args.lod_levels, 
        args.longitude, 
        args.latitude, 
        args.height, 
        args.verbose
    )
    success = converter.convert()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
