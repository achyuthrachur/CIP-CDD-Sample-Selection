const assert = require('assert');
const { sampleSize } = require('../docs/sample_size');

const cases = [
  { N: 200, conf: 0.99, TER: 0.04, EER: 0.01, expected: 54 },
  { N: 500, conf: 0.99, TER: 0.04, EER: 0.01, expected: 64 },
  { N: 800, conf: 0.99, TER: 0.04, EER: 0.01, expected: 68 },
  { N: 1000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 69 },
  { N: 2000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 71 },
  { N: 10000, conf: 0.95, TER: 0.04, EER: 0.01, expected: 43 },
  { N: 10000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 74 },
  { N: 50, conf: 0.99, TER: 0.05, EER: 0.01, expected: 50 },
  { N: 200, conf: 0.99, TER: 0.05, EER: 0.01, expected: 51 },
  { N: 10000, conf: 0.99, TER: 0.05, EER: 0.01, expected: 51 },
  { N: 10000, conf: 0.95, TER: 0.05, EER: 0.01, expected: 35 },
];

cases.forEach(({ N, conf, TER, EER, expected }) => {
  const got = sampleSize(N, conf, TER, EER);
  assert.strictEqual(got, expected, `sampleSize(${N}, ${conf}, ${TER}, ${EER}) => ${got}, expected ${expected}`);
});

console.log('All sample_size tests passed.');
