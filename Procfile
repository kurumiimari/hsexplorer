web: gunicorn --bind :8000 --workers 3 --threads 5 application:app
indexer: LOG_FILE='block_indexer' LOG_DIR='indexers' python3 manage.py run_block_indexer