# System API Ansible Roles

_WARNING: This API is not yet stable. Testing of this API should happen on non-production systems._

A collection of modules and supporting roles to configure common system subsystems utilizing the subsystems APIs whenever possible rather than common CLI tools.  This should allow improved performance, error handling, and consistency across future releases.

## Roles as System API

The System API is a generic way to configure a system according to formally defined API.
Various roles contribute toward the implementation of that API. The API is formally
described in the ```api/``` directory and an ```example-system-api.yml``` playbook example
that calls it.

### Current subsystems
- Networking
- Red Hat Subscription Manager
- SELinux
- Timesync

### Vagrant

You can use [vagrant](http://vagrantup.com) to quickly test roles in this repository. The Vagrantfile in this repository defines [multiple machines](https://www.vagrantup.com/docs/multi-machine/) (for now `fedora` and `centos`) and runs all `vagrant` commands on all of them by default. To run the example playbook on one machine, use

```shell
vagrant up MACHINE
```

Use `vagrant provision` to run the example playbook against an already-running machine.

## Specific non-API roles

### Subscriptions

This is an example playbook using the redhat_subscription Ansible Core module (Preview status). This will register a guest, attach the entitlement, and enable the common server channels to install packages.  Note:  This calls `verify_supported_platform` to fail if not RHEL 6.4 or later in order to meet the scope of this Proof of Concept project.  It does all this using an intermediary role called `common_RHSM` to simplify the process and auto-define appropriate repository channels based on the major release.  This will most certainly be refined and possibly renamed or merged into something else.

If using the optional Red Hat Subscription Manager example role, you will probably want to securely store your credentials in an encrypted [ansible vault](http://docs.ansible.com/ansible/playbooks_vault.html) file.  Currently this is the only role/module for this project that requires sensitive information.  It will need to include the following:

* rhn_username: your RHN user account
* rhn_password: your RHN password
* POOL_ID: your paid entitlement Pool ID to access content from Red Hat Subscription Manager


### Supported Platform Check
This role can be used by other roles using the `include_role` directive to help ensure that the minimum supported platform requirements are met.  It is really nothing more than a predefined set of conditional tasks.

### Networking
This module and role has not yet been merged into this repository and can instead be found at <https://github.com/NetworkManager/ansible-network-role>.

### Email: postfix
This role is explained in this [roles/postfix/README.md](https://github.com/cockpit-project/poc-sysmgmt-roles/blob/master/roles/postfix/README.md) which includes an example playbook.

### SELinux
This role is explained in [roles/selinux/README.adoc](roles/selinux/README.adoc) and demonstrated in [selinux-playbook.yml](roles/selinux/selinux-playbook.yml) playbook.

### Storage
Example playbook [roles/storage/example-playbook.yml](https://github.com/cockpit-project/poc-sysmgmt-roles/blob/master/roles/storage/example-playbook.yml) is provided which demonstrates basic storage configuration using the existing roles & modules already provided by Ansible.

This will provision LVM, filesystem, mount and user ownership of disks.  Modules used include:

- user
- lvg
- lvol
- filesystem
- file
- mount

### Timesync
This role is explained in this [roles/timesync/README.md](https://github.com/cockpit-project/poc-sysmgmt-roles/blob/master/roles/timesync/README.md) which includes example playbooks.

## Licenses
Ansible roles that are included in this project are individually licensed. Licensing information can be found in each role's `README.md`, under **License**.

Tests are licensed under GPLv3. See `test/COPYING`.
