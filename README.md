# ZimaOS AppStore

## Resources
- [ZimaOS Build Apps](https://www.zimaspace.com/docs/zimaos/Build-Apps)
- [Awesome CasaOS](https://awesome.casaos.io/content/3rd-party-app-stores/create-your-first-custom-appstore.html#steps)
- [Technitium Github Repo](https://github.com/TechnitiumSoftware/DnsServer/blob/master/docker-compose.yml)
- [What network should I use when I install a docker app?](https://share.google/aimode/AzigeRgHFO9oRqhP1)
## Notes
- The first package I created is Technitium DNS Server. It is pretty basic and a good one to use as a template.

## Architectural Design Decisions

### Technitium DNS Server
- Using host network so the DNS service is globally available on my home lab lan. This is not configured in the docker-compose.yml file but was done post install.

