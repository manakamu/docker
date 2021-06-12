#!/bin/bash
cd /usr/src/redmine/;
echo 'gem "yaml_db"' >> Gemfile;
bundle update;
bundle install --without development sqlite;
RAILS_ENV=production bundle exec rake db:migrate;
RAILS_ENV=production bundle exec rake db:data:load
