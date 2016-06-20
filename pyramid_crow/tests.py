import unittest
from pyramid import testing
from webtest import TestApp
import mock
import pyramid_crow


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.config = config = testing.setUp(
            settings={
                'raven.dsn': 'https://foo:bar@example.com/notadsn',
            }
        )
        config.include('pyramid_crow')

    def tearDown(self):
        testing.tearDown()

    def _makeApp(self):
        app = self.config.make_wsgi_app()
        return TestApp(app)

    def test_noop(self):
        config = self.config

        def view(request):
            return 'ok'

        config.add_view(view, name='', renderer='string')

        app = self._makeApp()
        resp = app.get('/')
        self.assertEqual(resp.body, b'ok')

    def test_capture_called(self):
        config = self.config

        def view(request):
            self.request = request
            raise Exception()

        config.add_view(view, name='', renderer='string')

        app = self._makeApp()

        with mock.patch.object(pyramid_crow.Client,
                               'captureException') as mock_capture:
            self.assertRaises(Exception, app.get, '/')

        mock_capture.assert_called_once()
        self.assertEqual(
            self.request.raven.context['request']['method'], 'GET'
        )
        self.assertEqual(
            self.request.raven.context['request']['url'], 'http://localhost/'
        )
        self.assertEqual(
            self.request.raven.context['request']['data'], ''
        )
        self.assertEqual(
            self.request.raven.context['request']['query_string'], ''
        )
        self.assertEqual(
            self.request.raven.context['request']['headers'],
            {'Host': 'localhost:80'},
        )

    def test_capture_query_string(self):
        config = self.config

        def view(request):
            self.request = request
            raise Exception()

        config.add_view(view, name='', renderer='string')

        app = self._makeApp()

        with mock.patch.object(pyramid_crow.Client,
                               'captureException') as mock_capture:
            self.assertRaises(Exception, app.get, '/',
                              params=(('foo', 'bar'), ('baz', 'garply')))

        mock_capture.assert_called_once()
        self.assertEqual(
            self.request.raven.context['request']['method'], 'GET'
        )
        self.assertEqual(
            self.request.raven.context['request']['url'], 'http://localhost/'
        )
        self.assertEqual(
            self.request.raven.context['request']['data'], ''
        )
        self.assertEqual(
            self.request.raven.context['request']['query_string'],
            'foo=bar&baz=garply'
        )
        self.assertEqual(
            self.request.raven.context['request']['headers'],
            {'Host': 'localhost:80'},
        )

    def test_capture_body(self):
        config = self.config

        def view(request):
            self.request = request
            raise Exception()

        config.add_view(view, name='', renderer='string')

        app = self._makeApp()

        with mock.patch.object(pyramid_crow.Client,
                               'captureException') as mock_capture:
            self.assertRaises(Exception, app.post, '/',
                              params=(('foo', 'bar'), ('baz', 'garply')))

        mock_capture.assert_called_once()
        self.assertEqual(
            self.request.raven.context['request']['method'], 'POST'
        )
        self.assertEqual(
            self.request.raven.context['request']['url'], 'http://localhost/'
        )
        self.assertEqual(
            self.request.raven.context['request']['data'], 'foo=bar&baz=garply'
        )
        self.assertEqual(
            self.request.raven.context['request']['query_string'], ''
        )
        self.assertEqual(
            self.request.raven.context['request']['headers'],
            {
                'Content-Length': '18',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'localhost:80',
            },
        )