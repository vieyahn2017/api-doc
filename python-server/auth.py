# -*- coding:utf-8 -*-

from core import context, MiddleWare

__all__ = ("CheckLogin", "CheckRights", "SetDefaultHeader", "MiddleWare")


class AuthenticationException(Exception): pass


class AuthorizationException(Exception):
    def __init__(self, msg):
        super(AuthorizationException, self).__init__(403, msg)


class RbacChecker(object):
    @staticmethod
    def get_config(path):
        rbac_config = context["rbac"]
        url_config = rbac_config.get(path)
        if url_config:
            return url_config

        for match_path in rbac_config.iterkeys():
            if path.startswith(match_path):
                return rbac_config.get(match_path)

    @staticmethod
    def login_required(handler):
        path = handler.request.path
        rights_config = RbacChecker.get_config(path)
        if rights_config:
            return rights_config.get("login_required", False)
        else:
            return False

    @staticmethod
    def acl_defintion(handler):
        path = handler.request.path
        acl_config = RbacChecker.get_config(path)
        if acl_config:
            return acl_config.get("acl", {})
        else:
            return {}

    @staticmethod
    def has_role(rolename):
        return True


def must_login(handler):
    return RbacChecker.login_required(handler)


class SetDefaultHeader(MiddleWare):
    def process_request(self, request):
        request.set_header("Server", "")
        request.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
        request.set_header("Pragma", "no-cache")
        request.set_header("Expires", "0")
        request.set_header("X-Content-Type-Options", "nosniff")


class CheckLogin(MiddleWare):
    def process_request(self, request):
        if must_login(request):
            if not self.is_login(request):
                raise AuthenticationException(403, "need.loging")

    def is_login(self, request):
        return request.get_session() != None


class CheckRights(MiddleWare):
    def process_request(self, request):
        self.check_roles(request)

    def user_check_method(self, name, handler):
        if hasattr(handler, name):
            return getattr(handler, name)
        else:
            return getattr(self, name)

    def check_roles(self, handler):
        if must_login(handler):
            http_method = handler.request.method.lower()
            acl = RbacChecker.acl_defintion(handler)
            if http_method in acl:
                rights = acl.get(http_method)
                if rights:
                    name = "check_%s_roles" % http_method
                    checkmethod = self.user_check_method(name, handler)
                    checkmethod(handler, rights)

    def default_check_acl(self, request, required_roles):
        currentuser = request.current_user
        my_roles = currentuser.roles
        if not any((role for role in my_roles if role in required_roles)):
            # username = currentuser.username
            exc_msg = "access.denied"
            raise AuthorizationException(exc_msg)

    def check_get_roles(self, request, required_roles):
        self.default_check_acl(request, required_roles)

    def check_post_roles(self, request, required_roles):
        self.default_check_acl(request, required_roles)

    def check_put_roles(self, request, required_roles):
        self.default_check_acl(request, required_roles)

    def check_delete_roles(self, request, required_roles):
        self.default_check_acl(request, required_roles)
