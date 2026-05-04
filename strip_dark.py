import re
import glob

def strip_dark_classes(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # regex to remove dark:xxx
    new_content = re.sub(r'dark:[^\s"\'\`]+', '', content)
    
    with open(filepath, 'w') as f:
        f.write(new_content)

for f in glob.glob('frontend/*.html'):
    strip_dark_classes(f)

print("Stripped dark mode from all HTML files.")
