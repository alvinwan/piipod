check:
	bash check.sh

install: requirements.txt install.sh
	bash install.sh

run:
	source activate.sh && \
		python3 run.py

db:
	source activate.sh && \
		python3 run.py -db create

refresh: piap/*/models.py
	source activate.sh && \
		python3 run.py -db refresh
