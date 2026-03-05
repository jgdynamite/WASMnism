<script>
  import ClipDemo from './components/ClipDemo.svelte';
  import ClapDemo from './components/ClapDemo.svelte';
  import MetricsPanel from './components/MetricsPanel.svelte';
  import { checkHealth } from './lib/api.js';
  import { onMount } from 'svelte';

  let activeTab = 'clip';
  let metricsHistory = [];
  let healthStatus = null;

  const MAX_HISTORY = 20;

  function addMetrics(metrics, type) {
    metricsHistory = [
      { ...metrics, type, timestamp: Date.now() },
      ...metricsHistory
    ].slice(0, MAX_HISTORY);
  }

  onMount(async () => {
    try {
      healthStatus = await checkHealth();
    } catch (e) {
      console.error('Health check failed:', e);
    }
  });
</script>

<main>
  <header>
    <h1>CLIP & CLAP Edge Inference Demo</h1>
    <p class="subtitle">Contrastive Language Models for Zero-Shot Classification</p>
    {#if healthStatus}
      <div class="health-status">
        <span class="status-dot" class:healthy={healthStatus.status === 'healthy'}></span>
        API: {healthStatus.status}
      </div>
    {/if}
  </header>

  <div class="container">
    <div class="demo-section">
      <nav class="tabs">
        <button
          class:active={activeTab === 'clip'}
          on:click={() => activeTab = 'clip'}
        >
          CLIP (Images)
        </button>
        <button
          class:active={activeTab === 'clap'}
          on:click={() => activeTab = 'clap'}
        >
          CLAP (Audio)
        </button>
      </nav>

      <div class="tab-content">
        {#if activeTab === 'clip'}
          <ClipDemo on:result={(e) => addMetrics(e.detail.metrics, 'clip')} />
        {:else}
          <ClapDemo on:result={(e) => addMetrics(e.detail.metrics, 'clap')} />
        {/if}
      </div>
    </div>

    <aside class="metrics-section">
      <MetricsPanel {metricsHistory} />
    </aside>
  </div>
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
  }

  main {
    min-height: 100vh;
    padding: 1.5rem;
  }

  header {
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .subtitle {
    color: #94a3b8;
    margin: 0.5rem 0 0;
    font-size: 1rem;
  }

  .health-status {
    position: absolute;
    top: 0;
    right: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #94a3b8;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
  }

  .status-dot.healthy {
    background: #22c55e;
  }

  .container {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 1.5rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  @media (max-width: 1024px) {
    .container {
      grid-template-columns: 1fr;
    }
  }

  .demo-section {
    background: #1e293b;
    border-radius: 12px;
    overflow: hidden;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid #334155;
  }

  .tabs button {
    flex: 1;
    padding: 1rem;
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }

  .tabs button:hover {
    color: #e2e8f0;
    background: #334155;
  }

  .tabs button.active {
    color: #60a5fa;
  }

  .tabs button.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: #60a5fa;
  }

  .tab-content {
    padding: 1.5rem;
  }

  .metrics-section {
    background: #1e293b;
    border-radius: 12px;
    padding: 1.5rem;
    height: fit-content;
    position: sticky;
    top: 1.5rem;
  }
</style>
