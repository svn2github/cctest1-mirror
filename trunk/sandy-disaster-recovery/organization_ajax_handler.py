#!/usr/bin/env python
#
# Copyright 2012 Andy Gimma
#
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
#

from wtforms import Form, BooleanField, TextField, validators, PasswordField, ValidationError, RadioField, SelectField

# System libraries.
import cgi
import jinja2
import logging
import os
import urllib2
import wtforms.validators
import cache
from collections import OrderedDict

# Local libraries.
import base
import event_db
import site_db
import site_util
import event_db
import json
import organization
jinja_environment = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class OrganizationAjaxHandler(base.RequestHandler):
    def get(self):
        data = {}
        event = None
        for e in event_db.Event.gql("Where name = :1", self.request.get("event_name")):
            event = e
        for org in organization.Organization.gql(
            'Where incident = :1 and is_active = :2 ORDER BY name', event.key(), True):
            data[org.name] = org.name
            
        d_sorted_by_value = OrderedDict(sorted(data.items(), key=lambda x: x[1]))
        
        self.response.out.write(json.dumps(d_sorted_by_value))
 