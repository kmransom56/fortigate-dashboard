#!/usr/bin/env python3
"""
Visio Stencil (.vss) SVG Extractor
Attempts to extract SVG content from Microsoft Visio stencil files
"""
import os
import re
import struct
import zipfile
import tempfile
from pathlib import Path

def is_compound_document(file_path):
    """Check if file is a Microsoft Compound Document"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # Compound Document signature
            return header == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    except:
        return False

def extract_strings_from_vss(file_path, min_length=10):
    """Extract readable strings from VSS file that might contain SVG-like content"""
    print(f"🔍 Extracting strings from: {os.path.basename(file_path)}")
    
    svg_patterns = []
    xml_content = []
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Look for SVG-like patterns
        svg_pattern = re.compile(rb'<svg[^>]*>.*?</svg>', re.DOTALL | re.IGNORECASE)
        path_pattern = re.compile(rb'<path[^>]*d="[^"]*"[^>]*>', re.IGNORECASE)
        viewbox_pattern = re.compile(rb'viewBox="[^"]*"', re.IGNORECASE)
        
        # Find SVG elements
        svg_matches = svg_pattern.findall(content)
        path_matches = path_pattern.findall(content)
        viewbox_matches = viewbox_pattern.findall(content)
        
        print(f"   Found {len(svg_matches)} potential SVG elements")
        print(f"   Found {len(path_matches)} path elements")
        print(f"   Found {len(viewbox_matches)} viewBox attributes")
        
        # Extract readable strings that might be XML/SVG
        strings = re.findall(rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}', content)
        
        for string in strings:
            try:
                decoded = string.decode('utf-8', errors='ignore')
                # Look for XML/SVG-like content
                if any(keyword in decoded.lower() for keyword in ['<svg', '<path', '<g', '<rect', '<circle', 'viewbox', 'xmlns']):
                    xml_content.append(decoded)
            except:
                pass
        
        return {
            'svg_elements': [s.decode('utf-8', errors='ignore') for s in svg_matches],
            'path_elements': [s.decode('utf-8', errors='ignore') for s in path_matches],
            'viewbox_elements': [s.decode('utf-8', errors='ignore') for s in viewbox_matches],
            'xml_strings': xml_content
        }
        
    except Exception as e:
        print(f"❌ Error extracting from {file_path}: {e}")
        return None

def try_ole_extraction(file_path):
    """Try to extract content using OLE compound document structure"""
    print(f"🏢 Attempting OLE extraction from: {os.path.basename(file_path)}")
    
    try:
        # Simple approach - look for embedded objects
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Look for embedded files/streams that might contain SVG
        # OLE files have directory entries - try to find relevant streams
        ole_signature = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        
        if content.startswith(ole_signature):
            print("   ✅ Valid OLE compound document")
            
            # Look for common Visio streams/storages
            visio_streams = [
                b'VisioDocument',
                b'Pages',
                b'Page',
                b'Shapes',
                b'Masters',
                b'Master'
            ]
            
            found_streams = []
            for stream_name in visio_streams:
                if stream_name in content:
                    found_streams.append(stream_name.decode())
                    print(f"   📁 Found stream: {stream_name.decode()}")
            
            return found_streams
        else:
            print("   ❌ Not a valid OLE document")
            return None
            
    except Exception as e:
        print(f"❌ OLE extraction error: {e}")
        return None

def convert_vss_to_svg_simple(vss_file, output_dir):
    """Simple attempt to extract any SVG-like content from VSS file"""
    print(f"\n🔄 Processing: {os.path.basename(vss_file)}")
    
    if not is_compound_document(vss_file):
        print("   ❌ Not a compound document")
        return False
    
    # Extract strings and patterns
    extracted = extract_strings_from_vss(vss_file)
    if not extracted:
        return False
    
    # Try OLE extraction
    ole_info = try_ole_extraction(vss_file)
    
    base_name = Path(vss_file).stem
    success = False
    
    # Save any found SVG elements
    if extracted['svg_elements']:
        for i, svg in enumerate(extracted['svg_elements']):
            output_file = os.path.join(output_dir, f"{base_name}_svg_{i}.svg")
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(svg)
                print(f"   ✅ Saved SVG: {os.path.basename(output_file)}")
                success = True
            except Exception as e:
                print(f"   ❌ Error saving SVG {i}: {e}")
    
    # Save XML-like content for manual inspection
    if extracted['xml_strings']:
        xml_file = os.path.join(output_dir, f"{base_name}_xml_content.txt")
        try:
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(f"XML-like content extracted from {base_name}.vss\n")
                f.write("=" * 50 + "\n\n")
                for i, xml in enumerate(extracted['xml_strings'][:10]):  # Limit to first 10
                    f.write(f"Fragment {i+1}:\n")
                    f.write(xml + "\n\n")
            print(f"   📝 Saved XML content: {os.path.basename(xml_file)}")
            success = True
        except Exception as e:
            print(f"   ❌ Error saving XML content: {e}")
    
    return success

def main():
    stencil_dir = "app/static/icons/Fortinet Visio Stencil"
    output_dir = "extracted_visio_content"
    
    print("🎨 Fortinet Visio Stencil SVG Extractor")
    print("=" * 50)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Find all .vss files
    vss_files = list(Path(stencil_dir).glob("*.vss"))
    
    if not vss_files:
        print("❌ No .vss files found!")
        return
    
    print(f"🔍 Found {len(vss_files)} Visio stencil files")
    
    success_count = 0
    for vss_file in vss_files:
        if convert_vss_to_svg_simple(vss_file, output_dir):
            success_count += 1
    
    print(f"\n✅ Processing complete!")
    print(f"📊 Successfully processed {success_count}/{len(vss_files)} files")
    print(f"📁 Check output in: {output_dir}")
    
    # Note about limitations
    print("\n📌 Note:")
    print("   Visio stencil files use proprietary binary format.")
    print("   This tool extracts text content and looks for SVG-like patterns.")
    print("   For full extraction, you may need Microsoft Visio or specialized tools.")

if __name__ == "__main__":
    main()

