from __future__ import absolute_import

import mock
import responses

from changes.constants import Result
from changes.models import Build, RepositoryBackend
from flask import Flask
from uuid import UUID

from changes.listeners.green_build import build_finished_handler


app = Flask(__name__)
app.config['BASE_URI'] = 'http://localhost'
app.config['GREEN_BUILD_URL'] = 'https://foo.example.com'
app.config['GREEN_BUILD_AUTH'] = ('username', 'password')


@responses.activate
@mock.patch('changes.listeners.green_build.get_options')
def test_simple(get_options):
    with app.test_request_context():
        release_id = '134:asdadfadf'

        responses.add(responses.POST, 'https://foo.example.com')
        get_options.return_value = {
            'green-build.notify': '1',
        }

        build = mock.Mock(spec=Build())
        build.patch_id = None
        build.project.slug = 'server'
        build.id = UUID(hex='c' * 32)
        build.project_id = UUID(hex='b' * 32)
        build.revision_sha = 'a' * 40
        build.repository.backend = RepositoryBackend.hg

        vcs = build.repository.get_vcs.return_value
        vcs.run.return_value = release_id

        # test with failing build
        build.result = Result.failed

        build_finished_handler(build)

        assert len(responses.calls) == 0

        # test with passing build
        build.result = Result.passed

        build_finished_handler(build)

        vcs.run.assert_called_once_with([
            'log', '-r aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', '--limit=1',
            '--template={rev}:{node|short}'
        ])

        get_options.assert_called_once_with(build.project_id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == 'https://foo.example.com/'
        assert responses.calls[0].request.body == 'project=server&build_server=changes&build_url=http%3A%2F%2Flocalhost%2Fprojects%2Fserver%2Fbuilds%2Fcccccccccccccccccccccccccccccccc%2F&id=134%3Aasdadfadf'
