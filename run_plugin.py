from pathlib import Path
import sys

import pymolfold

# Add package root to Python path
PACKAGE_ROOT = Path(__file__).parent
if str(PACKAGE_ROOT) not in sys.path:
    # 我去，这里必须append，如果用windows测试的话这个会覆盖torch中调用的pdb模块
    # 因为pymol本身也有一个pdb文件，因此可能会出现attempted relative import with no known parent package
    sys.path.append(str(PACKAGE_ROOT))

# Initialize plugin
pymolfold.plugin.__init_plugin__()