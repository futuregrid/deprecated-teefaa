all:
	cd /tmp
	rm -rf /tmp/vc
	mkdir -p /tmp/vc
	cd /tmp/vc; git clone git://github.com/futuregrid/teefaa.git
	cd /tmp/vc/teefaa/doc; ls; make html
	cp -r /tmp/vc/teefaa/doc/build/html/* .
        find . -name "*.pyc" --exec rm {} \;
	git add .
        git reset -- doc
        git reset -- src
        git reset -- .project .pydevproject .settings
	git commit -a -m "updating the github pages"
#	git commit -a _sources
#	git commit -a _static
	git push
	git checkout master
