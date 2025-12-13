// Netlify Function: report
// Expects POST with JSON { password, summary }
// Env vars: OPENAI_API_KEY, REPORT_PASSWORD

export async function handler(event) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method not allowed' };
  }
  try {
    const { password, summary } = JSON.parse(event.body || '{}');
    if (!password || password !== process.env.REPORT_PASSWORD) {
      return { statusCode: 401, body: 'Unauthorized' };
    }
    if (!summary) {
      return { statusCode: 400, body: 'Missing summary' };
    }
    if (!process.env.OPENAI_API_KEY) {
      return { statusCode: 500, body: 'OPENAI_API_KEY not set' };
    }

    const prompt = `Create a concise sampling summary and rationale based on this JSON:\n${JSON.stringify(summary, null, 2)}`;
    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-5.1',
        messages: [
          { role: 'system', content: 'You are a precise auditor writing a brief sampling rationale. Be factual and concise.' },
          { role: 'user', content: prompt },
        ],
        temperature: 0.3,
      }),
    });

    if (!resp.ok) {
      const text = await resp.text();
      return { statusCode: resp.status, body: text };
    }
    const data = await resp.json();
    const content = data.choices?.[0]?.message?.content?.trim() || '';
    return { statusCode: 200, body: JSON.stringify({ report: content }) };
  } catch (err) {
    console.error(err);
    return { statusCode: 500, body: err.message || 'Server error' };
  }
}
