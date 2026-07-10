---
layout: home

hero:
  name: ZimaOS App Store Developer Docs
  text: Build or migrate a compatible app store
  tagline: One path for creating a store from scratch, one path for upgrading a v1 store while keeping legacy clients working.
  actions:
    - theme: brand
      text: Create a Store
      link: /quick-start/overview
    - theme: alt
      text: Migrate from v1
      link: /migration/overview
    - theme: alt
      text: Read Protocol Reference
      link: /specs/overview

features:
  - title: Start from scratch
    details: Create the minimum source repository, add store identity, add app compose files, build dist, and publish static files.
    link: /quick-start/overview
    linkText: Create a store
  - title: Migrate from v1
    details: Keep the existing Apps tree, add v2-required fields and files, then publish v2 static output while still producing the v1 zip.
    link: /migration/overview
    linkText: Plan the migration
  - title: Protocol reference
    details: Find the required files, x-casaos fields, output files, assets, locale behavior, and field meanings.
    link: /specs/overview
    linkText: Browse specs
  - title: CI/CD
    details: Understand validation, release artifacts, gh-pages publishing, and how to reuse the official build action.
    link: /cicd/overview
    linkText: Set up CI/CD
  - title: FAQ
    details: Get short answers for ID conflicts, hosting, base URLs, build requirements, and minimum store structure.
    link: /faq/overview
    linkText: Read FAQ
---

## Choose a Path

- Creating a new store? Start with [Create a Store](/quick-start/overview).
- Updating an existing v1 store? Start with [Migrate from v1](/migration/overview).
