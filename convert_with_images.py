"""
Convert blog post from Markdown to DOCX with embedded images
"""
import re
import os
from pathlib import Path
import subprocess
import shutil
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_md_to_docx_with_images():
    """Convert markdown to DOCX and embed images"""
    
    print("="*60)
    print("Markdown to DOCX Converter (with Images)")
    print("="*60)
    
    # Paths
    blog_file = "blog_post.md"
    output_file = "blog_post_with_images.docx"
    temp_file = "blog_post_temp.md"
    
    # Check if blog file exists
    if not os.path.exists(blog_file):
        print(f"Error: {blog_file} not found!")
        return False
    
    print(f"\nFound {blog_file}")
    
    # Read the markdown content
    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all image references
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    images = re.findall(image_pattern, content)
    
    print(f"Found {len(images)} image(s)")
    
    # Update image paths to absolute paths
    updated_content = content
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    for alt_text, img_path in images:
        # Convert relative path to absolute
        if not os.path.isabs(img_path):
            abs_path = os.path.join(base_dir, img_path.replace('./', ''))
            abs_path = abs_path.replace('\\', '/')
            
            if os.path.exists(abs_path):
                print(f"   OK: {os.path.basename(img_path)}")
                # Replace in content
                old_ref = f'![{alt_text}]({img_path})'
                new_ref = f'![{alt_text}]({abs_path})'
                updated_content = updated_content.replace(old_ref, new_ref)
            else:
                print(f"   Warning: {img_path} not found")
    
    # Write temporary file with updated paths
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    # Check for pandoc
    pandoc_path = None
    
    # Try common locations
    locations = [
        shutil.which('pandoc'),
        r'C:\Program Files\Pandoc\pandoc.exe',
        r'C:\Users\{}\AppData\Local\Pandoc\pandoc.exe'.format(os.environ.get('USERNAME', ''))
    ]
    
    for loc in locations:
        if loc and os.path.exists(loc):
            pandoc_path = loc
            break
    
    if not pandoc_path:
        print("\nError: Pandoc not found!")
        print("Please make sure Pandoc is installed")
        return False
    
    print(f"\nUsing Pandoc: {os.path.basename(pandoc_path)}")
    
    # Run pandoc conversion
    print("\nConverting to DOCX...")
    
    try:
        cmd = [
            pandoc_path,
            temp_file,
            '-o', output_file,
            '--standalone',
            '--highlight-style=tango'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024  # KB
            print(f"\nSUCCESS!")
            print(f"\nCreated: {output_file}")
            print(f"Size: {file_size:.1f} KB")
            print(f"Location: {os.path.abspath(output_file)}")
            print(f"\nYour blog post is ready with embedded images!")
            return True
        else:
            print("\nError: Conversion failed")
            return False
            
    except Exception as e:
        print(f"\nError: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False


if __name__ == "__main__":
    success = convert_md_to_docx_with_images()
    
    if success:
        print("\n" + "="*60)
        print("DONE! Submit blog_post_with_images.docx")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("Conversion failed. See errors above.")
        print("="*60)
    
    input("\nPress Enter to exit...")
