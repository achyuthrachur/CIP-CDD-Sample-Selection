## Serverless report function (Netlify)

Minimal function to keep your OpenAI key off the frontend. Deploy this folder to Netlify, set env vars, and point the frontend at the function URL.

### Files
- `netlify/functions/report.js`: POST endpoint. Expects `{ password, summary }`. Checks `REPORT_PASSWORD`, calls OpenAI Chat Completions (`gpt-5.1`) with the provided sampling summary, returns `{ report }`.
- `netlify.toml`: Configures the functions directory.

### Configure env vars in Netlify
- `OPENAI_API_KEY`: your OpenAI key.
- `REPORT_PASSWORD`: password required from the frontend.

### Deploy
1) Push this folder to a repo and connect to Netlify, or use Netlify CLI:
```bash
netlify deploy --prod
```
2) After deploy, your function URL will look like:
```
https://<your-site>.netlify.app/.netlify/functions/report
```

### Frontend
In the client, POST:
```json
{
  "password": "<REPORT_PASSWORD>",
  "summary": { ... sampling JSON ... }
}
```
and read `data.report` from the response.
