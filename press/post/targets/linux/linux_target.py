import logging
import os

from press.helpers import deployment
from press.post.targets import Target
from press.post.targets.linux import util

log = logging.getLogger(__name__)


class LinuxTarget(Target):
    name = 'Linux'

    __default_user_home = '/home'  # /home/USER
    __default_root_home = '/'      # /USER, ie. /root

    required_files = [
    ]

    def set_language(self, language):
        _locale = 'LANG=%s\nLC_MESSAGES=C\n' % language
        deployment.write(self.join_root('/etc/locale.conf'), _locale)

    def set_timezone(self, timezone):
        localtime_path = self.join_root('/etc/localtime')
        deployment.remove_file(localtime_path)
        zone_info = os.path.join('../usr/share/zoneinfo/', timezone)
        deployment.create_symlink(zone_info, localtime_path)

    def localization(self):
        configuration = self.press_configuration.get('localization', dict())

        language = configuration.get('language')
        if language:
            log.info('Setting LANG=%s' % language)
            self.set_language(language)

        timezone = configuration.get('timezone')
        if timezone:
            log.info('Setting localtime: %s' % timezone)

    def __groupadd(self, group, gid=None, system=False):
        if not util.group_exists(group, self.root):
            log.info('Creating group %s' % group)
            self.chroot(util.format_groupadd(group, gid, system))
        else:
            log.warn('Group %s already exists' % group)

    # TODO: Authorized keys support
    def authentication(self):
        configuration = self.press_configuration.get('auth')
        if not configuration:
            log.warn('No authentication configuration found')
            return

        users = configuration.get('users')
        if not users:
            log.warn('No users have been defined')

        for user in users:
            _u = users[user]
            if user != 'root':
                # Add user groups

                if 'group' in _u:
                    self.__groupadd(_u['group'], _u.get('gid'))
                groups = _u.get('groups')
                if groups:
                    for group in groups:
                        self.__groupadd(group)

                # Add user

                if not util.user_exists(user, self.root):
                    log.info('Creating user: %s' % user)
                    self.chroot(util.format_useradd(user,
                                                    _u.get('uid'),
                                                    _u.get('group'),
                                                    _u.get('groups'),
                                                    _u.get('home'),
                                                    _u.get('shell'),
                                                    _u.get('create_home', True),
                                                    _u.get('system', False)))
                else:
                    log.warn('Defined user, %s, already exists' % user)

            # Set password

            password = _u.get('password')
            if password:
                password_options = _u.get('password_options', dict())
                is_encrypted = password_options.get('encrypted', True)
                log.info('Setting password for %s' % user)
                self.chroot(util.format_change_password(user, password, is_encrypted))
            else:
                log.warn('User %s has no password defined' % user)

        # Create system groups

        groups = configuration.get('groups')
        if groups:
            for group in groups:
                _g = groups[group] or dict()  # a group with no options will be null
                self.__groupadd(group, _g.get('gid'), _g.get('system'))

    def run(self):
        self.localization()
        self.authentication()
