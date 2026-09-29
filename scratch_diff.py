import subprocess
diff = subprocess.check_output(['git', 'diff', 'index.html'], text=True, errors='ignore')
with open('diff_index.txt', 'w', encoding='utf-8') as f:
    f.write(diff)
print("Wrote diff_index.txt, size:", len(diff))
