"""
Perm settings for lucks stuff
*** DO NOT TOUCH ***
"""

import os


chmod = {
    "-R /mnt/drive1": 777,
    "/mnt/drive1": 700,
    "-R /mnt/drive1/Fate": 700,
    "-R /mnt/drive1/Fate/data": 700,
    "-R /home/luck": 700,
    "-R /mnt/drive1/Trident": 700,
    "-R /mnt/drive1/HSMP": 700,
    "-R /mnt/drive3/luck": 700
}

chown = {
    "-R /mnt/drive1": "luck",
    "-R /mnt/drive1/Trident": "neptune",
    "-R /mnt/drive1/Karp": "ash",
    "-R /home/luck": "luck",
    "-R /mnt/drive3/luck": "luck"
}

chgrp = {
    "-R /mnt/drive1": "luck",
    "-R /mnt/drive1/Trident": "neptune",
    "-R /mnt/drive3/luck": "luck",
    "-R /home/luck": "luck"
}


def process(root, change):
    msg = f"Set {root.lstrip('-R ')} to {change}"
    if "-R" in root:
        msg += " recursively"
    print(msg)


for root, perm_level in chmod.items():
    os.system(f"chmod {perm_level} {root}")
    process(root, perm_level)

for root, user in chown.items():
    os.system(f"chown {user} {root}")
    process(root, user)

for root, group in chgrp.items():
    os.system(f"chgrp {group} {root}")
    process(root, group)
