const assert = require('assert');
const { sampleSize } = require('../docs/sample_size');

const cases = [
  { N: 200, conf: 0.99, TER: 0.04, EER: 0.01, expected: 47 },
  { N: 500, conf: 0.99, TER: 0.04, EER: 0.01, expected: 54 },
  { N: 800, conf: 0.99, TER: 0.04, EER: 0.01, expected: 56 },
  { N: 1000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 57 },
  { N: 2000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 58 },
  { N: 10000, conf: 0.95, TER: 0.04, EER: 0.01, expected: 30 },
  { N: 10000, conf: 0.99, TER: 0.04, EER: 0.01, expected: 60 },
  { N: 50, conf: 0.99, TER: 0.05, EER: 0.01, expected: 21 },
  { N: 200, conf: 0.99, TER: 0.05, EER: 0.01, expected: 29 },
  { N: 10000, conf: 0.99, TER: 0.05, EER: 0.01, expected: 34 },
  { N: 10000, conf: 0.95, TER: 0.05, EER: 0.01, expected: 17 },
];

cases.forEach(({ N, conf, TER, EER, expected }) => {
  const got = sampleSize(N, conf, TER, EER);
  assert.strictEqual(got, expected, `sampleSize(${N}, ${conf}, ${TER}, ${EER}) => ${got}, expected ${expected}`);
});

console.log('All sample_size tests passed.');
