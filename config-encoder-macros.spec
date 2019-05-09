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

%global sha 624ed05b65743a82bcfdef525176e6cfef5c71ee

Name:           config-encoder-macros
Version:        master.624ed05
Release:        1%{?dist}
Summary:        Helper macros for encoding config files
License:        MIT
URL:            https://github.com/picotrading/config-encoder-macros
Source0:        https://github.com/picotrading/%{name}/archive/%{sha}.zip
Vendor:         Jiri Tyr
BuildArch:      noarch

%define PKG_BASE_DIR /opt/config-encoder-macros

%description
Set of Jinja2 and ERB macros which help to encode Python and Ruby data structure into a different file format

%prep
%autosetup -n %{name}-%{sha} -p 1

%build

%install
mkdir -p %{buildroot}/%{PKG_BASE_DIR}
cp -r * %{buildroot}/%{PKG_BASE_DIR}/

%files
%license LICENSE.md
%defattr(0755,root,root)
%{PKG_BASE_DIR}

%clean
rm -rf %{buildroot}
