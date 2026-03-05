<script>
  export let results = [];
  export let loading = false;

  $: maxScore = results.length > 0 ? Math.max(...results.map(r => r.score)) : 1;
  $: maxSimilarity = results.length > 0 ? Math.max(...results.map(r => r.similarity)) : 1;

  // Similarity strength interpretation
  function getSimilarityStrength(sim) {
    if (sim >= 0.30) return { label: 'Strong', class: 'strong' };
    if (sim >= 0.25) return { label: 'Good', class: 'good' };
    if (sim >= 0.20) return { label: 'Moderate', class: 'moderate' };
    if (sim >= 0.15) return { label: 'Weak', class: 'weak' };
    return { label: 'Low', class: 'low' };
  }
</script>

<div class="results-container">
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <span>Running inference...</span>
    </div>
  {:else if results.length === 0}
    <div class="empty">
      <p>No results yet. Upload a file and run classification.</p>
    </div>
  {:else}
    <div class="results-header">
      <h3>Classification Results</h3>
      <div class="legend">
        <span class="legend-item">
          <span class="legend-color similarity-color"></span>
          Cosine Similarity (absolute)
        </span>
        <span class="legend-item">
          <span class="legend-color probability-color"></span>
          Softmax Probability (relative)
        </span>
      </div>
    </div>

    <div class="results-list">
      {#each results as result, i}
        {@const strength = getSimilarityStrength(result.similarity)}
        <div class="result-item" class:top={i === 0}>
          <div class="result-header">
            <span class="rank">#{i + 1}</span>
            <span class="label">{result.label}</span>
            <div class="scores">
              <span class="similarity" class:strong={strength.class === 'strong'} class:good={strength.class === 'good'}>
                {result.similarity.toFixed(3)}
              </span>
              <span class="score">{(result.score * 100).toFixed(1)}%</span>
            </div>
          </div>

          <div class="bars">
            <div class="bar-row">
              <div class="bar-container similarity-bar">
                <div
                  class="bar similarity-fill"
                  style="width: {Math.max(0, (result.similarity / 0.4) * 100)}%"
                  class:top-bar={i === 0}
                ></div>
              </div>
            </div>
            <div class="bar-row">
              <div class="bar-container probability-bar">
                <div
                  class="bar probability-fill"
                  style="width: {(result.score / maxScore) * 100}%"
                  class:top-bar-prob={i === 0}
                ></div>
              </div>
            </div>
          </div>

          {#if i === 0}
            <div class="match-indicator {strength.class}">
              {strength.label} match
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <div class="interpretation">
      <p><strong>Reading the scores:</strong></p>
      <ul>
        <li><strong>Cosine Similarity</strong> (top bar): Absolute match strength. 0.25+ is good, 0.30+ is strong.</li>
        <li><strong>Softmax %</strong> (bottom bar): Relative ranking among candidates. Sums to 100%.</li>
      </ul>
    </div>
  {/if}
</div>

<style>
  .results-container {
    margin-top: 1.5rem;
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  h3 {
    margin: 0;
    font-size: 1rem;
    color: #94a3b8;
  }

  .legend {
    display: flex;
    gap: 1rem;
    font-size: 0.7rem;
    color: #64748b;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .legend-color {
    width: 12px;
    height: 6px;
    border-radius: 2px;
  }

  .similarity-color {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
  }

  .probability-color {
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    color: #94a3b8;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #334155;
    border-top-color: #60a5fa;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .empty {
    text-align: center;
    padding: 2rem;
    color: #64748b;
  }

  .results-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 400px;
    overflow-y: auto;
  }

  .result-item {
    background: #0f172a;
    border-radius: 8px;
    padding: 0.75rem;
    transition: transform 0.2s;
    position: relative;
  }

  .result-item.top {
    background: linear-gradient(135deg, #1e3a5f, #1e293b);
    border: 1px solid #3b82f6;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .rank {
    font-weight: 600;
    color: #64748b;
    font-size: 0.875rem;
    min-width: 2rem;
  }

  .top .rank {
    color: #60a5fa;
  }

  .label {
    flex: 1;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .scores {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  .similarity {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.8rem;
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.1);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
  }

  .similarity.strong, .similarity.good {
    color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
  }

  .score {
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.8rem;
    color: #60a5fa;
    min-width: 3.5rem;
    text-align: right;
  }

  .bars {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .bar-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .bar-container {
    flex: 1;
    height: 5px;
    background: #334155;
    border-radius: 3px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease-out;
  }

  .similarity-fill {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
  }

  .probability-fill {
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
  }

  .top-bar {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }

  .top-bar-prob {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }

  .match-indicator {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
  }

  .match-indicator.strong {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }

  .match-indicator.good {
    background: rgba(34, 197, 94, 0.15);
    color: #86efac;
  }

  .match-indicator.moderate {
    background: rgba(251, 191, 36, 0.15);
    color: #fcd34d;
  }

  .match-indicator.weak {
    background: rgba(251, 146, 60, 0.15);
    color: #fdba74;
  }

  .match-indicator.low {
    background: rgba(248, 113, 113, 0.15);
    color: #fca5a5;
  }

  .interpretation {
    margin-top: 1rem;
    padding: 0.75rem;
    background: #1e293b;
    border-radius: 6px;
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .interpretation p {
    margin: 0 0 0.5rem;
  }

  .interpretation ul {
    margin: 0;
    padding-left: 1.25rem;
  }

  .interpretation li {
    margin-bottom: 0.25rem;
  }

  .interpretation strong {
    color: #e2e8f0;
  }
</style>
