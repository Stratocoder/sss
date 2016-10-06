deps:
	pip install -r requirements.txt
clean:
	find ./ -name *.pyc -delete
test: clean deps
	py.test --verbose tests/
