import os
os.system("python freeze.py")
os.system("git status")
os.system("git add -A")
os.system('git commit -m "add music and intro prompts"' )
os.system("git push")