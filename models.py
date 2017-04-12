# # -*- coding: utf-8 -*-


class User():
    def __init__(self, gh_id):
        self.gh_id = gh_id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.gh_id)
