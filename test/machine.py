#!/usr/bin/python2

from __future__ import absolute_import, division, print_function

import os
import subprocess
import time
import avocado
from avocado.utils import process
import yaml
import tempfile
import logging


def run(cmd, timeout=60, env=None, log_error=True):
    if isinstance(cmd, list):
        cmd = ' '.join(['"%s"' % arg for arg in cmd])

    result = process.run(cmd, verbose=False, ignore_status=True, env=env)
    if result.exit_status != 0:
        if log_error:
            logging.error(result)
        raise process.CmdError(cmd, result)

    return result.stdout


class Machine(object):
    """
    This is a generic machine class
    """
    def __init__(self, workdir, rolesdir):
        self.workdir = workdir
        self.rolesdir = rolesdir
        self.inventory_file = None

    def create_inventory_file(self, host):
        # write an ansible inventory file for this host
        self.inventory_file = os.path.join(self.workdir, 'inventory')
        with open(self.inventory_file, 'w') as f:
            f.write(host)

    def set_config(self, interface, **config):
        iface_dir = interface.replace('.', '_')
        play = {
            'hosts': 'system-api-test',
            'become': True,
            'roles': [dict(role=iface_dir, **config)]
        }

        testbook_path = os.path.join(self.rolesdir, iface_dir, 'test',
                                     'main.yml')
        if os.path.exists(testbook_path):
            play['post_tasks'] = [{
                'include': testbook_path,
                'vars': config
            }]

        playbook = [ play ]

        playbook_file = os.path.join(self.workdir, 'test.yml')
        with open(playbook_file, 'w') as f:
            f.write(yaml.dump(playbook))

        env = dict(ANSIBLE_ROLES_PATH=self.rolesdir, **os.environ)

        run(['ansible-playbook', '-vvv', '-i', self.inventory_file, playbook_file], env=env)


class Virtualhost(Machine):
    """
    This class prepares virtual machine as SUT
    """
    def __init__(self, image, workdir, rolesdir):
        super(Virtualhost, self).__init__(workdir, rolesdir)
        self.image = image
        self.qemu = None

        self.identity = os.path.join(self.workdir, 'id_rsa')
        run(['ssh-keygen', '-q', '-f', self.identity, '-N', ''])

        cloudinit_iso = self.create_cloudinit_iso()
        self.start_vm(cloudinit_iso)

        host = ('system-api-test'
                ' ansible_host=localhost'
                ' ansible_port=2222'
                ' ansible_user=admin'
                ' ansible_ssh_private_key_file="%s"'
                ' ansible_ssh_extra_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"'
                % self.identity)
        self.create_inventory_file(host)

    def create_cloudinit_iso(self):
        with open(os.path.join(self.workdir, 'meta-data'), 'w') as f:
            f.write('instance-id: nocloud\n')
            f.write('local-hostname: system-api-test\n')

        with open(os.path.join(self.workdir, 'user-data'), 'w') as f:
            f.write('#cloud-config\n')
            f.write('user: admin\n')
            f.write('password: foobar\n')
            f.write('ssh_pwauth: True\n')
            f.write('chpasswd:\n')
            f.write('  expire: False\n')
            f.write('ssh_authorized_keys:\n')
            f.write('  - ' + open(self.identity + '.pub', 'r').read())

        cloudinit_iso = os.path.join(self.workdir, 'cloud-init.iso')
        run(['genisoimage', '-input-charset', 'utf-8',
                            '-output', cloudinit_iso,
                            '-volid', 'cidata',
                            '-joliet', '-rock', '-quiet',
                            os.path.join(self.workdir, 'user-data'),
                            os.path.join(self.workdir, 'meta-data')])
        return cloudinit_iso

    def start_vm(self, cloudinit_iso):
        argv = ['qemu-system-x86_64',
                '-m', '1024',
                self.image,
                '-snapshot',
                '-cdrom', cloudinit_iso,
                '-net', 'nic,model=virtio',
                '-net', 'user,hostfwd=tcp::2222-:22',
                '-display', 'none']
        if os.access('/dev/kvm', os.W_OK):
            argv.append('-enable-kvm')

        self.qemu = subprocess.Popen(argv)

        # wait for ssh to come up
        tries = 10
        while tries > 0:
            try:
                self.execute('/bin/true', timeout=60, log_error=(tries == 1))
                break
            except process.CmdError:
                tries -= 1
                time.sleep(3)
        else:
            self.terminate()
            raise Exception('error connecting to the machine')

    def execute(self, command, timeout=None, log_error=False):
        return run(['ssh', '-o', 'IdentityFile=' + self.identity,
                           '-o', 'StrictHostKeyChecking=no',
                           '-o', 'UserKnownHostsFile=/dev/null',
                           '-o', 'PasswordAuthentication=no',
                            'admin@localhost', '-p', '2222', command],
                   timeout=timeout, log_error=log_error)

    def terminate(self):
        self.qemu.terminate()
        self.qemu.wait()


class Localhost(Machine):
    """
    This class extends Machine to be able to run tests only on localhost
    """

    def __init__(self, workdir, rolesdir):
        super(Localhost, self).__init__(workdir, rolesdir)
        host = 'system-api-test ansible_connection=local'
        self.create_inventory_file(host)

    @staticmethod
    def execute(command, timeout=None, log_error=False):
        return run(command, timeout=timeout, log_error=log_error)


class Test(avocado.Test):
    """
    Base class for integration tests.

    Subclasses must include `:avocado: enable` in their docstring.
    """

    def setUp(self):
        workdir = tempfile.mkdtemp(dir=self.workdir)
        rolesdir = os.path.join(self.basedir, '..', 'roles')
        if self.params.get('source'):
            self.setUpMux(workdir, rolesdir)
        else:
            self.setUpLocal(workdir, rolesdir)

    def tearDown(self):
        if self.params.get('source'):
            self.tearDownMux()
        else:
            self.tearDownLocal()

    def setUpMux(self, workdir, rolesdir):
        image = self.fetch_asset(self.params.get('source'))
        self.machine = Virtualhost(image, workdir=workdir, rolesdir=rolesdir)

        setup = self.params.get('setup')
        if setup:
            self.machine.execute(setup)

    def tearDownMux(self):
        self.machine.terminate()

    def setUpLocal(self, workdir, rolesdir):
        self.machine = Localhost(workdir, rolesdir)

    def tearDownLocal(self):
        pass
