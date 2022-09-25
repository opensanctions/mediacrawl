# mediacrawl

This repository holds a light-weight scraper for journalistic articles. It
serves as an input to the actual storyweb application. 

The tool has two parts, exposed as command-line functions:

* ``crawl`` will traverse all the HTML pages on a given web site recursively
  and store the downloaded files to a database for analysis. It implements
  some rate limiting and a rule language for determining what links to follow
  while crawling.
* ``parse`` chooses those pages which match a rule set selecting the articles
  to parse, then applies various extraction routines to pull out a standardised
  set of properties describing each article.

Both commands accept a YAML file as an input. The YAML file lists the sites
to be scraped and provides some configuration for the crawler.

``mediacrawl`` is part of storyweb, a project to extract actor networks from 
journalistic reporting: https://storyweb.opensanctions.org

