check:
	source manage.sh && \
		gs_check

install: requirements.txt manage.sh
	source manage.sh && \
		gs_install

run:
	source manage.sh activate && \
		python3 run.py

db:
	source manage.sh activate && \
		python3 run.py -db create && \
		python migrate.py db init

refresh:
	source manage.sh activate && \
		python3 run.py -db refresh

migrate:
	source manage.sh activate && \
		python migrate.py db migrate

upgrade:
	source manage.sh activate && \
		python migrate.py db upgrade

tornado:
	source manage.sh activate && \
		python3 run.py --tornado
