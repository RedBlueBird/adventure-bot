import sys
print("Python version")
print (sys.version)
print("Version info.")
print (sys.version_info)

import pkg_resources
installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
   for i in installed_packages])
print(installed_packages_list)