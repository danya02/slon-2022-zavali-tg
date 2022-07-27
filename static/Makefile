all: download

download: bootstrap.min.css bootstrap.bundle.min.js jquery.min.js

bootstrap.min.css:
	@echo "Downloading Bootstrap CSS..."
	wget -O bootstrap.min.css "https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/css/bootstrap.min.css"

bootstrap.bundle.min.js:
	@echo "Downloading Bootstrap JS..."
	wget -O bootstrap.bundle.min.js "https://cdn.jsdelivr.net/npm/bootstrap@5.2.0-beta1/dist/js/bootstrap.bundle.min.js"

jquery.min.js:
	@echo "Downloading jQuery JS..."
	wget -O jquery.min.js "https://code.jquery.com/jquery-3.6.0.min.js"

clean:
	rm -f bootstrap.min.css bootstrap.bundle.min.js jquery.min.js

