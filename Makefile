# create virtual environment
.env:
	virtualenv .env -p python3

# install all needed for development
develop: .env
	.env/bin/pip install -r requirements.txt

# run all tests
test: develop
	py.test tests/

# clean the development envrironment
clean:
	-rm -rf .env
