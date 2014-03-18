from __future__ import absolute_import, division, print_function

from datetime import datetime
from rfc822 import parsedate_tz, mktime_tz
from urlparse import urlparse

from .base import Vcs, RevisionResult, BufferParser

LOG_FORMAT = '{node}\x01{author}\x01{date|rfc822date}\x01{p1node} {p2node}\x01{desc}\x02'


class MercurialVcs(Vcs):
    binary_path = 'hg'

    def get_default_env(self):
        return {
            'HGPLAIN': '1',
        }

    @property
    def remote_url(self):
        if self.url.startswith(('ssh:', 'http:', 'https:')):
            parsed = urlparse(self.url)
            url = '%s://%s@%s/%s' % (
                parsed.scheme,
                parsed.username or self.username or 'hg',
                parsed.hostname + (':%s' % (parsed.port,) if parsed.port else ''),
                parsed.path.lstrip('/'),
            )
        else:
            url = self.url
        return url

    def run(self, cmd, **kwargs):
        cmd = [
            self.binary_path,
            '--config',
            'ui.ssh={0}'.format(self.ssh_connect_path)
        ] + cmd
        return super(MercurialVcs, self).run(cmd, **kwargs)

    def clone(self):
        self.run(['clone', '--uncompressed', self.remote_url, self.path])

    def update(self):
        self.run(['pull'])

    def log(self, parent=None, limit=100):
        # TODO(dcramer): we should make this streaming
        cmd = ['log', '--template=%s' % (LOG_FORMAT,)]
        if parent:
            cmd.append('-r %s' % (parent,))
        if limit:
            cmd.append('--limit=%d' % (limit,))
        result = self.run(cmd)

        for chunk in BufferParser(result, '\x02'):
            (sha, author, author_date, parents, message) = chunk.split('\x01')

            parents = filter(lambda x: x and x != '0' * 40, parents.split(' '))

            author_date = datetime.utcfromtimestamp(
                mktime_tz(parsedate_tz(author_date)))

            yield RevisionResult(
                id=sha,
                author=author,
                author_date=author_date,
                message=message,
                parents=parents,
            )

    def export(self, id):
        cmd = ['diff', '-g', '-c %s' % (id,)]
        result = self.run(cmd)
        print (cmd, result)
        return result
