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
# System libraries.
from wtforms import Form, BooleanField, TextField, validators, PasswordField, ValidationError, RadioField, SelectField

import cgi
import jinja2
import logging
import os
import urllib2
import wtforms.validators

# Local libraries.
import base
import event_db
import site_db
import site_util
import cache

from datetime import datetime
import settings

from google.appengine.ext import db
import organization
import primary_contact_db
import random_password

jinja_environment = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
template = jinja_environment.get_template('admin_edit_contact.html')
#CASE_LABELS = settings.CASE_LABELS
#COUNT = 26
GLOBAL_ADMIN_NAME = "Admin"
ten_minutes = 600

class AdminHandler(base.AuthenticatedHandler):
    def AuthenticatedGet(self, org, event):
        global_admin = False
        local_admin = False
        if org.name == GLOBAL_ADMIN_NAME:
            global_admin = True
        if org.is_admin == True and global_admin == False:
            local_admin = True
        
        if global_admin == False and local_admin == False:
            self.redirect("/")
            return
            
        if self.request.get("contact"):
            try:
                id = int(self.request.get("contact"))
            except:
                pass
            
            organization_list = None
            contact = primary_contact_db.Contact.get_by_id(id)
            if global_admin:
                query_string = "SELECT * FROM Organization"
                organization_list = db.GqlQuery(query_string)
            if local_admin:
                if not contact.organization.incident.key() == org.incident.key():
                    self.redirect("/admin")
                    return
                organization_list = []
                query_string = "SELECT * FROM Organization"
                org_list = db.GqlQuery(query_string)
                for o in org_list:
                    if o.incident.key() == org.incident.key():
                        organization_list.append(o)

            form = primary_contact_db.ContactFormFull(first_name = contact.first_name, last_name=contact.last_name, phone = contact.phone, email = contact.email, is_primary=int(contact.is_primary))
            organization_name = None
            if contact.organization:
                organization_name = contact.organization.name
            self.response.out.write(template.render(
            {
                "organization_list": organization_list,
                "edit_contact_id": id,
                "form": form,
                "organization_name": organization_name,
                "global_admin": global_admin,
            }))
            return
