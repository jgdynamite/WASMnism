<script>
  export let metricsHistory = [];

  $: latestMetrics = metricsHistory[0] || null;

  function formatTime(ms) {
    if (ms < 1) return '<1ms';
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  }

  function getBarWidth(value, max) {
    return Math.min((value / max) * 100, 100);
  }

  $: maxTime = latestMetrics
    ? Math.max(
        latestMetrics.input_encoding_ms,
        latestMetrics.text_encoding_ms,
        latestMetrics.similarity_ms
      )
    : 100;
</script>

<div class="metrics-panel">
  <h2>Performance Metrics</h2>

  {#if latestMetrics}
    <div class="current-metrics">
      <h3>Latest Request ({latestMetrics.type.toUpperCase()})</h3>

      <div class="metric-row">
        <span class="metric-label">Input Encoding</span>
        <div class="metric-bar-container">
          <div
            class="metric-bar input"
            style="width: {getBarWidth(latestMetrics.input_encoding_ms, maxTime)}%"
          ></div>
        </div>
        <span class="metric-value">{formatTime(latestMetrics.input_encoding_ms)}</span>
      </div>

      <div class="metric-row">
        <span class="metric-label">Text Encoding</span>
        <div class="metric-bar-container">
          <div
            class="metric-bar text"
            style="width: {getBarWidth(latestMetrics.text_encoding_ms, maxTime)}%"
          ></div>
        </div>
        <span class="metric-value">{formatTime(latestMetrics.text_encoding_ms)}</span>
      </div>

      <div class="metric-row">
        <span class="metric-label">Similarity</span>
        <div class="metric-bar-container">
          <div
            class="metric-bar similarity"
            style="width: {getBarWidth(latestMetrics.similarity_ms, maxTime)}%"
          ></div>
        </div>
        <span class="metric-value">{formatTime(latestMetrics.similarity_ms)}</span>
      </div>

      <div class="metric-summary">
        <div class="summary-item">
          <span class="summary-label">Total Time</span>
          <span class="summary-value highlight">{formatTime(latestMetrics.total_inference_ms)}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Candidates</span>
          <span class="summary-value">{latestMetrics.num_candidates}</span>
        </div>
      </div>
    </div>

    {#if metricsHistory.length > 1}
      <div class="history">
        <h3>History (Last {metricsHistory.length} requests)</h3>
        <div class="history-chart">
          {#each metricsHistory as metrics, i}
            <div class="history-bar-container">
              <div
                class="history-bar"
                class:clip={metrics.type === 'clip'}
                class:clap={metrics.type === 'clap'}
                style="height: {Math.min((metrics.total_inference_ms / Math.max(...metricsHistory.map(m => m.total_inference_ms))) * 100, 100)}%"
                title="{metrics.type.toUpperCase()}: {formatTime(metrics.total_inference_ms)} ({metrics.num_candidates} labels)"
              ></div>
              <span class="history-label">{metrics.num_candidates}</span>
            </div>
          {/each}
        </div>
        <div class="history-legend">
          <span class="legend-item clip">CLIP</span>
          <span class="legend-item clap">CLAP</span>
          <span class="legend-note">Bar height = total time, label = # candidates</span>
        </div>
      </div>
    {/if}
  {:else}
    <div class="empty-state">
      <p>Run a classification to see performance metrics.</p>
      <p class="hint">
        Try running the same image/audio with different numbers of candidate labels
        to see how inference time scales.
      </p>
    </div>
  {/if}

  <div class="info-section">
    <h3>Understanding the Metrics</h3>
    <ul>
      <li><strong>Input Encoding:</strong> Time to process image/audio through the encoder</li>
      <li><strong>Text Encoding:</strong> Time to encode all candidate labels (scales with count)</li>
      <li><strong>Similarity:</strong> Time to compute cosine similarities</li>
    </ul>
    <p class="tip">
      Sweet spot: 300-400 labels for reliable discrimination.
      Above 1000 labels, inference time becomes noticeable.
    </p>
  </div>
</div>

<style>
  .metrics-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  h2 {
    margin: 0;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
  }

  h3 {
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
    color: #64748b;
  }

  .current-metrics {
    background: #0f172a;
    border-radius: 8px;
    padding: 1rem;
  }

  .metric-row {
    display: grid;
    grid-template-columns: 100px 1fr 60px;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .metric-label {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .metric-bar-container {
    height: 8px;
    background: #334155;
    border-radius: 4px;
    overflow: hidden;
  }

  .metric-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease-out;
  }

  .metric-bar.input {
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
  }

  .metric-bar.text {
    background: linear-gradient(90deg, #3b82f6, #60a5fa);
  }

  .metric-bar.similarity {
    background: linear-gradient(90deg, #22c55e, #4ade80);
  }

  .metric-value {
    font-size: 0.75rem;
    font-family: 'Monaco', 'Menlo', monospace;
    color: #e2e8f0;
    text-align: right;
  }

  .metric-summary {
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #334155;
  }

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .summary-label {
    font-size: 0.75rem;
    color: #64748b;
  }

  .summary-value {
    font-size: 1.25rem;
    font-weight: 600;
    font-family: 'Monaco', 'Menlo', monospace;
  }

  .summary-value.highlight {
    color: #22c55e;
  }

  .history {
    background: #0f172a;
    border-radius: 8px;
    padding: 1rem;
  }

  .history-chart {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 80px;
    padding: 0.5rem 0;
  }

  .history-bar-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
  }

  .history-bar {
    width: 100%;
    max-width: 20px;
    border-radius: 2px 2px 0 0;
    transition: height 0.3s;
    margin-top: auto;
  }

  .history-bar.clip {
    background: linear-gradient(180deg, #60a5fa, #3b82f6);
  }

  .history-bar.clap {
    background: linear-gradient(180deg, #a78bfa, #8b5cf6);
  }

  .history-label {
    font-size: 0.625rem;
    color: #64748b;
    margin-top: 0.25rem;
  }

  .history-legend {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-top: 0.5rem;
    font-size: 0.75rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .legend-item::before {
    content: '';
    width: 10px;
    height: 10px;
    border-radius: 2px;
  }

  .legend-item.clip::before {
    background: #3b82f6;
  }

  .legend-item.clap::before {
    background: #8b5cf6;
  }

  .legend-note {
    color: #64748b;
    margin-left: auto;
  }

  .empty-state {
    text-align: center;
    padding: 1.5rem;
    color: #64748b;
  }

  .empty-state p {
    margin: 0 0 0.5rem;
  }

  .hint {
    font-size: 0.875rem;
    color: #475569;
  }

  .info-section {
    background: #0f172a;
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.875rem;
  }

  .info-section ul {
    margin: 0;
    padding-left: 1.25rem;
    color: #94a3b8;
  }

  .info-section li {
    margin-bottom: 0.5rem;
  }

  .info-section strong {
    color: #e2e8f0;
  }

  .tip {
    margin: 0.75rem 0 0;
    padding: 0.75rem;
    background: #1e3a5f;
    border-radius: 6px;
    color: #93c5fd;
    font-size: 0.75rem;
  }
</style>
