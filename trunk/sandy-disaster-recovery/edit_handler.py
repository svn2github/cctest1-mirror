#!/usr/bin/env python
#
# Copyright 2012 Jeremy Pack
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
import jinja2
import logging
import os
from google.appengine.ext import db
import json
import wtforms.validators

# Local libraries.
import base
import site_db
import site_util
import form_db

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
template = jinja_environment.get_template('form.html')
single_site_template = jinja_environment.get_template('single_site_incident_form.html')
logout_template = jinja_environment.get_template('logout.html')
HATTIESBURG_SHORT_NAME = "hattiesburg"
GEORGIA_SHORT_NAME = "gordon-barto-tornado"

class EditHandler(base.AuthenticatedHandler):
  def AuthenticatedGet(self, org, event):
    #single_site_template = jinja_environment.get_template('single_site.html')
    #if event.short_name in [HATTIESBURG_SHORT_NAME, GEORGIA_SHORT_NAME]:
      #single_site_template = jinja_environment.get_template('single_site_derechos.html')

    # lookup by id or case_number
    id = self.request.get('id', None)
    case_number = self.request.get('case', None)
    if not id and case_number:
        q = db.GqlQuery("SELECT * FROM Site WHERE case_number=:1", case_number)
        if q.count() == 1:
            id = q[0].key().id()

    # if no id, 404
    if id is None:
      self.response.set_status(404)
      return

    # load site
    site = site_db.GetAndCache(int(id))
    if not site:
      self.response.set_status(404)
      return
      
    if not site.event.key() == event.key():
        self.redirect("/sites?message=The site you are trying to edit doesn't belong to the event you are signed in to. If you think you are seeing this message in error, contact your administrator")
        return
    #form = site_db.SiteForm(self.request.POST, site)
    #if event.short_name in [HATTIESBURG_SHORT_NAME, GEORGIA_SHORT_NAME]:
      #form = site_db.DerechosSiteForm(self.request.POST, site)
    post_json2 = site_db.SiteToDict(site)
    date_string = str(post_json2['request_date'])
    post_json2['request_date'] = date_string
    post_json2['event'] = site.event.name
    #post_json = {
      #"city": str(site.city),
      #"name": str(site.name),
      #"reported_by": str(site.reported_by.name),
    #}
    post_json = json.dumps(post_json2)
    
    
    q = db.Query(form_db.IncidentForm)
    q.filter("incident =", event.key())
    query = q.get()

    # set it as form_stub
    # send to single site

    inc_form = None
    form=None
    if query:
      inc_form = query.form_html
    single_site = single_site_template.render(
        { "form": form,
          "org": org,
	  "incident_form_block": inc_form,
          })
    #raise Exception(query.form_html)
    self.response.out.write(template.render(
          {"mode_js": self.request.get("mode") == "js",
           "logout" : logout_template.render({"org": org, "event": event}),
           "single_site": single_site,
           "form": form,
           "id": id,
	   "post_json": post_json	,
           "page": "/edit"}))

  def AuthenticatedPost(self, org, event):
    #if event.short_name in [HATTIESBURG_SHORT_NAME, GEORGIA_SHORT_NAME]:
      #single_site_template = jinja_environment.get_template('single_site_derechos.html')
    try:
      id = int(self.request.get('_id'))
    except:
      return
    site = site_db.Site.get_by_id(id)
    data = site_db.StandardSiteForm(self.request.POST, site)
    #if event.short_name in [HATTIESBURG_SHORT_NAME, GEORGIA_SHORT_NAME]:
        #form = site_db.DerechosSiteForm(self.request.POST, site)

    # un-escaping data caused by base.py = self.request.POST[i] = cgi.escape(self.request.POST[i])
    data.name.data = site_util.unescape(data.name.data)
    data.priority.data = int(data.priority.data)
    data.name.validators = data.name.validators + [wtforms.validators.Length(min = 1, max = 100,
                             message = "Name must be between 1 and 100 characters")]
    data.phone1.validators = data.phone1.validators + [wtforms.validators.Length(
        min = 1, max = 100,
        message = "Please enter a primary phone number")]
    data.city.validators = data.city.validators + [wtforms.validators.Length(
        min = 1, max = 100,
        message = "Please enter a city name")]
    data.state.validators = data.state.validators + [wtforms.validators.Length(
        min = 1, max = 100,
        message = "Please enter a state name")]
    data.work_type.validators = data.work_type.validators + [wtforms.validators.Length(
        min = 1, max = 100,
        message = "Please set a primary work type")]


    case_number = site.case_number
    claim_for_org = self.request.get("claim_for_org") == "y"

    mode_js = self.request.get("mode") == "js"
    if data.validate():
      # Save the data, and redirect to the view page
      for f in data:
        # In order to avoid overriding fields that didn't appear
        # in this form, we have to only set those that were explicitly
        # set in the post request.
        in_post = self.request.get(f.name, default_value = None)
        if not in_post:
          continue
        setattr(site, f.name, f.data)
      if claim_for_org:
        site.claimed_by = org
      # clear assigned_to if status is unassigned
      if data.status.data == 'Open, unassigned':
        site.assigned_to = ''
        
        
      for k, v in self.request.POST.iteritems():
	if k not in site_db.STANDARD_SITE_PROPERTIES_LIST:
	  setattr(site, k, v)
      site_db.PutAndCache(site)
      if mode_js:
        # returning a 200 is sufficient here.
        return
      else:
        self.redirect('/map?id=%d' % id)
    else:
      q = db.Query(form_db.IncidentForm)
      q.filter("incident =", event.key())
      query = q.get()

      # set it as form_stub
      # send to single site

      inc_form = None
      form=None
      if query:
	inc_form = query.form_html
	
      post_json2 = site_db.SiteToDict(site)
      date_string = str(post_json2['request_date'])
      post_json2['request_date'] = date_string
      post_json2['event'] = site.event.name
      #post_json = {
	#"city": str(site.city),
	#"name": str(site.name),
	#"reported_by": str(site.reported_by.name),
      #}
      post_json = json.dumps(post_json2)
      single_site = single_site_template.render(
          { "form": data,
            "org": org,
	    "incident_form_block": inc_form,
	  })
      if mode_js:
        self.response.set_status(400)
      self.response.out.write(template.render(
          {"mode_js": mode_js,
           "logout" : logout_template.render({"org": org, "event": event}),
           "errors": data.errors,
           "form": data,
           "single_site": single_site,
           "id": id,
	   "post_json": post_json,
           "page": "/edit"}))
