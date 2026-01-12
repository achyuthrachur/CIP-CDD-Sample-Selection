// Attribute sample size calculator (one-sided upper bound on deviation rate)
// API: sampleSize(N, conf, TER, EER)
// TER/EER are decimals (e.g., 0.04), conf in (0,1)

(function(root) {
  function zScore(conf) {
    const alpha = 1 - conf;
    if (Math.abs(conf - 0.99) < 1e-9) return 2.326; // per spec (one-sided)
    // fall back to precise normal quantile (one-sided)
    if (typeof jStat !== 'undefined' && jStat.normal && jStat.normal.inv) {
      return jStat.normal.inv(1 - alpha, 0, 1);
    }
    // basic approximation if jStat not available in tests
    // Abramowitz-Stegun approximation
    const p = 1 - alpha;
    const a1 = -39.6968302866538,
      a2 = 220.946098424521,
      a3 = -275.928510446969;
    const a4 = 138.357751867269,
      a5 = -30.6647980661472,
      a6 = 2.50662827745924;
    const b1 = -54.4760987982241,
      b2 = 161.585836858041,
      b3 = -155.698979859887;
    const b4 = 66.8013118877197,
      b5 = -13.2806815528857;
    const c1 = -0.00778489400243029,
      c2 = -0.322396458041136,
      c3 = -2.40075827716184;
    const c4 = -2.54973253934373,
      c5 = 4.37466414146497,
      c6 = 2.93816398269878;
    const d1 = 0.00778469570904146,
      d2 = 0.32246712907004,
      d3 = 2.445134137143,
      d4 = 3.75440866190742;
    const plow = 0.02425;
    const phigh = 1 - plow;
    let q, r;
    if (p < plow) {
      q = Math.sqrt(-2 * Math.log(p));
      return (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
        ((((d1 * q + d2) * q + d3) * q + d4) * q + 1);
    } else if (p > phigh) {
      q = Math.sqrt(-2 * Math.log(1 - p));
      return -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
        ((((d1 * q + d2) * q + d3) * q + d4) * q + 1);
    }
    q = p - 0.5;
    r = q * q;
    return (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
      (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1);
  }

  function sampleSize(N, conf, TER, EER) {
    if (!(N >= 1)) throw new Error('Population must be >= 1');
    if (!(conf > 0 && conf < 1)) throw new Error('Confidence must be in (0,1)');
    if (!(TER > 0 && TER < 1)) throw new Error('Tolerable error rate must be in (0,1)');
    if (!(EER >= 0 && EER < 1)) throw new Error('Expected error rate must be in [0,1)');
    if (!(TER > EER)) throw new Error('Tolerable error rate must exceed expected error rate.');

    const z = zScore(conf);
    for (let n = 1; n <= N; n++) {
      // Use expected deviations, rounded up, with a minimum of 1.
      const x = Math.max(1, Math.ceil(n * EER));
      const phat = x / n;
      const ucl = phat + z * Math.sqrt((phat * (1 - phat)) / n);
      if (ucl <= TER) {
        return n;
      }
    }
    return N;
  }

  // Export
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sampleSize, zScore };
  } else {
    root.sampleSize = sampleSize;
    root.zScore = zScore;
  }
})(typeof window !== 'undefined' ? window : globalThis);
