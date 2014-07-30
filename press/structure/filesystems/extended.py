from press.cli import run
from press.structure.filesystems import FileSystem
from press.structure.exceptions import FileSystemCreateException

import logging

log = logging.getLogger(__name__)


class EXT(FileSystem):
    fs_type = ''
    _default_command_path = ''

    def __init__(self, fs_label=None, superuser_reserve=.03, stride_size=0, stripe_width=0,
                 command_path='', mount_options=None):

        super(EXT, self).__init__(fs_label, mount_options)

        self.superuser_reserve = superuser_reserve
        self.stride_size = stride_size
        self.stripe_width = stripe_width

        self.command_path = command_path or self._default_command_path

        self.full_command = \
            '{command_path} -U{uuid} -m{superuser_reserve} {extended_options}{label_options} {device}'

        # algorithm for calculating stripe-width: stride * N where N are member disks that are not used
        # as parity disks or hot spares
        self.extended_options = ''
        if self.stripe_width and self.stride_size:
            self.extended_options = ' -E stride=%s,stripe_width=%s' % (self.stride_size, self.stripe_width)

        self.label_options = ''
        if self.fs_label:
            self.label_options = ' -L %s' % self.fs_label

    def create(self, device):
        command = self.full_command.format(
            **dict(
                command_path=self.command_path,
                superuser_reserve=self.superuser_reserve,
                extended_options=self.extended_options,
                label_options=self.label_options,
                device=device,
                uuid=self.fs_uuid
            )
        )
        log.info("Creating filesystem: %s" % command)
        result = run(command)

        if result.returncode:
            raise FileSystemCreateException(self.fs_label, command, result)


class EXT3(EXT):
    fs_type = 'ext3'
    _default_command_path = '/usr/bin/mkfs.ext3'


class EXT4(EXT):
    fs_type = 'ext4'
    _default_command_path = '/usr/bin/mkfs.ext4'

