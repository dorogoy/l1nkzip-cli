import os

# Keep the suite off the network. Update-check tests opt back in.
os.environ.setdefault("L1NKZIP_NO_UPDATE_CHECK", "1")
