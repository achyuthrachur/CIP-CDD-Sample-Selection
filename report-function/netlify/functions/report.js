// Netlify Function: report
// Expects POST with JSON { summary }
// Env vars: OPENAI_API_KEY

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type, Accept',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

export async function handler(event) {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers: corsHeaders, body: '' };
  }
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers: corsHeaders, body: 'Method not allowed' };
  }
  try {
    const { summary } = JSON.parse(event.body || '{}');
    if (!summary) {
      return { statusCode: 400, headers: corsHeaders, body: 'Missing summary' };
    }
    if (!process.env.OPENAI_API_KEY) {
      return { statusCode: 500, headers: corsHeaders, body: 'OPENAI_API_KEY not set' };
    }

    const prompt = `You are an expert internal audit / risk / CIP CDD sampling analyst focusing on onboarding data (not KYC).

You will be given a JSON summary of a sampling exercise. It may contain:
- methodology: { method, confidence, margin, expected_error_rate, planned_sample_size, seed, systematic_random_start, ... }
- stratify_fields: e.g., ["Jurisdiction"]
- source: { file_name, sheet_name }
- population: { size, distribution: [{ stratum: {...}, count, share }, ...] }
- sample: { size, distribution: [{ stratum: {...}, count, share }, ...] }
- allocations: [{ stratum: {...}, population_count, sample_count, share_of_population, share_of_sample }, ...]
- sample_ids: [list of sampled record IDs]

Produce a clear, professional narrative report in plain text (no Markdown, no tables, no # or * characters, no bold/italic). Use simple numbered sections and plain lines. Convert proportions to percentages where helpful. Do NOT include the raw JSON in the report; treat it as back-end data only. Use only numbers present in the JSON.

Use these section headings (plain text):
1. Objective and context
2. Source data and population summary
3. Sampling methodology
4. Sampling rationale
5. Sample summary
6. Allocation analysis and representativeness
7. Limitations and considerations
8. Conclusion

For distributions, list each stratum on its own line like:
Stratum: <values> | Count: <n> | Population share: <p%> (and Sample share: <p%> if available)

Focus on onboarding data and control testing (not KYC). Write in audit-friendly language.

JSON data:
${JSON.stringify(summary, null, 2)}`;
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
      return { statusCode: resp.status, headers: corsHeaders, body: text };
    }
    const data = await resp.json();
    const content = data.choices?.[0]?.message?.content?.trim() || '';
    return { statusCode: 200, headers: corsHeaders, body: JSON.stringify({ report: content }) };
  } catch (err) {
    console.error(err);
    return { statusCode: 500, headers: corsHeaders, body: err.message || 'Server error' };
  }
}
