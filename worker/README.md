# JD proxy (Cloudflare Worker)

Backs the Copy JD button on the public Jobs Tracker page. Stateless: the page sends the ATS details
for one posting, the Worker fetches its description from the employer's public job API and returns
plain text.

Deploy once:

    cd worker
    npx wrangler login
    npx wrangler deploy

Set the deployed URL through the JD_PROXY_URL environment variable when generating the queue page.

Only these hosts are ever fetched: boards-api.greenhouse.io, api.lever.co, api.eu.lever.co,
api.ashbyhq.com, api.smartrecruiters.com, `*.myworkdayjobs.com`, `*.oraclecloud.com`, plus, for every other ATS, only the https hosts listed for that company in the page's map (config host fields and the hosts of its queue links). Those are read as HTML (JSON-LD, then the description block); boards that render in the browser return a clear "copy it by hand" error.
