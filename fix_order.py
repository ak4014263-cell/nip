import os
import re

frontend_dir = r"c:\Users\hp\Downloads\IOP\WTJ\frontend\src\pages\candidate"

for file in os.listdir(frontend_dir):
    if file.endswith(".tsx"):
        path = os.path.join(frontend_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find the line with API_BASE
        api_base_match = re.search(r'(const API_BASE = .*?\n)', content)
        if api_base_match:
            api_base_str = api_base_match.group(1)
            # Remove it from current location
            content = content.replace(api_base_str, '')
            # Insert it right after the imports
            # Find the last import
            imports = list(re.finditer(r'^import .*?\n', content, re.MULTILINE))
            if imports:
                last_import = imports[-1]
                insert_pos = last_import.end()
                content = content[:insert_pos] + "\n" + api_base_str + content[insert_pos:]
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed order in {file}")

