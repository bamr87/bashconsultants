# ==============================================================================
# BASH Consultants - Docker-First Jekyll Development
# ==============================================================================
#
# Based on zer0-mistakes theme Docker architecture
#
# Usage:
#   docker build -t bashconsultants .
#   docker run -d -p 4042:4042 -v $(pwd):/site --name bashconsultants bashconsultants
#   docker exec -it bashconsultants /bin/bash
#
# Multi-stage build:
#   - base: Ruby 3.3 slim + minimal build deps
#   - dev: Development tools + test gems
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Base - Ruby 3.3 with minimal build dependencies
# ------------------------------------------------------------------------------
FROM ruby:3.3-slim AS base

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libyaml-dev \
        zlib1g-dev \
        git && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /site

RUN gem install bundler -v '~> 2.3'

# Copy dependency files first for better caching
COPY Gemfile Gemfile.lock* ./

RUN bundle config set --local deployment false && \
    bundle config set --local without '' && \
    bundle install --jobs 4 --retry 3

# ------------------------------------------------------------------------------
# Stage 2: Development & Test
# ------------------------------------------------------------------------------
FROM base AS dev

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        curl \
        jq && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN bundle config set --local with 'development test' && \
    bundle install --jobs 4 --retry 3

COPY . .

EXPOSE 4042
CMD ["bundle", "exec", "jekyll", "serve", "--config", "_config.yml,_config_dev.yml", "--host", "0.0.0.0", "--port", "4042", "--watch", "--force_polling"]