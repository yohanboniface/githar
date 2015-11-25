"""
Create activity report from Github commits.

Usage:
    cli.py <orga/name>... [options]

Options:
  -h --help             Show this screen.
  --author=<name>       Name of the author to filter commits.
  --since=<date>        Only commits since this date (format: YYYY-MM-DD)
  --until=<date>        Only commits until this date (format: YYYY-MM-DD)
  --format=<format>     Format to use for output ('text', 'markdown')
"""

from docopt import docopt
import requests

TEMPLATE = 'https://api.github.com/repos/{}/commits'


class Repository:

    def __init__(self, path, format='text', **filters):
        self.path = path
        self.filters = filters
        self.data = []
        self.format = format

    def __call__(self):
        url = TEMPLATE.format(self.path)
        while url:
            r = requests.get(url, params=self.filters)
            self.data.extend(r.json())
            url = r.links.get('next', {}).get('url')
        return self

    def __iter__(self):
        for metadata in self.data[::-1]:
            commit = Commit(metadata, self.format)
            if commit.is_merge:
                continue
            yield commit

    def __str__(self):
        if self.format == 'markdown':
            return self.as_markdown()
        return self.as_text()

    def format_filters(self):
        return ' | '.join('{}={}'.format(k, v)
                          for k, v in self.filters.items() if v)

    def as_text(self):
        return "{}\n\n{}\n\n{}".format(
            self.path,
            self.format_filters(),
            '\n'.join(str(commit) for commit in self)
        )

    def as_markdown(self):
        return "# {}\n\n{}\n\n{}".format(
            self.path,
            self.format_filters(),
            '\n\n'.join(str(commit) for commit in self)
        )


class Commit:

    def __init__(self, metadata, format):
        self.metadata = metadata
        self.format = format

    def __str__(self):
        if self.format == 'markdown':
            return self.as_markdown()
        return self.as_text()

    def as_text(self):
        return '{}\t{}'.format(self.date, self.message)

    def as_markdown(self):
        return '{}    [{}]({})'.format(self.date, self.message, self.url)

    @property
    def message(self):
        return self.metadata['commit']['message'].split('\n')[0]

    @property
    def date(self):
        return self.metadata['commit']['author']['date'][:10]

    @property
    def url(self):
        return self.metadata['html_url']

    @property
    def is_merge(self):
        return len(self.metadata['parents']) == 2


if __name__ == '__main__':
    args = docopt(__doc__, version='1.0')
    for path in args['<orga/name>']:
        repo = Repository(path, format=args['--format'],
                          author=args['--author'], since=args['--since'],
                          until=args['--until'])
        print(repo())
