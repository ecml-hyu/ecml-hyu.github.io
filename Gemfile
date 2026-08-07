source "https://rubygems.org"

# GitHub Pages 가 실제로 사용하는 버전 조합을 그대로 재현한다.
# 로컬 빌드: bundle install && bundle exec jekyll build
#   미리보기: bundle exec jekyll serve
gem "github-pages", group: :jekyll_plugins

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-sitemap"
end

# Windows / JRuby 용 타임존 데이터
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

gem "wdm", "~> 0.1", :platforms => [:mingw, :x64_mingw, :mswin]
