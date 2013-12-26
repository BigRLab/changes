import json
import traceback

from functools import wraps
from urllib import quote

from flask import Response, current_app, request
from flask.views import MethodView

from changes.api.serializer import serialize as serialize_func
from changes.api.stream import EventStream


LINK_HEADER = '<{uri}&page={page}>; rel="{name}"'


def as_json(context):
    return json.dumps(serialize_func(context))


def param(key, validator=lambda x: x, required=True, dest=None):
    def wrapped(func):
        @wraps(func)
        def _wrapped(*args, **kwargs):
            if key in kwargs:
                value = kwargs.pop(key, '')
            elif request.method == 'POST':
                value = request.form.get(key) or ''
            else:
                value = ''

            dest_key = str(dest or key)

            value = value.strip()
            if not value:
                if required:
                    raise ParamError(key, 'value is required')
                return func(*args, **kwargs)

            try:
                value = validator(value)
            except ParamError:
                raise
            except Exception:
                raise ParamError(key, 'invalid value')

            kwargs[dest_key] = value

            return func(*args, **kwargs)

        return _wrapped
    return wrapped


class APIError(Exception):
    pass


class ParamError(APIError):
    def __init__(self, key, msg):
        self.key = key
        self.msg = msg

    def __unicode__(self):
        return '{0} is not valid: {1}'.format(self.key, self.msg)


class APIView(MethodView):
    def dispatch_request(self, *args, **kwargs):
        if 'text/event-stream' in request.headers.get('Accept', ''):
            channels = self.get_stream_channels(**kwargs)
            if not channels:
                return Response(status=404)
            return self.stream_response(channels)

        try:
            return super(APIView, self).dispatch_request(*args, **kwargs)
        except APIError as exc:
            current_app.logger.info(unicode(exc), exc_info=True)
            return self.respond({
                'message': unicode(exc),
            }, status_code=403)
        except Exception as exc:
            current_app.logger.exception(unicode(exc))
            data = {
                'message': 'Internal error',
            }
            if current_app.config['API_TRACEBACKS']:
                data['traceback'] = ''.join(traceback.format_exc())
            return self.respond(data, status_code=500)

    def paginate(self, queryset):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        assert per_page <= 100
        assert page > 0

        offset = (page - 1) * per_page

        result = list(queryset)[offset:offset + per_page + 1]

        links = []
        if page > 1:
            links.append(('previous', page - 1))
        if len(result) > per_page:
            links.append(('next', page + 1))
            result = result[:per_page]

        response = self.respond(result)

        querystring = u'&'.join(
            u'{0}={1}'.format(quote(k), quote(v))
            for k, v in request.args.iteritems()
            if k != 'page'
        )
        base_url = request.base_url
        if querystring:
            base_url += u'?' + querystring

        link_values = []
        for name, page_no in links:
            link_values.append(LINK_HEADER.format(
                uri=base_url,
                page=page_no,
                name=name,
            ))
        if link_values:
            response.headers['Link'] = ', '.join(link_values)
        return response

    def respond(self, context, status_code=200):
        return Response(
            as_json(self.serialize(context)),
            mimetype='application/json',
            status=status_code)

    def serialize(self, *args, **kwargs):
        return serialize_func(*args, **kwargs)

    def as_json(self, context):
        return json.dumps(context)

    def get_stream_channels(self, **kwargs):
        return []

    def stream_response(self, channels):
        stream = EventStream(channels=channels)
        return Response(stream, mimetype='text/event-stream')

    def get_backend(self, app=current_app):
        # TODO this should be automatic via a project
        from changes.backends.jenkins.builder import JenkinsBuilder
        return JenkinsBuilder(app=current_app, base_url=app.config['JENKINS_URL'])
