PYTHON=python

ifdef PREFIX
PREFIX_ARG=--prefix=$(PREFIX)
endif

all: build

build:
	$(PYTHON) setup.py build

clean:
	-$(PYTHON) setup.py clean --all
	find . -name '*.py[cdo]' -exec rm -f '{}' ';'
	find . -name '*.err' -exec rm -f '{}' ';'
	rm -rf __pycache__ dist build htmlcov
	rm -f README.md MANIFEST *,cover .coverage

install: build
	$(PYTHON) setup.py install $(PREFIX_ARG)

dist:
	TAR_OPTIONS="--owner=root --group=root --mode=u+w,go-w,a+rX-s" \
	$(PYTHON) setup.py -q sdist

tests:
	@echo "There aren't any tests yet!" >& 2 && exit 1

coverage: tests

# E261: two spaces before inline comment
# E301: expected blank line
# E302: two new lines between functions/etc.
pep8:
	pep8 --ignore=E261,E301,E302 --repeat geordi/__init__.py setup.py

pyflakes:
	pyflakes geordi/__init__.py setup.py

pylint:
	pylint --rcfile=.pylintrc geordi/__init__.py setup.py

markdown:
	pandoc -f rst -t markdown README.txt > README.md

.PHONY: all build clean install dist tests coverage pep8 pyflakes pylint \
	markdown
