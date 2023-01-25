# mediacrawl

This repository holds a light-weight crawler for journalistic articles. It serves as an input to the actual [storyweb](https://storyweb.opensanctions.org) application by producing data files in the [`articledata`](https://github.com/pudo/articledata/) format. 

The tool has two parts, exposed as command-line functions:

* ``crawl`` will traverse all the HTML pages on a given web site recursively
  and store the downloaded files to a database for analysis. It implements
  some rate limiting and a rule language for determining what links to follow
  while crawling.
* ``parse`` chooses those pages which match a rule set selecting the articles
  to parse, then applies various extraction routines to pull out a standardised
  set of properties describing each article.

Both commands accept a YAML configuration file as an input. The YAML file lists the sites to be scraped and provides some configuration for the crawler.

## Configuration format

The `mediacrawl` configuration file supplies the article crawler with a set of domains to be included and further rules about what material published on those sites should be considered "articles" (as opposed to, for example, listing and home pages, author profiles, etc.):

```yaml
sites:
  # Example configuration to crawl the International Consortium of Investigative Journalists'
  # web site:
  - name: icij.org
    # These URLs are used to start the crawl. The more the merrier:
    urls:
      - https://www.icij.org/
      - https://www.icij.org/inside-icij/
    # Create only one connection to any of the traversed domain names at a time:
    domain_concurrency: 1
    # Sleep for one second (can be a float) after each page's retrieval:
    delay: 1
    # Remove some marketing/tracking details from URLs in order to avoid duplication
    # of the imported articles:
    query_ignore:
      - utm_term
      - utm_source
      - utm_campaign
      - utm_medium

    # The sections below use a rule language to determine if pages should be included
    # in the given stage of the media crawl. It defines a set of filter criteria that 
    # a given page must match (such as: domain, mime, element, xpath or pattern), and
    # a set of boolean criteria that can be used to make arbitrary combinations of the
    # filters.

    # Check if a candidate page should be crawled, i.e. downloaded and checked for more
    # links that can be followed by the crawler engine:
    crawl:
      and:
        - or:
            - domain: icij.org
        - not:
            or:
              - mime: nonweb
              - domain: offshoreleaks.icij.org
              - domain: medicaldevices.icij.org
              - domain: wwwmaster.icij.org
              - domain: media.icij.org
              - domain: dev.icij.org
              - domain: datashare.icij.org
              - domain: donate.icij.org
              - domain: cloudfront-4.icij.org
              - domain: wwww.icij.org

    # Check if a given page is also meant to be parsed as an article. This should be a set
    # of criteria that define HTML elements or URL paths typical of articles and which do
    # not occur on non-article page (e.g. listings, category pages). 
    # Pages which have not been crawled cannot be parsed, so the parse section implicitly
    # will only consider pages that have matched the `crawl` set of criteria.
    parse:
      or:
        - element: .//time[@class="post-published"]


```

## Usage

The application can either be run as a raw Python tool by installing the dependencies listed in `requirements.txt` and the checked-out directory of the application, or as a docker container (`docker pull ghcr.io/opensanctions/mediacrawl:main`). Here's the commands for a manual install:

```bash
git clone https://github.com/opensanctions/mediacrawl.git 
cd mediacrawl
pip install -r requirements.txt
pip install -e ".[dev]"
```

`mediacrawl` expects the `MEDIACRAWL_DATABASE_URL` environment variable to be set to the async SQLAlchemy URL for a PostgreSQL database, e.g.:

```bash
export MEDIACRAWL_DATABASE_URL=postgresql+asyncpg://localhost/mediacrawl
```

Finally, you can run the application by pointing it to your YAML configuration file for the sites you wish to crawl (`my_sites.yml` below):

```bash
mediacrawl crawl my_sites.yml
mediacrawl parse my_sites.yml --outpath article-exports/
```

The resulting data dumps in the `article-exports/` folder can subsequently be imported into `storyweb` or any other application using the `articledata` micro-format. 

## Credits

The most complex problem to be solved by `mediacrawl` is extracting particular aspects of a news story (e.g. its title, summary, author, body or publication date) from a downloaded HTML file. This functionality is implemented by the amazing [`trafilatura`](https://trafilatura.readthedocs.io/en/latest/) library developed by Adrien Barbaresi.

``mediacrawl`` is part of StoryWeb, a project to extract actor networks from journalistic reporting: https://storyweb.opensanctions.org. StoryWeb is a project funded by [Prototypefund](https://prototypefund.de/) with funding from the German ministry of research and education (BMBF). 

## License

See `LICENSE`, standard MIT license.

