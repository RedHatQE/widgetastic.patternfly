================================
widgetastic.patternfly-Testing
================================
This project uses the same pattern that wt.core and wt.pf4 use for testing

The pytest fixtures use podman directly to run:
1. selenium container
2. nginx container

Selenium container is used as the webdriver.

nginx container is used to host the testing page.

In order to execute the tests, you have to do some setup for podman.

Pull the selenium and nginx container images:
```
podman pull docker.io/library/nginx:alpine
podman pull quay.io/redhatqe/selenium-standalone:latest
```


Create a directory for the podman socket, and start a listening service:
```
mkdir -p ${XDG_RUNTIME_DIR}/podman
podman system service --time=0 unix://${XDG_RUNTIME_DIR}/podman/podman.sock &
```
