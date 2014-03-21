from __future__ import absolute_import, division

from lxml import etree

from changes.config import db
from changes.models.filecoverage import FileCoverage

from .base import ArtifactHandler


class CoverageHandler(ArtifactHandler):
    def process(self, fp):
        results = self.get_coverage(fp)

        for result in results:
            # TODO(cramer): this has a race condition
            constraints = {
                'job_id': result.job_id,
                'project_id': result.project_id,
                'filename': result.filename,
            }
            if not FileCoverage.query.filter_by(**constraints).first():
                db.session.add(result)

        return results

    def get_coverage(self, fp):
        """
        Return a phabricator-capable coverage mapping.

        >>> {
        >>>     'foo.py': 'NNNUUUUUUUUUUUUCCCUUUUUCCCCCCCCCNNCNCNCCCNNNN',
        >>> }

        Line flags consists of a single character coverage indicator for each line in the file.

        - N: no coverage available
        - U: uncovered
        - C: covered
        """
        job = self.job

        root = etree.fromstring(fp.read())

        results = []
        for node in root.iter('class'):
            file_coverage = []
            for lineset in node.iterchildren('lines'):
                lineno = 0
                for line in lineset.iterchildren('line'):
                    number, hits = int(line.get('number')), int(line.get('hits'))
                    if lineno < number - 1:
                        for lineno in xrange(lineno, number - 1):
                            file_coverage.append('N')
                    if hits > 0:
                        file_coverage.append('C')
                    else:
                        file_coverage.append('U')
                    lineno = number
            results.append(FileCoverage(
                job_id=job.id,
                project_id=job.project_id,
                filename=node.get('filename'),
                data=''.join(file_coverage),
            ))

        return results
