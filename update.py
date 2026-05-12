import os

admin_files = [
    'templates/admin/dashboard.html',
    'templates/admin/routes.html',
    'templates/admin/shipments.html',
    'templates/admin/users.html',
    'templates/admin/warehouses.html',
    'templates/admin/validate.html',
    'templates/common/blockchain.html'
]
for f in admin_files:
    if os.path.exists(f):
        c = open(f).read()
        open(f, 'w').write(c.replace("{% extends 'admin/layout.html' %}", "{% extends 'base/admin_base.html' %}"))
