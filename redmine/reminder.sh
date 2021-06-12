#!/bin/bash
cd /usr/src/redmine;
bundle exec rake redmine:send_reminders days=3 RAILS_ENV=production
