# Copyright 2019 Nokia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

Name:           access-management
Version:        %{_version}
Release:        1%{?dist}
Summary:        Access Management
License:        %{_platform_license}

Vendor:         %{_platform_vendor}
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python-flask, python2-flask-restful, python2-configparser, mod_wsgi, python2-peewee
BuildRequires:  python python-setuptools

%description
This RPM contains Access Management component for Akraino REC blueprint

%prep
%autosetup

%install
mkdir -p %{buildroot}%{_python_site_packages_path}/access_management
mkdir -p %{buildroot}/var/log/access_management

mkdir -p %{buildroot}%{_python_site_packages_path}/yarf/handlers/am
rsync -ra src/access_management/rest-plugin/* %{buildroot}/%{_python_site_packages_path}/yarf/handlers/am

mkdir -p %{buildroot}/etc/required-secrets/
cp secrets/am-secrets.yaml %{buildroot}/etc/required-secrets/am-secrets.yaml

mkdir -p %{buildroot}%{_unitdir}/
cp systemd/auth-server.service %{buildroot}%{_unitdir}/

cd src && python setup.py install --root %{buildroot} --no-compile --install-purelib %{_python_site_packages_path} --install-scripts %{_platform_bin_path} && cd -


%files
%defattr(0755,root,root)
%{_python_site_packages_path}/access_management*
%{_python_site_packages_path}/yarf/handlers/am/*
/etc/required-secrets/am-secrets.yaml
%dir %attr(0770, access-manager,access-manager) /var/log/access_management
%attr(0755,root, root) %{_platform_bin_path}/auth-server
%attr(0644,root, root) %{_unitdir}/auth-server.service

%pre
/usr/bin/getent passwd access-manager > /dev/null||/usr/sbin/useradd -r access-manager


%post
if [ $1 -eq 2 ]; then
    if [ -f %{{aaa_backend_config_path}} ]; then
        sudo /usr/bin/systemctl restart auth-server
    fi
fi


%preun


%postun
if [ $1 -eq 0 ]; then
    rm -rf /opt/access_management
    /usr/sbin/userdel access-manager
fi

%clean
rm -rf %{buildroot}
