======================================
 Geordi: Interactive Django profiling
======================================

Geordi is a `Django`_ `middleware`_ that lets you interactively profile your
site. Add ``?__geordi__`` to any URL, browse to it, and you'll get a PDF
showing the request's call graph and the time spent in each call.

If you've set ``DEBUG = True`` in your `Django settings`_, anyone can profile
a page–even anonymous users. With ``DEBUG = False``, only super users can
profile pages.

If you're running your Django site under a server like `Gunicorn`_ and you've
configured `time limits on requests`_, you can set ``GEORDI_CELERY = True`` to
run the profiler in a background `Celery`_ task.

.. _Django: https://www.djangoproject.com/
.. _middleware: https://docs.djangoproject.com/en/dev/topics/http/middleware/
.. _Django settings: https://docs.djangoproject.com/en/dev/topics/settings/
.. _Gunicorn: http://gunicorn.org/
.. _time limits on requests: http://gunicorn.org/configure.html#timeout
.. _Celery: http://celeryproject.org/


Installation
------------

Before you get started, make sure you have `GraphViz`_ installed.

After you've done ``pip install geordi``, add ``'geordi'`` to the
``INSTALLED_APPS`` setting, and add ``'geordi.VisorMiddleware'`` to the
``MIDDLEWARE_CLASSES`` setting. You'll probably want to put it after Django's
authentication middleware and before everything else.

For background profiling with Celery, set ``GEORDI_CELERY = True``.

.. _GraphViz: http://www.graphviz.org/
