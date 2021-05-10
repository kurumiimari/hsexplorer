# hsexplorer

A Handshake block explorer. The backend is written in Python/Flask, and frontend interactions are written in Javascript/React.

A live beta version is available at [http://hsexplorer-prod.us-west-2.elasticbeanstalk.com/](http://hsexplorer-prod.us-west-2.elasticbeanstalk.com/). 

## Local Development

You'll need the following things to run the dev server locally:

1. Python 3. This should be installed with most modern OSes; if not use `brew`/`apt`/`yum` or whatever your package manager of choice is to install it.
2. Postgres.
3. Redis.
4. A synchronized mainnet HSD node in order to run the indexer.

Once all these are installed, `cd` into the root of the project. Then, run the following command to run the database migrations:

```
python3 manage.py db upgrade head
```

Next, make sure Redis is started. This is usually as easy as running `redis-server` in a dedicated terminal window.

Now, you can run the following command to start the dev server:

```bash
FLASK_ENV=development python3 application.py
```

The application will be available at `http://localhost:8000`. There won't be any blocks, however - to populate them, you'll need to run the indexer. Run this command in a dedicated terminal to do that:

```bash
python3 manage.py run_block_indexer
```

It'll take a while (4-8 hours depending on your machine) to index the entire blockchain. However, you should be able to see historical blocks showing up on the web app almost immediately.

Price and mempool info are also provided by dedicated indexers that you can run with these commands:

```bash
python3 manage.py run_mempool_indexer
python3 manage.py run_tick_indexer
```

You can also contact Kurumi for a SQL dump of an almost-synced database. No promises, though ✨.

### Customizing Your Environment

`hsexplorer` is configured using environment variables. The following environment variables are available:

- `FLASK_ENV`: Sets Flask's env type. Can be `development` or `production`.
- `SQLALCHEMY_DATABASE_URI`: Configures the application's database URI.
- `SQLALCHEMY_ECHO`: When set to `1`, turns on query logging.
- `SECRET_KEY`: Flask's secret key. Used to generate session IDs.
- `HSD_HOST`: The full-qualified URL (i.e., hostname with scheme and port) to the indexer's HSD node.
- `HSD_API_KEY`: The API key used to authenticate with the indexer's HSD node.
- `REDIS_URL`: Configures the application's redis URL.
- `MANAGEMENT_KEY`: Sets the secret key used to authenticate with management endpoints.

### Developing New JS Bundles

This is a multi-page app where the server generates most pages. However, to add richer functionality `hsexplorer` supports the concept of "JavaScript bundles." These are simply `webpack` entrypoints that are automatically picked up by the template engine and rendered on the page. All JS bundles are implemented in the `ui` folder.


To create a new JS bundle, do the following:

1. Create a new entrypoint in `webpack.config.js` that points to an entrypoint file in `ui/entries`.
2. On the page that you want the entrypoint to appear, use the `{{ bundle_root('<bundle_name>') }}` helper to include both your script and a `div` element to render your components into.
3. Implement your entrypoint to call `ReactDOM.render()` with a target element of id `bundle-root-<bundle_name>`.

To view your changes live, run `npm run watch` to automatically regenerate your JS bundles on save. You'll need to manually refresh whatever page you are on to see them.

Note that if `FLASK_ENV` is not set to `development`, bundles and static assets will be cached.

Check out the `names.js` file in `ui/entries` for a "Hello World" example of how the bundling system works.