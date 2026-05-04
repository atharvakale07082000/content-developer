import re

def process_file(src, dst):
    with open(src, 'r') as f:
        content = f.read()
    
    # Remove all dark mode classes (like dark:bg-zinc-900, dark:hover:text-white)
    content = re.sub(r'dark:[^\s"\'\`]+', '', content)
    
    with open(dst, 'w') as f:
        f.write(content)

process_file('stitch_assets/lumina_landing_page/code.html', 'frontend/index.html')
process_file('stitch_assets/lumina_login_1/code.html', 'frontend/login.html')
process_file('stitch_assets/lumina_register/code.html', 'frontend/register.html')
process_file('stitch_assets/lumina_history/code.html', 'frontend/history.html')

print("Processed static pages successfully.")
