
wheel:
	python setup.py bdist_wheel
docker: wheel
	cp dist/*.whl docker/root/
	sudo docker build --no-cache -t ytdl-sub:0.1 docker/
docs:
	sphinx-build -a -b html docs docs/_html

.PHONY: wheel docker docs
