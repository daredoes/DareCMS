from darecms.common import *


class MenuItem:
    access = None   # list of permission levels allowed to display this menu
    href = None     # link to render
    submenu = None  # submenu to show
    name = None     # name of Menu item to show

    def __init__(self, href=None, access=None, submenu=None, name=None):
        assert submenu or href, "menu items must contain ONE nonempty: href or submenu"
        assert not submenu or not href, "menu items must not contain both a href and submenu"

        if submenu:
            self.submenu = listify(submenu)
        else:
            self.href = href

        self.name = name
        self.access = access

    def append_menu_item(self, m):
        """
        If we're appending a new menu item, and we aren't a submenu, convert us to one now.
        Create a new submenu and append a new item to it with the same name and href as us.

        Example:
            Original menu:
                (name='Rectangles', href="rectangle.html')

            Append to it a new menu item:
                [name='Squares', href='square.html']

            New result is:
                (name='Rectangles', submenu=
                    [
                        (Name='Rectangles', href="rectangle.html"),
                        (Name='Squares', href="square.html")
                    ]
                )
        """
        if not self.submenu and self.href:
            self.submenu = [MenuItem(name=self.name, href=self.href)]
            self.href = None

        self.submenu.append(m)

    def render_items_filtered_by_current_access(self):
        """
        Returns: dict of menu items which are allowed to be seen by the logged in user's access levels
        """
        out = {}

        if self.access and set(listify(self.access)).isdisjoint(sa.AdminAccount.access_set()):
            return None

        out['name'] = self.name
        if self.submenu:
            out['submenu'] = []
            for menu_item in self.submenu:
                filtered_menu_items = menu_item.render_items_filtered_by_current_access()
                if filtered_menu_items:
                    out['submenu'].append(filtered_menu_items)
        else:
            out['href'] = self.href

        return out

    def __getitem__(self, key):
        for sm in self.submenu:
            if sm.name == key:
                return sm


c.MENU = MenuItem(name='Root', submenu=[
    MenuItem(name='Users', access=[c.ACCOUNTS], submenu=[
        MenuItem(name='Add New', href='{{ c.PATH }}/accounts/form'),
        MenuItem(name='All', href='{{ c.PATH }}/accounts/all'),
        MenuItem(name='Admins', href='{{ c.PATH }}/accounts/'),
    ]),
    MenuItem(name='{{ c.CURRENT_ADMIN.first_name }} {{ c.CURRENT_ADMIN.last_name }}', access=[c.ACCOUNTS], submenu=[
        MenuItem(name='Change Password', href='{{ c.PATH }}/accounts/change_password'),
        MenuItem(name='Edit Info', href='{{ c.PATH }}/accounts/form?id={{ c.CURRENT_ADMIN.id }}')
    ]),
    MenuItem(name='{{ "Logout" if c.CURRENT_ADMIN else "Login" }}',
             href='{{ c.PATH + "/accounts/logout" if c.CURRENT_ADMIN else c.PATH + "/accounts/login" }}'),
    MenuItem(name="Sitemap", href="{{ c.PATH }}/accounts/sitemap")
])
