---
title: Search
description: Search BASH Consulting's services, case studies, and articles on cloud, ERP, and accounting systems for Denver small and medium businesses
author: Amr Abdel-Motaleb
layout: default
slug: search
permalink: /search/
lastmod: 2026-07-06T12:00:00.000Z
draft: false
sitemap: true
keywords:
  - site search
  - BASH Consulting services
  - Denver IT consulting
  - ERP consulting articles
  - cloud migration case studies
---

## Find a service, case study, or article

Type what you're looking for — a system name like QuickBooks or QAD, a problem like "month-end close", or a service area like cloud migration. Results come from every published page on this site.

<form class="d-flex gap-2 my-4" role="search" action="/search/" method="get" data-page-search-form>
  <label class="visually-hidden" for="page-search-input">Search this site</label>
  <input id="page-search-input" class="form-control form-control-lg" type="search" name="q"
         placeholder="Search services, case studies, and articles…" autocomplete="off" data-page-search-input>
  <button class="btn btn-primary btn-lg" type="submit">Search</button>
</form>

<div id="page-search-results" class="mb-4" data-page-search-results>
  <p class="text-muted" data-page-search-status>Enter a search term above, or press <kbd>/</kbd> anywhere on the site for quick search.</p>
</div>

<script>
(function () { 'use strict'; // Consumes the same /search.json index as the theme's search modal // (assets/js/search-modal.js) and the ?q= handoff from 404.html. var form = document.querySelector('[data-page-search-form]'); var input = document.querySelector('[data-page-search-input]'); var resultsBox = document.querySelector('[data-page-search-results]'); var status = document.querySelector('[data-page-search-status]');
  if (!form || !input || !resultsBox) return;

var index = null; var indexPromise = null; var indexAvailable = true;

  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!indexPromise) {
      indexPromise = fetch('/search.json')
        .then(function (response) {
          if (!response.ok) { indexAvailable = false; return []; }
          return response.json();
        })
        .then(function (data) {
          index = Array.isArray(data) ? data : [];
          return index;
        })
        .catch(function () { indexAvailable = false; return []; });
    }
    return indexPromise;
  }

  function escapeHtml(value) {
    var div = document.createElement('div');
    div.textContent = String(value == null ? '' : value);
    return div.innerHTML;
  }

  function highlight(text, query) {
    var escaped = escapeHtml(text);
    if (!query) return escaped;
    var safe = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return escaped.replace(new RegExp('(' + safe + ')', 'ig'), '<mark>$1</mark>');
  }

  function snippet(item, query) {
    var source = item.content || item.description || '';
    var lower = source.toLowerCase();
    var at = lower.indexOf(query.toLowerCase());
    if (at === -1) {
      source = item.description || item.content || '';
      return source.length > 160 ? source.slice(0, 160) + '…' : source;
    }
    var start = Math.max(0, at - 70);
    var end = Math.min(source.length, at + 110);
    return (start > 0 ? '… ' : '') + source.slice(start, end) + (end < source.length ? ' …' : '');
  }

  function score(item, query) {
    var title = (item.title || '').toLowerCase();
    var description = (item.description || '').toLowerCase();
    var content = (item.content || '').toLowerCase();
    var tags = (item.tags || []).join(' ').toLowerCase();
    var categories = (item.categories || []).join(' ').toLowerCase();
    if (title.indexOf(query) !== -1) return 3;
    if (description.indexOf(query) !== -1 || tags.indexOf(query) !== -1 || categories.indexOf(query) !== -1) return 2;
    if (content.indexOf(query) !== -1) return 1;
    return 0;
  }

  function labelFor(item) {
    var url = item.url || '';
    if (url.indexOf('/services/') === 0) return 'Service';
    if (url.indexOf('/case-studies/') === 0) return 'Case study';
    if (item.collection === 'posts') return 'Article';
    return 'Page';
  }

  function render(matches, query) {
    resultsBox.innerHTML = '';
    var summary = document.createElement('p');
    summary.className = 'text-muted';
    if (!indexAvailable) {
      summary.textContent = 'Search is unavailable right now. Try the links in the site navigation instead.';
      resultsBox.appendChild(summary);
      return;
    }
    summary.textContent = matches.length
      ? matches.length + ' result' + (matches.length === 1 ? '' : 's') + ' for “' + query + '”'
      : 'No results for “' + query + '”. Try a shorter term, or browse the services overview below.';
    resultsBox.appendChild(summary);

    if (!matches.length) {
      var fallback = document.createElement('p');
      fallback.innerHTML = '<a href="/services/">Browse all services</a> or <a href="/contact/">tell us what you’re looking for</a>.';
      resultsBox.appendChild(fallback);
      return;
    }

    var list = document.createElement('div');
    list.className = 'list-group';
    matches.slice(0, 20).forEach(function (item) {
      var link = document.createElement('a');
      link.className = 'list-group-item list-group-item-action py-3';
      link.href = item.url;

      var heading = document.createElement('div');
      heading.className = 'd-flex justify-content-between align-items-start gap-2';
      var title = document.createElement('span');
      title.className = 'fw-semibold';
      title.innerHTML = highlight(item.title || 'Untitled', query);
      var badge = document.createElement('span');
      badge.className = 'badge text-bg-secondary flex-shrink-0';
      badge.textContent = labelFor(item);
      heading.appendChild(title);
      heading.appendChild(badge);
      link.appendChild(heading);

      var text = snippet(item, query);
      if (text) {
        var desc = document.createElement('div');
        desc.className = 'small text-muted mt-1';
        desc.innerHTML = highlight(text, query);
        link.appendChild(desc);
      }
      list.appendChild(link);
    });
    resultsBox.appendChild(list);
  }

  function runSearch(rawQuery, updateUrl) {
    var query = (rawQuery || '').trim().toLowerCase();
    if (!query) {
      resultsBox.innerHTML = '';
      if (status) resultsBox.appendChild(status);
      return;
    }
    if (status && status.parentNode) status.parentNode.removeChild(status);
    if (updateUrl && window.history && window.history.replaceState) {
      var url = new URL(window.location.href);
      url.searchParams.set('q', rawQuery.trim());
      window.history.replaceState({}, document.title, url);
    }
    loadIndex().then(function (items) {
      var matches = items
        .map(function (item) { return { item: item, rank: score(item, query) }; })
        .filter(function (entry) { return entry.rank > 0; })
        .sort(function (a, b) { return b.rank - a.rank; })
        .map(function (entry) { return entry.item; });
      render(matches, rawQuery.trim());
    });
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    runSearch(input.value, true);
  });

var debounce = null; input.addEventListener('input', function () {
    clearTimeout(debounce);
    debounce = setTimeout(function () { runSearch(input.value, true); }, 250);
  });

// Consume the ?q= handoff (from 404.html or shared links). var initial = new URLSearchParams(window.location.search).get('q'); if (initial) {
    input.value = initial;
    runSearch(initial, false);
} })();
</script>

## Can't find what you need

If search doesn't turn up an answer, describe the problem in your own words and we'll point you to the right place — [contact BASH Consulting](/contact/) for a free consultation.
