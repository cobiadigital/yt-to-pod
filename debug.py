import os
os.system("python freeze.py")
os.system("git status")
os.system("git add -A")
os.system('git commit -m "change feedgen to podgen"' )
os.system("git push")