check:
	bash check.sh

install: requirements.txt install.sh
	bash install.sh

run:
	source activate.sh && \
		python3 run.py

db:
	source activate.sh && \
		python3 run.py -db create && \
		python migrate.py db init

refresh: piap/*/models.py
	source activate.sh && \
		python3 run.py -db refresh

migrate:
	source activate.sh && \
		python migrate.py db migrate && \
		python migrate.py db upgrade

tornado:
	source activate.sh && \
		python3 run.py --tornado
