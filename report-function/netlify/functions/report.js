// Netlify Function: report
// Expects POST with JSON { password, summary }
// Env vars: OPENAI_API_KEY, REPORT_PASSWORD

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
    const { password, summary } = JSON.parse(event.body || '{}');
    const requiredPassword = process.env.REPORT_PASSWORD;
    if (requiredPassword && password !== requiredPassword) {
      return { statusCode: 401, headers: corsHeaders, body: 'Unauthorized' };
    }
    if (!summary) {
      return { statusCode: 400, headers: corsHeaders, body: 'Missing summary' };
    }
    if (!process.env.OPENAI_API_KEY) {
      return { statusCode: 500, headers: corsHeaders, body: 'OPENAI_API_KEY not set' };
    }

    const prompt = `You are an expert internal audit / risk / CIP CDD sampling analyst.

I will give you a JSON object that summarizes a sampling exercise. It will typically contain keys like:
- methodology: { method, confidence, margin, expected_error_rate, planned_sample_size, seed, systematic_random_start, ... }
- stratify_fields: e.g. ["Jurisdiction"]
- source: { file_name, sheet_name }
- population: { size, distribution: [{ stratum: {...}, count, share }, ...] }
- sample: { size, distribution: [{ stratum: {...}, count, share }, ...] }
- allocations: [{ stratum: {...}, population_count, sample_count, share_of_population, share_of_sample }, ...]
- sample_ids: [list of sampled record IDs]

Your task is to write a clear, professional narrative report in markdown, suitable for inclusion in an internal audit or risk working paper.

Requirements for the report structure (use these exact headings):
1. Objective and context
2. Source data and population summary (include a markdown table of population distribution)
3. Sampling methodology (confidence %, margin %, expected error %, planned sample size, seed/systematic start)
4. Sampling rationale (why the method/parameters/stratification are appropriate)
5. Sample summary (actual sample size and a markdown table of sample vs population shares)
6. Allocation analysis and representativeness
7. Limitations and considerations
8. Conclusion

Style:
- Clear, professional audit language.
- Use only numbers present in the JSON (convert proportions to % where helpful).
- Do NOT include the raw JSON in the report; treat it as back-end data only.

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
