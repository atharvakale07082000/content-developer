import re

def strip_dark(content):
    return re.sub(r'dark:[^\s"\'\`]+', '', content)

def get_body_content(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    # Extract everything inside <body>...</body>
    match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
    if match:
        return strip_dark(match.group(1))
    return ""

def build():
    # Base layout from lumina_new_analysis_input
    with open('stitch_assets/lumina_new_analysis_input/code.html', 'r') as f:
        base_html = f.read()
    
    base_html = strip_dark(base_html)

    # We need to take the Sidebar, TopNavBar from the base html,
    # and then create a <main> that holds three state divs.

    # Actually, the base HTML already has a <main> tag. Let's find it.
    
    input_main = get_body_content('stitch_assets/lumina_new_analysis_input/code.html')
    thinking_main = get_body_content('stitch_assets/lumina_processing_query/code.html')
    results_main = get_body_content('stitch_assets/lumina_dashboard/code.html')

    # Since they all have different Sidebars/Topbars (some differ slightly), we'll keep the sidebar & topbar from the results_main as the base, because it has all the links.
    
    # Let's just create a completely clean dashboard.html 
    
    with open('stitch_assets/lumina_dashboard/code.html', 'r') as f:
        results_raw = strip_dark(f.read())
        
    # We will inject the other two views into the <main> element of results_raw.
    # Replace the <main> ... </main> with a wrapper containing all three views. 
    # Wait, the best way to do this is to just write a script that does it using regex or just I'll do it manually.
    pass

build()
